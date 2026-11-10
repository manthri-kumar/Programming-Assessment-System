import { expect, request as createRequest, test, type APIRequestContext, type Page } from '@playwright/test'

test.describe.configure({ mode: 'serial' })

const API = process.env.E2E_API_URL ?? 'http://127.0.0.1:8000'
const password = 'browser-test-password'
const teacherRegistrationCode = process.env.E2E_TEACHER_REGISTRATION_CODE ?? ''
let api: APIRequestContext
let teacherEmail: string
let studentEmail: string
let teacherToken: string
let studentToken: string
let assignmentId: number
let submissionId: number
const assignmentPdf = Buffer.from('JVBERi0xLjMKJeLjz9MKMSAwIG9iago8PAovUHJvZHVjZXIgKHB5cGRmKQo+PgplbmRvYmoKMiAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWyA0IDAgUiBdCj4+CmVuZG9iagozIDAgb2JqCjw8Ci9UeXBlIC9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKNCAwIG9iago8PAovVHlwZSAvUGFnZQovUmVzb3VyY2VzIDw8Ci9Gb250IDw8Ci9GMSA1IDAgUgo+Pgo+PgovTWVkaWFCb3ggWyAwLjAgMC4wIDMwMCAyMDAgXQovUGFyZW50IDIgMCBSCi9Db250ZW50cyA2IDAgUgo+PgplbmRvYmoKNSAwIG9iago8PAovVHlwZSAvRm9udAovU3VidHlwZSAvVHlwZTEKL0Jhc2VGb250IC9IZWx2ZXRpY2EKPj4KZW5kb2JqCjYgMCBvYmoKPDwKL0xlbmd0aCA5OAo+PgpzdHJlYW0KQlQgL0YxIDEyIFRmIDIwIDE2MCBUZCAoQXJyYXkgU3VtIERlc2NyaXB0aW9uOiBBZGQgdmFsdWVzIExhbmd1YWdlOiBQeXRob24gQ29uY2VwdHM6IEFycmF5cykgVGogRVQKZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgNwowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAwMTUgMDAwMDAgbiAKMDAwMDAwMDA1NCAwMDAwMCBuIAowMDAwMDAwMTEzIDAwMDAwIG4gCjAwMDAwMDAxNjIgMDAwMDAgbiAKMDAwMDAwMDI5NCAwMDAwMCBuIAowMDAwMDAwMzY0IDAwMDAwIG4gCnRyYWlsZXIKPDwKL1NpemUgNwovUm9vdCAzIDAgUgovSW5mbyAxIDAgUgo+PgpzdGFydHhyZWYKNTEyCiUlRU9GCg==','base64')
const assignmentPhoto = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9Z4TQAAAAASUVORK5CYII=', 'base64')

async function register(email: string, role: 'student' | 'teacher') {
  const response = await api.post('/auth/register', { data: { email, password, role, ...(role === 'teacher' ? { teacher_registration_code: teacherRegistrationCode } : {}) } })
  expect(response.status()).toBe(201)
}

async function token(email: string) {
  const response = await api.post('/auth/login', { data: { email, password } })
  expect(response.ok()).toBeTruthy()
  return (await response.json()).access_token as string
}

async function login(page: Page, email: string) {
  await page.goto('/login')
  await page.getByLabel('Email').fill(email)
  await page.getByLabel('Password', { exact: true }).fill(password)
  await page.getByRole('button', { name: 'Sign in', exact: true }).last().click()
  await expect(page).toHaveURL(/\/(student|teacher)$/)
}

async function expectNoPageOverflow(page: Page) {
  const overflow = await page.evaluate(() => ({
    clientWidth: document.documentElement.clientWidth,
    scrollWidth: document.documentElement.scrollWidth,
    elements: [...document.querySelectorAll<HTMLElement>('body *')].filter(element => {
      const rect = element.getBoundingClientRect()
      return rect.right > document.documentElement.clientWidth + 1 || rect.left < -1
    }).slice(0, 8).map(element => ({ tag: element.tagName, className: element.className, text: element.textContent?.trim().slice(0, 80), rect: element.getBoundingClientRect().toJSON() })),
  }))
  expect(overflow.scrollWidth, JSON.stringify(overflow, null, 2)).toBeLessThanOrEqual(overflow.clientWidth + 1)
}

