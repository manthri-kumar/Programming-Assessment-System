import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { BarChart3, Braces, Camera, CheckCircle2, FileText, Upload, Users } from 'lucide-react'
import { ApiError, api, queryKeys, type AssignmentPayload } from '../api/client'
import type { AssignmentImport, AssignmentImportDraft, Language, TestCase } from '../api/types'
import { ImportReview } from '../features/ImportReview'
import { applyImportFields, clearImportField, importFailure } from '../features/import-review'
import { Badge, Button, Card, EmptyState, ErrorState, PageHeader, Skeleton } from '../components/ui'
import { SubmissionsPage } from './student'

function Metric({ icon, value, label }: { icon: React.ReactNode; value: string | number; label: string }) { return <Card className="stat-card"><span className="stat-icon">{icon}</span><div><div className="stat-value">{value}</div><div className="stat-label">{label}</div></div></Card> }

export function TeacherDashboard() {
  const analytics = useQuery({ queryKey: queryKeys.analytics, queryFn: api.analytics })
  const assignments = useQuery({ queryKey: queryKeys.assignments, queryFn: api.assignments })
  if (analytics.isPending || assignments.isPending) return <Skeleton lines={10}/>
  if (analytics.error || assignments.error) return <ErrorState error={analytics.error || assignments.error}/>
  const data = analytics.data!
  return <><PageHeader title="Teacher Dashboard" description="Owned assignments and persisted assessment results." action={<Link className="button button-primary" to="/teacher/assignments/new">Create assignment</Link>}/><div className="stats-grid"><Metric icon={<Braces/>} value={data.assignment_count} label="Assignments"/><Metric icon={<Users/>} value={data.submission_count} label="Submissions"/><Metric icon={<CheckCircle2/>} value={data.evaluated_count} label="Evaluated"/><Metric icon={<BarChart3/>} value={data.average_score == null ? '—' : `${data.average_score}%`} label="Valid score average"/></div><Card><div className="section-title"><h2>Owned assignments</h2><Link className="section-link" to="/teacher/assignments">Manage all →</Link></div>{assignments.data?.length ? assignments.data.slice(0, 6).map(item => <div className="problem-row" key={item.id}><span className="row-number">{item.id}</span><div><span className="row-title">{item.title}</span><div className="stack"><Badge tone="gold">{item.language}</Badge>{item.concept_ids.map(id => <Badge key={id}>{id}</Badge>)}</div></div><span className="muted">{item.deadline ? new Date(item.deadline).toLocaleDateString() : 'No deadline'}</span><Link className="button button-secondary" to={`/teacher/assignments/${item.id}/edit`}>Edit</Link></div>) : <EmptyState title="No assignments">Create your first assignment to begin.</EmptyState>}</Card></>
}

export function TeacherAssignments() {
  const { data = [], isPending, error } = useQuery({ queryKey: queryKeys.assignments, queryFn: api.assignments })
  if (isPending) return <Skeleton lines={8}/>
  if (error) return <ErrorState error={error}/>
  return <><PageHeader title="Assignments" description="Create and edit assignments you own. Hidden tests remain teacher-only." action={<Link className="button button-primary" to="/teacher/assignments/new">New assignment</Link>}/><div className="card-grid">{data.map(item => <Card key={item.id}><Badge tone="gold">{item.language}</Badge><h2>{item.title}</h2><p className="muted">{item.description || 'No description.'}</p><div className="stack"><Link className="button button-secondary" to={`/teacher/assignments/${item.id}/edit`}>Edit</Link><Link className="button button-primary" to={`/teacher/submissions?assignment=${item.id}`}>Submissions</Link></div></Card>)}</div></>
}

const emptyTest: TestCase = { id: 'case-1', input: '', expected_output: '', weight: 1, concept_ids: [] }
const defaultForm: AssignmentPayload = { title: '', description: '', language: 'python', reference_source: '', tests: [emptyTest], rubric: { policy_version: 'core-v1', weights: { structure: .25, syntax: .15, tests: .5, originality: .1 } }, requirements: '', input_notes: '', output_notes: '', examples: [], constraints: '', concept_ids: [], deadline: null }
type FieldErrors = Record<string, string>
const bytes = (value: string) => new TextEncoder().encode(value).length

