import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { ApiError, api, type AssignmentPayload } from '../api/client'
import type { AssignmentImport, AssignmentImportDraft, ImportDraftField } from '../api/types'
import { AssignmentFormPage } from '../pages/teacher'
import { applyImportFields, importFailure } from './import-review'
import { ImportReview } from './ImportReview'

const field = (value: unknown, origin: ImportDraftField['origin'] = 'extracted'): ImportDraftField => ({ value, origin, confidence: .65, sources: [{ page: 2, text: 'Original source text' }], warnings: [], verification: 'unverified' })
const payload: AssignmentPayload = { title: '', description: '', language: 'python', reference_source: '', tests: [], rubric: { policy_version: 'core-v1', weights: { structure: .25, syntax: .15, tests: .5, originality: .1 } }, examples: [], concept_ids: [] }
function record(): AssignmentImport {
  return { public_id: 'review-1', state: 'review-ready', media_type: 'image/png', original_name: 'question.png', byte_size: 10, content_hash: 'a'.repeat(64), config_hash: 'b'.repeat(64), assignment_id: null, expires_at: '2099-01-01T00:00:00Z', created_at: '', updated_at: '', metadata: { pages: 2 }, extraction: { segments: [{ page: 1, method: 'ocr', text: 'First page', confidence: .6 }, { page: 2, method: 'ocr', text: 'Second page', confidence: .7 }] }, draft: { schema_version: 'assignment-import-draft-v1', config_hash: 'b'.repeat(64), unresolved_concepts: [], candidate_tests: [], fields: { title: field('Private title'), language: field('python'), concept_ids: field(['input']), reference_source: field('private code', 'provider-suggested') } } }
}
function renderForm(item = record()) {
  vi.spyOn(api, 'graph').mockResolvedValue({ version: 'v1', nodes: [{ id: 'input', label: 'Input', guidance: '' }], edges: [] })
  vi.spyOn(api, 'assignmentImports').mockResolvedValue([item])
  vi.spyOn(api, 'assignmentImport').mockResolvedValue(item)
  vi.spyOn(api, 'importPreview').mockRejectedValue(new ApiError(503, 'private error'))
  return render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } })}><MemoryRouter><AssignmentFormPage/></MemoryRouter></QueryClientProvider>)
}
afterEach(() => vi.restoreAllMocks())