async function expectNamedControls(page: Page) {
  const unnamed = await page.locator('button, a[href], input, select, textarea').evaluateAll(elements => elements.filter(element => {
    const html = element as HTMLElement
    if (html.getAttribute('aria-hidden') === 'true' || html.hasAttribute('disabled')) return false
    const labelledBy = html.getAttribute('aria-labelledby')
    const ariaLabel = html.getAttribute('aria-label')
    const text = html.textContent?.trim()
    const id = html.id
    const label = id ? document.querySelector(`label[for="${CSS.escape(id)}"]`)?.textContent?.trim() : html.closest('label')?.textContent?.trim()
    return !labelledBy && !ariaLabel && !text && !label && !html.getAttribute('title')
  }).map(element => element.outerHTML.slice(0, 160)))
  expect(unnamed).toEqual([])
}

test.beforeAll(async ({ request }, testInfo) => {
  void request
  if (!teacherRegistrationCode) throw new Error('E2E_TEACHER_REGISTRATION_CODE is required')
  api = await createRequest.newContext({ baseURL: API })
  const suffix = `${testInfo.project.name}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`
  teacherEmail = `teacher-${suffix}@example.test`
  studentEmail = `student-${suffix}@example.test`
  await register(teacherEmail, 'teacher')
  await register(studentEmail, 'student')
  teacherToken = await token(teacherEmail)
  studentToken = await token(studentEmail)
  const assignment = await api.post('/assignments', {
    headers: { Authorization: `Bearer ${teacherToken}` },
    data: {
      title: `Array Sum ${testInfo.project.name}`,
      description: 'Read integers and print their sum.',
      language: 'python',
      reference_source: 'print(sum(map(int, input().split())))',
      tests: [{ id: 'sum-1', input: '1 2 3\n', expected_output: '6\n', weight: 1, concept_ids: ['input'] }],
      rubric: { policy_version: 'core-v1', weights: { structure: 0.25, syntax: 0.15, tests: 0.5, originality: 0.1 } },
      requirements: 'Use the provided input.', input_notes: 'Space-separated integers.', output_notes: 'One integer.',
      examples: ['Input: 1 2 3\nOutput: 6'], constraints: 'At least one integer.', concept_ids: ['input'],
      deadline: new Date(Date.now() + 86_400_000).toISOString(),
    },
  })
  expect(assignment.status()).toBe(201)
  assignmentId = (await assignment.json()).id
  const submission = await api.post('/submissions', {
    headers: { Authorization: `Bearer ${studentToken}` },
    data: { assignment_id: assignmentId, language: 'python', source: 'print(sum(map(int, input().split())))' },
  })
  expect(submission.status()).toBe(201)
  submissionId = (await submission.json()).id
})

test.afterAll(async () => { await api.dispose() })