export function validateAssignment(value: AssignmentPayload, knownConcepts: Set<string>): FieldErrors {
  const errors: FieldErrors = {}
  if (!value.title.trim()) errors.title = 'Title is required.'
  if (!['python', 'c', 'java'].includes(value.language)) errors.language = 'Choose Python, C, or Java.'
  if (!value.reference_source.trim()) errors.reference_source = 'Reference solution cannot be blank.'
  else if (bytes(value.reference_source) > 65536) errors.reference_source = 'Reference solution must not exceed 65,536 UTF-8 bytes.'
  const weights = value.rubric.weights ?? {}
  const weightValues = ['structure', 'syntax', 'tests', 'originality'].map(name => weights[name])
  if (weightValues.some(weight => !Number.isFinite(weight) || weight < 0) || Math.abs(weightValues.reduce((sum, weight) => sum + weight, 0) - 1) > .0001) errors.rubric = 'Rubric weights must be finite, nonnegative, and sum to 1.'
  if (value.tests.length > 50) errors.tests = 'No more than 50 tests are allowed.'
  const ids = new Set<string>()
  value.tests.forEach((test, index) => {
    const prefix = `tests.${index}`
    const id = test.id.trim()
    if (!id) errors[`${prefix}.id`] = 'Test ID is required.'
    else if (id.length > 128) errors[`${prefix}.id`] = 'Test ID must not exceed 128 characters.'
    else if (ids.has(id)) errors[`${prefix}.id`] = `Test ID “${id}” is duplicated.`
    ids.add(id)
    if (!Number.isFinite(test.weight) || test.weight <= 0) errors[`${prefix}.weight`] = 'Test weight must be a positive finite number.'
    if (bytes(test.input) > 65536) errors[`${prefix}.input`] = 'Test input must not exceed 65,536 UTF-8 bytes.'
    if (bytes(test.expected_output) > 65536) errors[`${prefix}.expected_output`] = 'Expected output must not exceed 65,536 UTF-8 bytes.'
    const unknown = test.concept_ids.filter(id => !knownConcepts.has(id))
    if (unknown.length) errors[`${prefix}.concept_ids`] = `Unknown concept IDs: ${unknown.join(', ')}.`
  })
  const unknown = (value.concept_ids ?? []).filter(id => !knownConcepts.has(id))
  if (unknown.length) errors.concept_ids = `Unknown concept IDs: ${unknown.join(', ')}.`
  if ((value.examples?.length ?? 0) > 10) errors.examples = 'No more than 10 examples are allowed.'
  if (value.deadline && Number.isNaN(new Date(value.deadline).getTime())) errors.deadline = 'Enter a valid deadline.'
  return errors
}

function backendField(location: unknown): string {
  if (!Array.isArray(location)) return 'form'
  const parts = location.filter(part => part !== 'body').map(String)
  if (parts[0] === 'reference_source') return 'reference_source'
  if (parts[0] === 'concept_ids') return 'concept_ids'
  if (parts[0] === 'rubric') return 'rubric'
  if (parts[0] === 'tests' || ['id', 'input', 'expected_output', 'weight'].includes(parts[0])) return parts[0] === 'tests' ? parts.join('.') : 'tests'
  return parts.join('.') || 'form'
}