describe('private import review', () => {
  it('does not automatically copy unverified code or tests into grading fields', () => {
    const draft = record().draft as AssignmentImportDraft
    draft.fields.tests = field([{ id: 'generated', input: '1', expected_output: 'invented', weight: 1, concept_ids: [] }], 'provider-suggested')
    expect(applyImportFields(payload, draft, new Set(['input']))).toMatchObject({ title: 'Private title', reference_source: '', tests: [] })
    draft.fields.reference_source.origin = 'teacher-confirmed'
    expect(applyImportFields(payload, draft, new Set(['input'])).reference_source).toBe('private code')
  })

  it.each([
    [503, 'ocr_timeout', 'timed out'], [503, 'ocr_busy', 'capacity'], [422, 'encrypted_pdf', 'Password-protected'],
    [413, 'image_dimensions_exceeded', 'dimensions'], [413, 'page_limit_exceeded', 'page limit'], [410, 'import_expired', 'expired'],
    [401, 'private', 'session'], [403, 'private', 'permission'], [429, 'private', 'Too many'], [409, 'idempotency_conflict', 'conflicts'],
    [500, 'internal_error', 'server could not complete'],
  ])('maps HTTP %s / %s safely', (status, code, expected) => {
    const message = importFailure(new ApiError(Number(status), 'secret provider output', undefined, undefined, { code, message: 'private diagnostic' }))
    expect(message).toContain(expected); expect(message).not.toContain('secret'); expect(message).not.toContain('diagnostic')
  })

  it('shows source-page navigation, uncertainty and blocked candidates accessibly', async () => {
    const item = record(); (item.draft as AssignmentImportDraft).candidate_tests = [{ id: 'candidate-1', input: '1', expected_output: '2', origin: 'provider-generated', verification: 'unverified', sources: [] }]
    const decision = vi.fn()
    render(<ImportReview record={item} previewUrl="" previewError="Preview unavailable" busy={false} saved={false} onUse={vi.fn()} onReject={vi.fn()} onCandidate={decision} onSave={vi.fn()} onRemove={vi.fn()} onRetry={vi.fn()}/> )
    expect(screen.getByText('First page')).toBeInTheDocument()
    await userEvent.selectOptions(screen.getByLabelText('Source page'), '2')
    expect(screen.getByText('Second page')).toBeInTheDocument()
    expect(screen.getAllByText(/Low confidence/).length).toBeGreaterThan(0)
    await userEvent.click(screen.getByRole('button', { name: 'I verified candidate-1; add to tests' }))
    expect(decision).toHaveBeenCalledWith('candidate-1', true)
  })

  it('rejects an applied field from both persisted draft and editable form', async () => {
    const item = record(); const next = record(); (next.draft as AssignmentImportDraft).fields.title = { ...field(null), origin: 'missing' }
    const patch = vi.spyOn(api, 'updateImportDraft').mockResolvedValue(next)
    renderForm(item); await userEvent.click(await screen.findByRole('button', { name: /question.png · review-ready/ }))
    expect(screen.getByLabelText('Title')).toHaveValue('Private title')
    expect(screen.getByLabelText('Reference solution')).toHaveValue('')
    await userEvent.click(screen.getByRole('button', { name: 'Reject Title' }))
    await waitFor(() => expect(screen.getByLabelText('Title')).toHaveValue(''))
    expect(patch).toHaveBeenCalledWith('review-1', {}, ['title'], undefined, undefined)
  })

  it('adds a candidate to hidden tests only after the backend records explicit verification', async () => {
    const item = record()
    const candidate = { id: 'sample-1', input: '7', expected_output: '14', origin: 'extracted' as const, verification: 'unverified' as const, sources: [] }
    ;(item.draft as AssignmentImportDraft).candidate_tests = [candidate]
    const confirmed = record()
    ;(confirmed.draft as AssignmentImportDraft).candidate_tests = [{ ...candidate, verification: 'teacher-confirmed' }]
    const patch = vi.spyOn(api, 'updateImportDraft').mockResolvedValue(confirmed)
    renderForm(item); await userEvent.click(await screen.findByRole('button', { name: /question.png · review-ready/ }))
    expect(screen.getAllByLabelText('Expected output')).toHaveLength(1)
    await userEvent.click(screen.getByRole('button', { name: 'I verified sample-1; add to tests' }))
    await waitFor(() => expect(screen.getAllByLabelText('Expected output')).toHaveLength(2))
    expect(screen.getAllByLabelText('Expected output')[1]).toHaveValue('14')
    expect(patch).toHaveBeenCalledWith('review-1', {}, undefined, ['sample-1'], [])
  })

  it('saves tests, rubric, deadline and code privately and warns before unsaved cancellation', async () => {
    const item = record(); const patch = vi.spyOn(api, 'updateImportDraft').mockResolvedValue(item)
    const confirm = vi.spyOn(api, 'confirmImport')
    renderForm(item); await userEvent.click(await screen.findByRole('button', { name: /question.png · review-ready/ }))
    await userEvent.type(screen.getByLabelText('Reference solution'), 'print(2)')
    await userEvent.type(screen.getByLabelText('Deadline'), '2026-12-01T12:00')
    await userEvent.click(screen.getByRole('button', { name: 'Save review draft' }))
    await screen.findByText('Private review saved.')
    expect(patch.mock.calls[0][1]).toMatchObject({ reference_source: 'print(2)', deadline: '2026-12-01T12:00', tests: [{ id: 'case-1' }], rubric: { policy_version: 'core-v1' } })
    expect(confirm).not.toHaveBeenCalled()
    await userEvent.type(screen.getByLabelText('Title'), ' changed')
    const discard = vi.spyOn(window, 'confirm').mockReturnValue(false)
    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    expect(discard).toHaveBeenCalled(); expect(screen.getByLabelText('Title')).toHaveValue('Private title changed')
    const event = new Event('beforeunload', { cancelable: true }); window.dispatchEvent(event); expect(event.defaultPrevented).toBe(true)
  })

  it('keeps an unavailable upload recoverable and uses an opaque idempotency key', async () => {
    const item = { ...record(), state: 'extraction-unavailable', draft: {} }
    renderForm(item)
    vi.mocked(api.assignmentImports).mockResolvedValue([])
    const upload = vi.spyOn(api, 'createImport').mockResolvedValue({ ...item, state: 'validated' })
    const extract = vi.spyOn(api, 'extractImport').mockRejectedValueOnce(new ApiError(503, 'unavailable', undefined, undefined, { code: 'ocr_unavailable' })).mockResolvedValue(record())
    await userEvent.click(await screen.findByRole('button', { name: /Upload Image/ }))
    fireEvent.change(screen.getByLabelText('Choose document'), { target: { files: [new File(['image'], 'Faculty Question (1).png', { type: 'image/png' })] } })
    await screen.findByText(/Local OCR is unavailable/)
    expect(upload.mock.calls[0][1]).toMatch(/^[a-f0-9-]{36}$/)
    expect(screen.getByRole('button', { name: 'Confirm and create assignment' })).toBeDisabled()
    await userEvent.click(screen.getByRole('button', { name: 'Retry extraction' }))
    await waitFor(() => expect(screen.getByLabelText('Title')).toHaveValue('Private title'))
    expect(extract).toHaveBeenCalledTimes(2)
    expect(within(screen.getByRole('group', { name: 'Assignment creation method' })).getByRole('button', { name: 'Manual' })).toBeEnabled()
  })
})