test('student and teacher registration, role routing, session restoration, and logout', async ({ page }, testInfo) => {
  const suffix = `${testInfo.project.name}-${Date.now()}-registration`
  const registerThroughForm = async (email: string, role: 'student' | 'teacher') => {
    await page.goto('/register')
    await page.getByLabel('Email').fill(email)
    await page.getByLabel('Password', { exact: true }).fill(password)
    await page.getByLabel('Role').selectOption(role)
    if (role === 'teacher') await page.getByLabel('Teacher invitation code').fill(teacherRegistrationCode)
    await page.getByRole('button', { name: 'Create account' }).click()
    await expect(page.getByRole('status')).toContainText('Account created')
    await page.getByRole('button', { name: 'Sign in', exact: true }).last().click()
    await expect(page).toHaveURL(new RegExp(`/${role}$`))
    await page.reload()
    await expect(page).toHaveURL(new RegExp(`/${role}$`))
  }

  await registerThroughForm(`registered-student-${suffix}@example.test`, 'student')
  await page.goto('/teacher/assignments')
  await expect(page).toHaveURL(/\/student$/)
  await page.getByRole('button', { name: 'Open profile menu' }).click()
  await page.getByRole('menuitem', { name: 'Logout' }).click()
  await expect(page).toHaveURL(/\/login$/)

  await registerThroughForm(`registered-teacher-${suffix}@example.test`, 'teacher')
  await page.goto('/student/progress')
  await expect(page).toHaveURL(/\/teacher$/)
  await page.getByRole('button', { name: 'Open profile menu' }).click()
  await page.getByRole('menuitem', { name: 'Logout' }).click()
  await expect(page).toHaveURL(/\/login$/)
})

test('teacher form creates and edits an assignment through the complete fail-closed assessment workflow', async ({ page }, testInfo) => {
  test.setTimeout(60_000)
  const title = `UI Contract ${testInfo.project.name} ${Date.now()}`
  const updatedTitle = `${title} Updated`
  await login(page, teacherEmail)
  await page.goto('/teacher/assignments/new')
  await expect(page.getByRole('heading', { name: 'Create assignment' })).toBeVisible()
  await page.getByLabel('Title').fill(title)
  await page.getByLabel('Description').fill('Echo one line of input.')
  await page.getByLabel('Reference solution').fill('print(input())')
  await page.getByLabel('Input', { exact: true }).fill('hello\n')
  await page.getByLabel('Expected output').fill('hello\n')
  await page.getByLabel('Assignment concepts').getByRole('checkbox').first().check()
  const createResponse = page.waitForResponse(response => response.url().endsWith('/assignments') && response.request().method() === 'POST')
  await page.getByRole('button', { name: 'Save assignment' }).click()
  const created = await createResponse
  expect(created.status()).toBe(201)
  const createdBody = await created.json()
  const createdId = createdBody.id as number
  await expect(page).toHaveURL(/\/teacher\/assignments$/)
  await expect(page.getByText(title)).toBeVisible()

  await page.goto(`/teacher/assignments/${createdId}/edit`)
  await expect(page.getByRole('heading', { name: 'Edit assignment' })).toBeVisible()
  await page.getByLabel('Title').fill(updatedTitle)
  const updateResponse = page.waitForResponse(response => response.url().endsWith(`/assignments/${createdId}`) && response.request().method() === 'PATCH')
  await page.getByRole('button', { name: 'Save assignment' }).click()
  expect((await updateResponse).status()).toBe(200)
  await expect(page.getByText(updatedTitle)).toBeVisible()

  await page.getByRole('button', { name: 'Open profile menu' }).click()
  await page.getByRole('menuitem', { name: 'Logout' }).click()
  await login(page, studentEmail)
  await page.goto('/student/assignments')
  await expect(page.getByText(updatedTitle)).toBeVisible()
  await page.getByText(updatedTitle).locator('..').getByRole('link', { name: 'View assignment' }).click()
  await expect(page.getByRole('heading', { name: updatedTitle })).toBeVisible()
  await expect(page.locator('main')).not.toContainText('print(input())')
  await expect(page.locator('main')).not.toContainText('hello')
  await page.getByRole('link', { name: 'Open workspace' }).click()
  const fallbackEditor = page.locator('textarea.editor-fallback')
  if (await fallbackEditor.isVisible()) {
    await fallbackEditor.fill('print(input())')
  } else {
    await page.locator('.monaco-editor').click({ position: { x: 220, y: 100 } })
    await page.keyboard.press('Control+A')
    await page.keyboard.type('print(input())')
  }
  await page.getByRole('button', { name: 'Submit & evaluate' }).click()
  await page.getByRole('button', { name: 'Confirm submission' }).click()
  await expect(page).toHaveURL(/\/student\/submissions\/\d+$/)
  const createdSubmissionId = Number(page.url().split('/').pop())
  await expect(page.getByText('ImplementationEvaluationAgent')).toBeVisible()
  await expect(page.getByText('FeedbackAgent')).toBeVisible()
  await expect(page.getByText('A missing score remains unavailable; weights are not redistributed.')).toBeVisible()
  await expect(page.getByText('assessment-report-v3', { exact: true })).toBeVisible()
  await expect(page.getByText('Secure functional execution is unavailable; static feedback is provisional.')).toBeVisible()
  await expect(page.getByText('Teacher evidence review')).toHaveCount(0)

  await page.getByRole('button', { name: 'Open profile menu' }).click()
  await page.getByRole('menuitem', { name: 'Logout' }).click()
  await login(page, teacherEmail)
  await page.goto(`/teacher/submissions/${createdSubmissionId}`)
  await expect(page.getByText('ImplementationEvaluationAgent')).toBeVisible()
  await expect(page.getByText('FeedbackAgent')).toBeVisible()
  await expect(page.getByText('Teacher evidence review')).toBeVisible()
})