export function assignmentError(error: unknown): { summary: string; fields: FieldErrors } {
  if (!(error instanceof ApiError)) return { summary: 'Assignment could not be saved. Please try again.', fields: {} }
  if (error.status === 0) return { summary: 'Unable to connect to the server. Please try again.', fields: {} }
  if (error.status === 401) return { summary: 'Your session has expired. Please sign in again.', fields: {} }
  if (error.status === 403) return { summary: 'You are not authorized to save this assignment.', fields: {} }
  const fields: FieldErrors = {}
  if (error.status === 422 && error.detail && typeof error.detail === 'object' && !Array.isArray(error.detail) && 'unknown_concepts' in error.detail) {
    const ids = (error.detail as { unknown_concepts?: unknown }).unknown_concepts
    const names = Array.isArray(ids) ? ids.filter((id): id is string => typeof id === 'string') : []
    fields.concept_ids = names.length ? `Unknown concept IDs: ${names.join(', ')}. Refresh the concept list and choose valid concepts.` : 'One or more concepts are no longer valid.'
  } else if (error.status === 422 && Array.isArray(error.detail)) {
    for (const item of error.detail) {
      if (!item || typeof item !== 'object') continue
      const detail = item as { loc?: unknown; msg?: unknown }
      const key = backendField(detail.loc)
      const raw = typeof detail.msg === 'string' ? detail.msg.replace(/^Value error,\s*/i, '') : 'Invalid value.'
      fields[key] = raw.length <= 240 ? raw : 'Invalid value.'
    }
  }
  return { summary: Object.keys(fields).length ? 'Please correct the highlighted assignment fields.' : 'Assignment could not be saved. Please check the entered details.', fields }
}