test('teacher imports embedded PDF text, reviews it, and explicitly creates a student-visible assignment', async ({ page }, testInfo) => {
  test.setTimeout(45_000)
  const title=`Imported PDF ${testInfo.project.name} ${Date.now()}`
  await login(page,teacherEmail);await page.goto('/teacher/assignments/new');await page.getByRole('button',{name:/Upload Image\/PDF/}).click()
  await page.getByLabel(/Choose document/).setInputFiles({name:'question.pdf',mimeType:'application/pdf',buffer:assignmentPdf})
  await expect(page.getByRole('heading',{name:'Review extracted draft'})).toBeVisible()
  await page.getByLabel('Title').fill(title);await page.getByLabel('Reference solution').fill('print(sum(map(int,input().split())))');await page.getByLabel('Input',{exact:true}).fill('1 2\n');await page.getByLabel('Expected output').fill('3\n')
  const boxes=page.getByLabel('Assignment concepts').getByRole('checkbox');if(!(await boxes.first().isChecked()))await boxes.first().check()
  const confirmed=page.waitForResponse(response=>response.url().includes('/assignment-imports/')&&response.url().endsWith('/confirm'))
  await page.getByRole('button',{name:'Confirm and create assignment'}).click();expect((await confirmed).status()).toBe(201);await expect(page).toHaveURL(/\/teacher\/assignments$/);await expect(page.getByText(title)).toBeVisible()
  await page.getByRole('button',{name:'Open profile menu'}).click();await page.getByRole('menuitem',{name:'Logout'}).click();await login(page,studentEmail);await page.goto('/student/assignments');await expect(page.getByText(title)).toBeVisible()
})

test('teacher reviews a photographed question with the deterministic browser adapter', async ({ page }) => {
  const now = '2026-11-09T00:00:00Z'
  const draft = {
    public_id: 'photo-browser-adapter', state: 'review-ready', media_type: 'image/png', original_name: 'question-photo.png', byte_size: assignmentPhoto.length,
    content_hash: 'a'.repeat(64), metadata: { pages: 1, width: 1, height: 1, orientation: 1 },
    extraction: { schema_version: 'assignment-import-extraction-v1', provider: 'deterministic-browser-adapter', segments: [{ page: 1, method: 'ocr', text: 'Photo Sum', confidence: .82 }] },
    draft: { schema_version: 'assignment-import-draft-v1', config_hash: 'b'.repeat(64), unresolved_concepts: [], candidate_tests: [], fields: {
      title: { value: 'Photo Sum', origin: 'extracted', confidence: .82, sources: [{ page: 1, text: 'Photo Sum' }], warnings: [], verification: 'unverified' },
      description: { value: 'Add the photographed values.', origin: 'extracted', confidence: .76, sources: [{ page: 1, text: 'Add values' }], warnings: ['Review low-confidence text.'], verification: 'unverified' },
      language: { value: 'python', origin: 'provider-suggested', confidence: .7, sources: [{ page: 1, text: 'Python' }], warnings: [], verification: 'unverified' },
      concept_ids: { value: ['arrays'], origin: 'provider-suggested', confidence: .7, sources: [{ page: 1, text: 'Arrays' }], warnings: [], verification: 'unverified' },
    } }, config_hash: 'b'.repeat(64), assignment_id: null, expires_at: '2026-12-01T00:00:00Z', created_at: now, updated_at: now,
  }
  let patched = false
  await page.route('**/assignment-imports/photo-browser-adapter/preview', route => route.fulfill({ status: 200, contentType: 'image/png', body: assignmentPhoto }))
  await page.route('**/assignment-imports/photo-browser-adapter/extract', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(draft) }))
  await page.route('**/assignment-imports/photo-browser-adapter/draft', async route => { patched = true; await route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(draft) }) })
  await page.route('**/assignment-imports/capabilities', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ enabled: true, embedded_pdf_text: true, ocr: true, ocr_provider: 'deterministic-browser-adapter' }) }))
  await page.route('**/assignment-imports', async route => {
    if (route.request().method() === 'POST') await route.fulfill({ status: 201, contentType: 'application/json', body: JSON.stringify({ ...draft, state: 'validated', extraction: { segments: [] }, draft: {} }) })
    else await route.fulfill({ status: 200, contentType: 'application/json', body: '[]' })
  })
  await login(page, teacherEmail)
  await page.goto('/teacher/assignments/new')
  await page.getByRole('button', { name: /Take Photo/ }).click()
  await page.getByLabel(/Choose document/).setInputFiles({ name: 'question-photo.png', mimeType: 'image/png', buffer: assignmentPhoto })
  await expect(page.getByRole('heading', { name: 'Review extracted draft' })).toBeVisible()
  await expect(page.getByAltText('Uploaded assignment preview')).toBeVisible()
  await expect(page.getByLabel('Title')).toHaveValue('Photo Sum')
  await expect(page.getByText('82% confidence')).toBeVisible()
  await expect(page.getByText('Review low-confidence text.')).toBeVisible()
  await page.getByRole('button', { name: 'Save review draft' }).click()
  await expect.poll(() => patched).toBe(true)
  await expect(page.getByRole('button', { name: 'Confirm and create assignment' })).toBeVisible()
  // This is UI evidence for the deterministic adapter, not proof of a provisioned OCR runtime.
})