export function AssignmentFormPage() {
  const { id } = useParams()
  const assignmentId = id ? Number(id) : null
  const navigate = useNavigate()
  const client = useQueryClient()
  const existing = useQuery({ queryKey: queryKeys.assignment(assignmentId ?? 0), queryFn: () => api.assignment(assignmentId!), enabled: Boolean(assignmentId) })
  const graph = useQuery({ queryKey: queryKeys.graph, queryFn: api.graph })
  const [form, setForm] = useState<AssignmentPayload>(defaultForm)
  const [exampleText, setExampleText] = useState('')
  const [conceptSearch, setConceptSearch] = useState('')
  const [error, setError] = useState('')
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})
  const [mode, setMode] = useState<'manual'|'upload'|'camera'>('manual')
  const [importRecord, setImportRecord] = useState<AssignmentImport | null>(null)
  const [importError, setImportError] = useState('')
  const [previewUrl, setPreviewUrl] = useState('')
  const [previewError, setPreviewError] = useState('')
  const [savedSnapshot, setSavedSnapshot] = useState('')
  const [draftSaved, setDraftSaved] = useState(false)
  const [importStage, setImportStage] = useState('')
  const capabilities = useQuery({ queryKey: queryKeys.importCapabilities, queryFn: api.importCapabilities, enabled: !assignmentId, retry: false })
  const savedImports = useQuery({ queryKey: queryKeys.assignmentImports, queryFn: api.assignmentImports, enabled: !assignmentId, retry: false })

  useEffect(() => {
    if (!existing.data) return
    const item = existing.data
    setForm({ title: item.title, description: item.description, language: item.language, reference_source: item.reference_source ?? '', tests: item.tests ?? [], rubric: item.rubric ?? { policy_version: 'core-v1' }, requirements: item.requirements, input_notes: item.input_notes, output_notes: item.output_notes, examples: item.examples, constraints: item.constraints_text, concept_ids: item.concept_ids, deadline: item.deadline })
    setExampleText(item.examples.join('\n---\n'))
  }, [existing.data])

  const save = useMutation({ mutationFn: async (value: AssignmentPayload) => {
    if (assignmentId) return api.updateAssignment(assignmentId, value)
    if (!importRecord) return api.createAssignment(value)
    await api.updateImportDraft(importRecord.public_id, { ...value })
    return api.confirmImport(importRecord.public_id, value)
  }, onSuccess: () => { void client.invalidateQueries({ queryKey: queryKeys.assignments }); void client.invalidateQueries({ queryKey: queryKeys.analytics }); void client.invalidateQueries({ queryKey: queryKeys.assignmentImports }); navigate('/teacher/assignments') }, onError: value => { const mapped = assignmentError(value); setError(mapped.summary); setFieldErrors(mapped.fields) } })
  const knownConcepts = useMemo(() => new Set(graph.data?.nodes.map(node => node.id) ?? []), [graph.data])
  const visibleConcepts = (graph.data?.nodes ?? []).filter(node => `${node.label} ${node.id}`.toLowerCase().includes(conceptSearch.toLowerCase()))
  const toggleConcept = (conceptId: string) => setForm(current => ({ ...current, concept_ids: (current.concept_ids ?? []).includes(conceptId) ? (current.concept_ids ?? []).filter(id => id !== conceptId) : [...(current.concept_ids ?? []), conceptId] }))

  const canonicalDraft = { ...form, examples: exampleText ? exampleText.split('\n---\n').map(value => value.trim()).filter(Boolean) : [] }
  const snapshot = JSON.stringify(canonicalDraft)
  const dirty = Boolean(importRecord && savedSnapshot && snapshot !== savedSnapshot)
  const canDiscard = () => !dirty || window.confirm('Discard unsaved review changes? Save the private draft to keep them.')
  const loadDraft = (record: AssignmentImport) => {
    const next = 'fields' in record.draft ? applyImportFields({ ...defaultForm, language: '' as Language }, record.draft as AssignmentImportDraft, knownConcepts) : { ...defaultForm, language: '' as Language }
    setImportRecord(record); setForm(next); setExampleText(next.examples?.join('\n---\n') ?? '')
    setSavedSnapshot(JSON.stringify(next)); setDraftSaved(false)
  }
  const extracted = (record: AssignmentImport) => { loadDraft(record); setImportError(''); setImportStage(''); void client.invalidateQueries({ queryKey: queryKeys.assignmentImports }) }
  const failed = (value: unknown) => { setImportError(importFailure(value)); setImportStage('') }
  const upload = useMutation({ mutationFn: async (file: File) => {
    setImportError(''); setImportStage('Uploading and validating document…')
    const created = await api.createImport(file, crypto.randomUUID())
    loadDraft(created); void client.invalidateQueries({ queryKey: queryKeys.assignmentImports }); setImportStage('Extracting document…')
    try { return await api.extractImport(created.public_id) }
    catch (error) { const latest = await api.assignmentImport(created.public_id).catch(() => created); setImportRecord(latest); throw error }
  }, onSuccess: extracted, onError: failed })
  const retryExtraction = useMutation({ mutationFn: () => api.extractImport(importRecord!.public_id), onSuccess: extracted, onError: failed })
  const patchImport = useMutation({ mutationFn: ({ fields, rejected, confirmed, rejectedCandidates }: { fields: Record<string, unknown>; rejected?: string[]; confirmed?: string[]; rejectedCandidates?: string[] }) => api.updateImportDraft(importRecord!.public_id, fields, rejected, confirmed, rejectedCandidates), onSuccess: record => { setImportRecord(record); setImportError(''); void client.invalidateQueries({ queryKey: queryKeys.assignmentImports }) }, onError: failed })
  const removeImport = useMutation({ mutationFn: () => api.deleteImport(importRecord!.public_id), onSuccess: () => { setImportRecord(null); setMode('manual'); setImportError(''); setForm(defaultForm); setExampleText(''); void client.invalidateQueries({ queryKey: queryKeys.assignmentImports }) }, onError: failed })
  const resumeImport = useMutation({ mutationFn: (id: string) => api.assignmentImport(id), onSuccess: record => { setMode(record.media_type === 'application/pdf' ? 'upload' : 'camera'); loadDraft(record); setImportError('') }, onError: failed })
  const busy = upload.isPending || patchImport.isPending || retryExtraction.isPending || removeImport.isPending || save.isPending || resumeImport.isPending
  const importId = importRecord?.public_id
  useEffect(() => {
    let active = true; let objectUrl = ''
    setPreviewUrl(''); setPreviewError('')
    if (importId) api.importPreview(importId).then(blob => { if (active) { objectUrl = URL.createObjectURL(blob); setPreviewUrl(objectUrl) } }).catch(value => { if (active) setPreviewError(`Preview unavailable. ${importFailure(value)}`) })
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl) }
  }, [importId])
  useEffect(() => {
    if (!dirty || save.isPending) return
    const beforeUnload = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = '' }
    const navigation = (event: MouseEvent) => { const link = (event.target as Element).closest?.('a[href]'); if (link && !link.hasAttribute('download') && !window.confirm('Leave with unsaved review changes?')) { event.preventDefault(); event.stopPropagation() } }
    window.addEventListener('beforeunload', beforeUnload); document.addEventListener('click', navigation, true)
    return () => { window.removeEventListener('beforeunload', beforeUnload); document.removeEventListener('click', navigation, true) }
  }, [dirty, save.isPending])
  const acceptField = (name: string) => {
    if (!importRecord || !('fields' in importRecord.draft)) return
    const field = importRecord.draft.fields[name]
    patchImport.mutate({ fields: { [name]: field.value } }, { onSuccess: record => {
      if (!('fields' in record.draft)) return
      const next = applyImportFields(canonicalDraft, { ...record.draft as AssignmentImportDraft, fields: { [name]: record.draft.fields[name] } }, knownConcepts)
      setForm(next); if (name === 'examples') setExampleText(next.examples?.join('\n---\n') ?? '')
    } })
  }
  const rejectField = (name: string) => patchImport.mutate({ fields: {}, rejected: [name] }, { onSuccess: () => { setForm(current => clearImportField(current, name)); if (name === 'examples') setExampleText(''); setDraftSaved(false) } })
  const candidateDecision = (id: string, accept: boolean) => patchImport.mutate({ fields: {}, confirmed: accept ? [id] : [], rejectedCandidates: accept ? [] : [id] }, { onSuccess: record => {
    if (!accept || !('candidate_tests' in record.draft)) return
    const candidate = record.draft.candidate_tests.find(value => value.id === id)
    if (candidate && ['teacher-confirmed', 'worker-verified'].includes(candidate.verification)) setForm(current => ({ ...current, tests: [...current.tests.filter(value => value.id !== candidate.id), { id: candidate.id, input: candidate.input, expected_output: candidate.expected_output, weight: 1, concept_ids: [] }] }))
  } })

  function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    if (graph.isPending || graph.error) { setError('Concepts could not be loaded. Retry before saving the assignment.'); return }
    if (importRecord && importRecord.state !== 'review-ready') { setError('Extract the document successfully or return to manual creation before publishing.'); return }
    const payload: AssignmentPayload = { ...canonicalDraft, title: form.title.trim(), tests: form.tests.map(test => ({ ...test, id: test.id.trim() })), concept_ids: [...(form.concept_ids ?? [])] }
    const errors = validateAssignment(payload, knownConcepts)
    setFieldErrors(errors)
    if (Object.keys(errors).length) { setError('Please correct the highlighted assignment fields.'); return }
    payload.deadline = form.deadline ? new Date(form.deadline).toISOString() : null
    save.mutate(payload)
  }

  if ((existing.isPending && assignmentId) || graph.isPending) return <Skeleton lines={10}/>
  return <><PageHeader title={assignmentId ? 'Edit assignment' : 'Create assignment'} description="Reference source, expected outputs, and rubric internals are hidden from students."/><Card className="form-card">
    {error && <div className="error-state" role="alert">{error}</div>}
    {!assignmentId && <div className="import-authoring">
      <div className="mode-tabs" role="group" aria-label="Assignment creation method">
        <Button type="button" aria-pressed={mode==='manual'} disabled={busy} variant={mode==='manual'?'primary':'secondary'} onClick={()=>{if(canDiscard()){setMode('manual');setImportRecord(null);setImportError('')}}}>Manual</Button>
        <Button type="button" aria-pressed={mode==='upload'} disabled={busy || capabilities.data?.enabled === false} variant={mode==='upload'?'primary':'secondary'} onClick={()=>setMode('upload')}><Upload size={16}/> Upload Image/PDF</Button>
        <Button type="button" aria-pressed={mode==='camera'} disabled={busy || capabilities.data?.enabled === false} variant={mode==='camera'?'primary':'secondary'} onClick={()=>setMode('camera')}><Camera size={16}/> Take Photo</Button>
      </div>
      {mode!=='manual' && <div className="import-drop" onDragOver={event=>event.preventDefault()} onDrop={event=>{event.preventDefault();const file=event.dataTransfer.files[0];if(file&&!busy&&canDiscard())upload.mutate(file)}}>
        <FileText aria-hidden="true"/><p>{mode==='camera'?'Take or select a photo of the assignment.':'Drop a PNG, JPEG, WebP, or PDF here, or choose a file.'}</p>
        <label className="button button-secondary">Choose document<input className="sr-only" type="file" accept={mode==='camera'?'image/*':'.png,.jpg,.jpeg,.webp,.pdf'} capture={mode==='camera'?'environment':undefined} disabled={busy} onChange={event=>{const file=event.target.files?.[0];if(file&&canDiscard())upload.mutate(file);event.target.value=''}}/></label>
        {importStage && <p role="status">{importStage}</p>}
        <small>Private teacher document · 10 MiB maximum · never published automatically</small>
      </div>}
      {capabilities.data && !capabilities.data.ocr && mode==='camera' && <p className="field-warning">Local OCR is not configured. Photo extraction will report unavailable; manual entry remains available.</p>}
      {!importRecord && savedImports.data?.length ? <div><h2>Resume a private import</h2><div className="stack">{savedImports.data.slice(0,5).map(item=><Button type="button" disabled={busy} variant="secondary" key={item.public_id} onClick={()=>resumeImport.mutate(item.public_id)}>{item.original_name} · {item.state}</Button>)}</div></div>:null}
      {importError && <div className="error-state" role="alert">{importError}</div>}
      {importRecord && <ImportReview record={importRecord} previewUrl={previewUrl} previewError={previewError} busy={busy} saved={draftSaved && !dirty} onUse={acceptField} onReject={rejectField} onCandidate={candidateDecision} onSave={()=>patchImport.mutate({fields:{...canonicalDraft}}, {onSuccess:()=>{setSavedSnapshot(snapshot);setDraftSaved(true)}})} onRemove={()=>{if(canDiscard())removeImport.mutate()}} onRetry={()=>retryExtraction.mutate()}/>}
    </div>}
    <form onSubmit={submit} className="form-grid" noValidate>
      <fieldset disabled={busy} className="assignment-fields" aria-label="Assignment fields">
      <Field label="Title" error={fieldErrors.title}><input aria-invalid={Boolean(fieldErrors.title)} maxLength={200} value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}/></Field>
      <Field label="Language" error={fieldErrors.language}><select aria-invalid={Boolean(fieldErrors.language)} value={form.language} onChange={e => setForm({ ...form, language: e.target.value as Language })}><option value="" disabled>Select a language</option><option value="python">Python 3.11</option><option value="c">C11 (Clang)</option><option value="java">Java 17</option></select></Field>
      <Field full label="Description"><textarea maxLength={4000} value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}/></Field>
      <Field full label="Requirements"><textarea maxLength={8000} value={form.requirements} onChange={e => setForm({ ...form, requirements: e.target.value })}/></Field>
      <Field label="Input notes"><textarea maxLength={4000} value={form.input_notes} onChange={e => setForm({ ...form, input_notes: e.target.value })}/></Field>
      <Field label="Output notes"><textarea maxLength={4000} value={form.output_notes} onChange={e => setForm({ ...form, output_notes: e.target.value })}/></Field>
      <Field full label="Constraints"><textarea maxLength={4000} value={form.constraints} onChange={e => setForm({ ...form, constraints: e.target.value })}/></Field>
      <div className="field field-full"><span>Concepts</span><input aria-label="Search concepts" placeholder="Search by concept name or ID" value={conceptSearch} onChange={e => setConceptSearch(e.target.value)}/>{graph.error && <span className="field-error">Concepts could not be loaded.</span>}<div className="concept-selector" role="group" aria-label="Assignment concepts">{visibleConcepts.map(node => <label className="concept-option" key={node.id}><input type="checkbox" checked={(form.concept_ids ?? []).includes(node.id)} onChange={() => toggleConcept(node.id)}/><span><strong>{node.label}</strong><small>{node.id}</small></span></label>)}</div>{fieldErrors.concept_ids && <span className="field-error">{fieldErrors.concept_ids}</span>}</div>
      <Field full label="Examples (separate with a line containing ---)" error={fieldErrors.examples}><textarea value={exampleText} onChange={e => setExampleText(e.target.value)}/></Field>
      <Field label="Deadline" error={fieldErrors.deadline}><input type="datetime-local" aria-invalid={Boolean(fieldErrors.deadline)} value={form.deadline ? form.deadline.slice(0, 16) : ''} onChange={e => setForm({ ...form, deadline: e.target.value || null })}/></Field>
      <Field full label="Reference solution" error={fieldErrors.reference_source}><textarea aria-invalid={Boolean(fieldErrors.reference_source)} className="code-input" value={form.reference_source} onChange={e => setForm({ ...form, reference_source: e.target.value })}/></Field>
      <div className="field-full"><h2>Rubric weights</h2>{fieldErrors.rubric && <p className="field-error">{fieldErrors.rubric}</p>}<div className="weight-grid">{['structure', 'syntax', 'tests', 'originality'].map(name => <Field key={name} label={name}><input type="number" min="0" max="1" step="0.01" value={form.rubric.weights?.[name] ?? 0} onChange={e => setForm({ ...form, rubric: { ...form.rubric, weights: { ...form.rubric.weights, [name]: Number(e.target.value) } } })}/></Field>)}</div></div>
      <div className="field-full"><div className="section-title"><h2>Hidden tests</h2><Button type="button" variant="secondary" onClick={() => setForm({ ...form, tests: [...form.tests, { ...emptyTest, id: `case-${form.tests.length + 1}` }] })}>Add test</Button></div>{fieldErrors.tests && <p className="field-error">{fieldErrors.tests}</p>}{form.tests.map((test, index) => <Card key={index} className="test-editor"><Field label="Test ID" error={fieldErrors[`tests.${index}.id`]}><input aria-invalid={Boolean(fieldErrors[`tests.${index}.id`])} value={test.id} onChange={e => setForm({ ...form, tests: form.tests.map((value, i) => i === index ? { ...value, id: e.target.value } : value) })}/></Field><Field label="Input" error={fieldErrors[`tests.${index}.input`]}><textarea value={test.input} onChange={e => setForm({ ...form, tests: form.tests.map((value, i) => i === index ? { ...value, input: e.target.value } : value) })}/></Field><Field label="Expected output" error={fieldErrors[`tests.${index}.expected_output`]}><textarea value={test.expected_output} onChange={e => setForm({ ...form, tests: form.tests.map((value, i) => i === index ? { ...value, expected_output: e.target.value } : value) })}/></Field><Field label="Weight" error={fieldErrors[`tests.${index}.weight`]}><input type="number" min="0.01" step="0.01" value={test.weight} onChange={e => setForm({ ...form, tests: form.tests.map((value, i) => i === index ? { ...value, weight: Number(e.target.value) } : value) })}/></Field><Button type="button" variant="danger" disabled={form.tests.length === 1} onClick={() => setForm({ ...form, tests: form.tests.filter((_, i) => i !== index) })}>Remove</Button></Card>)}</div>
      <div className="form-actions field-full"><Button type="button" variant="secondary" onClick={() => {if(canDiscard())navigate('/teacher/assignments')}}>Cancel</Button><Button disabled={busy || Boolean(graph.error) || Boolean(importRecord && importRecord.state!=='review-ready')}>{save.isPending ? 'Saving…' : importRecord ? 'Confirm and create assignment' : 'Save assignment'}</Button></div>
      </fieldset>
    </form>
  </Card></>
}

function Field({ label, children, full = false, error }: { label: string; children: React.ReactNode; full?: boolean; error?: string }) { return <label className={`field ${full ? 'field-full' : ''}`}><span>{label}</span>{children}{error && <span className="field-error">{error}</span>}</label> }
export function TeacherSubmissions() { return <SubmissionsPage teacher/> }
export function TeacherSettings() { return <><PageHeader title="Settings" description="Security-sensitive administration remains server-controlled."/><Card className="unsupported"><h2>Account and platform controls</h2><p>Profile mutation, global user administration, worker controls, arbitrary compiler configuration, and availability management are not exposed by this client.</p></Card></> }