test('student routes, responsive shell, accessibility, and fail-closed evaluation', async ({ page }, testInfo) => {
  const consoleErrors: string[] = []
  const pageErrors: string[] = []
  page.on('console', message => { if (message.type() === 'error') consoleErrors.push(message.text()) })
  page.on('pageerror', error => pageErrors.push(error.message))
  await login(page, studentEmail)

  const routes: Array<[string, RegExp]> = [
    ['/student', /Good (morning|afternoon|evening)/],
    ['/student/assignments', /^Assignments$/],
    [`/student/assignments/${assignmentId}`, /Array Sum/],
    [`/student/assignments/${assignmentId}/workspace`, /Array Sum/],
    ['/student/submissions', /My Submissions/],
    [`/student/submissions/${submissionId}`, /Submission #/],
    ['/student/progress', /^Progress$/],
    ['/student/bookmarks', /^Bookmarks$/],
    ['/student/recommended', /^Recommended$/],
    ['/student/learning', /Learning Path/],
    ['/student/settings', /^Settings$/],
  ]
  for (const [route, heading] of routes) {
    await page.goto(route)
    await expect(page.getByRole('heading', { name: heading }).first()).toBeVisible()
    await expectNoPageOverflow(page)
    await expectNamedControls(page)
  }

  await page.goto('/student')
  await page.screenshot({ path: testInfo.outputPath(`student-dashboard-${testInfo.project.name}.png`), fullPage: true })
  const viewport = page.viewportSize()!
  if (viewport.width <= 760) {
    await expect(page.locator('.sidebar')).not.toBeInViewport()
    await page.getByRole('button', { name: 'Open navigation' }).click()
    await expect(page.locator('.sidebar')).toBeInViewport()
  } else {
    await expect(page.locator('.sidebar')).toBeInViewport()
  }
  await page.keyboard.press('Control+k')
  await expect(page.locator('#global-search')).toBeFocused()

  await page.goto(`/student/submissions/${submissionId}`)
  await page.getByRole('button', { name: 'Evaluate' }).click()
  await page.waitForTimeout(1_000)
  expect(await page.locator('main').innerText(), JSON.stringify(consoleErrors, null, 2)).toContain('A missing score remains unavailable; weights are not redistributed.')
  await expect(page.getByText('ImplementationEvaluationAgent')).toBeVisible()
  await expect(page.getByText('FeedbackAgent')).toBeVisible()
  expect(pageErrors).toEqual([])
  expect(consoleErrors.filter(message => !message.startsWith('Failed to load resource:'))).toEqual([])
})

test('teacher routes and authorization-safe API failures', async ({ page }) => {
  await login(page, teacherEmail)
  const routes: Array<[string, RegExp]> = [
    ['/teacher', /Teacher Dashboard/],
    ['/teacher/assignments', /^Assignments$/],
    ['/teacher/assignments/new', /Create assignment/],
    [`/teacher/assignments/${assignmentId}/edit`, /Edit assignment/],
    ['/teacher/submissions', /Student Submissions/],
    [`/teacher/submissions/${submissionId}`, /Submission #/],
    ['/teacher/settings', /^Settings$/],
  ]
  for (const [route, heading] of routes) {
    await page.goto(route)
    await expect(page.getByRole('heading', { name: heading }).first()).toBeVisible()
    await expectNoPageOverflow(page)
    await expectNamedControls(page)
  }

  const unauthorized = await api.patch(`/assignments/${assignmentId}`, { headers: { Authorization: `Bearer ${studentToken}` }, data: { title: 'Forbidden' } })
  expect(unauthorized.status()).toBe(403)
  const invalid = await api.post('/assignments', { headers: { Authorization: `Bearer ${teacherToken}` }, data: { title: '' } })
  expect(invalid.status()).toBe(422)
  const unauthenticated = await api.get('/auth/me')
  expect(unauthenticated.status()).toBe(401)
  const unavailable = await api.get('/ready')
  expect(unavailable.status()).toBe(503)
})

test('loading, empty, not-found, API error, and expired-session states', async ({ page }) => {
  await login(page, studentEmail)
  await page.goto('/student/bookmarks')
  await expect(page.getByText('No bookmarks')).toBeVisible()

  await page.goto('/student/submissions/99999999')
  await expect(page.getByRole('alert')).toBeVisible()

  await page.route('**/api/assignments', async route => {
    await new Promise(resolve => setTimeout(resolve, 350))
    await route.continue()
  }, { times: 1 })
  await page.goto('/student/assignments')
  await expect(page.locator('.skeleton')).toBeVisible()
  await expect(page.getByRole('heading', { name: 'Assignments' })).toBeVisible()

  await page.route('**/api/student/progress', route => route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ error: { code: 'test_failure', message: 'Controlled API failure' } }) }))
  await page.goto('/student/progress')
  await expect(page.getByRole('alert')).toContainText('Controlled API failure')

  await page.unroute('**/api/student/progress')
  await page.route('**/api/student/progress', route => route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ error: { code: 'expired', message: 'Session expired' } }) }), { times: 1 })
  await page.goto('/student/progress')
  await expect(page).toHaveURL(/\/login$/)
  await expect(page.getByText(/session expired/i)).toBeVisible()
})
