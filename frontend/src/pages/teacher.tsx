import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { BarChart3, Braces, Camera, CheckCircle2, FileText, Upload, Users, X } from 'lucide-react'
import { ApiError, api, queryKeys, type AssignmentPayload } from '../api/client'
import type { AssignmentImport, AssignmentImportDraft, ImportDraftField, Language, TestCase } from '../api/types'
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
  const capabilities = useQuery({ queryKey: queryKeys.importCapabilities, queryFn: api.importCapabilities, enabled: !assignmentId, retry: false })
  const savedImports = useQuery({ queryKey: queryKeys.assignmentImports, queryFn: api.assignmentImports, enabled: !assignmentId, retry: false })

  useEffect(() => {
    if (!existing.data) return
    const item = existing.data
    setForm({ title: item.title, description: item.description, language: item.language, reference_source: item.reference_source ?? '', tests: item.tests ?? [], rubric: item.rubric ?? { policy_version: 'core-v1' }, requirements: item.requirements, input_notes: item.input_notes, output_notes: item.output_notes, examples: item.examples, constraints: item.constraints_text, concept_ids: item.concept_ids, deadline: item.deadline })
    setExampleText(item.examples.join('\n---\n'))
  }, [existing.data])

  const save = useMutation({ mutationFn: (value: AssignmentPayload) => assignmentId ? api.updateAssignment(assignmentId, value) : importRecord ? api.confirmImport(importRecord.public_id, value) : api.createAssignment(value), onSuccess: () => { void client.invalidateQueries({ queryKey: queryKeys.assignments }); navigate('/teacher/assignments') }, onError: value => { const mapped = assignmentError(value); setError(mapped.summary); setFieldErrors(mapped.fields) } })
  const knownConcepts = useMemo(() => new Set(graph.data?.nodes.map(node => node.id) ?? []), [graph.data])
  const visibleConcepts = (graph.data?.nodes ?? []).filter(node => `${node.label} ${node.id}`.toLowerCase().includes(conceptSearch.toLowerCase()))
  const toggleConcept = (conceptId: string) => setForm(current => ({ ...current, concept_ids: (current.concept_ids ?? []).includes(conceptId) ? (current.concept_ids ?? []).filter(id => id !== conceptId) : [...(current.concept_ids ?? []), conceptId] }))

  const applyDraft = (record: AssignmentImport) => {
    if (!('fields' in record.draft)) return
    const fields = record.draft.fields
    const present = (name:string) => fields[name]?.value != null
    const value = <T,>(name: string, fallback: T): T => (fields[name]?.value ?? fallback) as T
    setForm(current => ({ ...current,
      ...(present('title')?{title:value('title',current.title)}:{}), ...(present('description')?{description:value('description',current.description)}:{}),
      ...(present('requirements')?{requirements:value('requirements',current.requirements??'')}:{}), ...(present('language')?{language:value<Language>('language',current.language)}:{}),
      ...(present('input_notes')?{input_notes:value('input_notes',current.input_notes??'')}:{}), ...(present('output_notes')?{output_notes:value('output_notes',current.output_notes??'')}:{}),
      ...(present('constraints')?{constraints:value('constraints',current.constraints??'')}:{}), ...(present('concept_ids')?{concept_ids:value<string[]>('concept_ids',[]).filter(id=>knownConcepts.has(id))}:{}),
      ...(present('reference_source')?{reference_source:value('reference_source',current.reference_source)}:{}) }))
    if (present('examples')) { const examples=value<string[]>('examples',[]); setExampleText(examples.join('\n---\n')) }
  }

  const upload = useMutation({ mutationFn: async (file: File) => { const created = await api.createImport(file, `${file.name}:${file.size}:${file.lastModified}`); return api.extractImport(created.public_id) }, onSuccess: record => { setImportRecord(record); setImportError(''); applyDraft(record) }, onError: value => { const error = value as ApiError; setImportError(error.status === 503 ? 'The document was uploaded, but local OCR is not configured. PDFs with embedded text remain supported; you can continue manually.' : error.status === 413 ? 'The document exceeds an upload, page, or image limit.' : error.detail && typeof error.detail === 'object' && 'message' in error.detail ? String((error.detail as {message:string}).message) : 'The document could not be imported. Check its type and contents.') } })
  const patchImport = useMutation({ mutationFn: ({fields,rejected}:{fields:Record<string,unknown>;rejected?:string[]}) => api.updateImportDraft(importRecord!.public_id, fields, rejected), onSuccess: record => setImportRecord(record) })
  const removeImport = useMutation({ mutationFn: () => api.deleteImport(importRecord!.public_id), onSuccess: () => { setImportRecord(null); setMode('manual'); if (previewUrl) URL.revokeObjectURL(previewUrl); setPreviewUrl('') } })

  const importId = importRecord?.public_id
  useEffect(() => { let active = true; if (!importId) return; api.importPreview(importId).then(blob => { if (!active) return; const url=URL.createObjectURL(blob); setPreviewUrl(old => { if(old)URL.revokeObjectURL(old); return url }) }).catch(()=>undefined); return () => { active=false } }, [importId])
  useEffect(() => () => { if (previewUrl) URL.revokeObjectURL(previewUrl) }, [previewUrl])

  function submit(event: FormEvent) {
    event.preventDefault()
    setError('')
    if (graph.isPending || graph.error) { setError('Concepts could not be loaded. Retry before saving the assignment.'); return }
    const payload: AssignmentPayload = { ...form, title: form.title.trim(), tests: form.tests.map(test => ({ ...test, id: test.id.trim() })), concept_ids: [...(form.concept_ids ?? [])], examples: exampleText ? exampleText.split('\n---\n').map(value => value.trim()).filter(Boolean) : [], deadline: form.deadline ? new Date(form.deadline).toISOString() : null }
    const errors = validateAssignment(payload, knownConcepts)
    setFieldErrors(errors)
    if (Object.keys(errors).length) { setError('Please correct the highlighted assignment fields.'); return }
    save.mutate(payload)
  }

  if ((existing.isPending && assignmentId) || graph.isPending) return <Skeleton lines={10}/>
  return <><PageHeader title={assignmentId ? 'Edit assignment' : 'Create assignment'} description="Reference source, expected outputs, and rubric internals are hidden from students."/><Card className="form-card">
    {error && <div className="error-state" role="alert">{error}</div>}
    {!assignmentId && <div className="import-authoring">
      <div className="mode-tabs" role="tablist" aria-label="Assignment creation method">
        <Button type="button" variant={mode==='manual'?'primary':'secondary'} onClick={()=>setMode('manual')}>Manual</Button>
        <Button type="button" variant={mode==='upload'?'primary':'secondary'} onClick={()=>setMode('upload')}><Upload size={16}/> Upload Image/PDF</Button>
        <Button type="button" variant={mode==='camera'?'primary':'secondary'} onClick={()=>setMode('camera')}><Camera size={16}/> Take Photo</Button>
      </div>
      {mode!=='manual' && <div className="import-drop" onDragOver={event=>event.preventDefault()} onDrop={event=>{event.preventDefault();const file=event.dataTransfer.files[0];if(file)upload.mutate(file)}}>
        <FileText aria-hidden="true"/><p>{mode==='camera'?'Take or select a photo of the assignment.':'Drop a PNG, JPEG, WebP, or PDF here, or choose a file.'}</p>
        <label className="button button-secondary">{upload.isPending?'Extracting…':'Choose document'}<input className="sr-only" type="file" accept={mode==='camera'?'image/*':'.png,.jpg,.jpeg,.webp,.pdf'} capture={mode==='camera'?'environment':undefined} disabled={upload.isPending} onChange={event=>{const file=event.target.files?.[0];if(file)upload.mutate(file)}}/></label>
        <small>Private teacher document · 10 MiB maximum · never published automatically</small>
      </div>}
      {capabilities.data && !capabilities.data.ocr && mode==='camera' && <p className="field-warning">Local OCR is not configured. Photo extraction will report unavailable; manual entry remains available.</p>}
      {!importRecord && savedImports.data?.length ? <div><h2>Resume a private import</h2><div className="stack">{savedImports.data.slice(0,5).map(item=><Button type="button" variant="secondary" key={item.public_id} onClick={()=>{setMode(item.media_type==='application/pdf'?'upload':'camera');setImportRecord(item);applyDraft(item)}}>{item.original_name} · {item.state}</Button>)}</div></div>:null}
      {importError && <div className="error-state" role="alert">{importError}</div>}
      {importRecord && <ImportReview record={importRecord} previewUrl={previewUrl} onUse={name=>{if(!('fields' in importRecord.draft))return;const draft=importRecord.draft as AssignmentImportDraft;const field=draft.fields[name];if(field)applyDraft({...importRecord,draft:{...draft,fields:{[name]:field}}})}} onReject={name=>patchImport.mutate({fields:{},rejected:[name]})} onSave={()=>patchImport.mutate({fields:{title:form.title,description:form.description,requirements:form.requirements??'',language:form.language,input_notes:form.input_notes??'',output_notes:form.output_notes??'',constraints:form.constraints??'',concept_ids:form.concept_ids??[],reference_source:form.reference_source,examples:exampleText?exampleText.split('\n---\n').map(value=>value.trim()).filter(Boolean):[]}})} onRemove={()=>removeImport.mutate()}/>} 
    </div>}
    <form onSubmit={submit} className="form-grid" noValidate>
      <Field label="Title" error={fieldErrors.title}><input aria-invalid={Boolean(fieldErrors.title)} maxLength={200} value={form.title} onChange={e => setForm({ ...form, title: e.target.value })}/></Field>
      <Field label="Language" error={fieldErrors.language}><select aria-invalid={Boolean(fieldErrors.language)} value={form.language} onChange={e => setForm({ ...form, language: e.target.value as Language })}><option value="python">Python 3.11</option><option value="c">C11 (Clang)</option><option value="java">Java 17</option></select></Field>
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
      <div className="form-actions field-full"><Button type="button" variant="secondary" onClick={() => navigate('/teacher/assignments')}>Cancel</Button><Button disabled={save.isPending || Boolean(graph.error)}>{save.isPending ? 'Saving…' : importRecord ? 'Confirm and create assignment' : 'Save assignment'}</Button></div>
    </form>
  </Card></>
}

function ImportReview({record,previewUrl,onUse,onReject,onSave,onRemove}:{record:AssignmentImport;previewUrl:string;onUse:(name:string)=>void;onReject:(name:string)=>void;onSave:()=>void;onRemove:()=>void}) {
  const fields = 'fields' in record.draft ? record.draft.fields : {}
  return <Card className="import-review"><div className="section-title"><div><h2>Review extracted draft</h2><p className="muted">Nothing is published until you confirm the validated form.</p></div><Button type="button" variant="danger" onClick={onRemove}><X size={16}/> Remove import</Button></div>
    <div className="import-review-grid"><div>{previewUrl && record.media_type.startsWith('image/') ? <img className="import-preview" src={previewUrl} alt="Uploaded assignment preview"/> : previewUrl ? <a className="button button-secondary" href={previewUrl} download={record.original_name}>Download original PDF</a> : <Skeleton lines={4}/>}</div><div className="provenance-list">{Object.entries(fields).filter(([,field])=>field.value!=null).map(([name,field])=><div className="provenance-row" key={name}><div><strong>{name.replaceAll('_',' ')}</strong> <Badge tone={field.origin==='teacher-confirmed'?'green':'gold'}>{field.origin}</Badge>{field.confidence!=null&&<small> {Math.round(field.confidence*100)}% confidence</small>}<p className="muted">{summarizeImportField(field)}</p>{field.sources[0]&&<small>Source page {field.sources[0].page}</small>}{field.warnings.map(value=><p className="field-warning" key={value}>{value}</p>)}</div><div className="stack"><Button type="button" variant="secondary" onClick={()=>onUse(name)}>Use</Button>{field.origin==='provider-suggested'&&<Button type="button" variant="ghost" onClick={()=>onReject(name)}>Reject</Button>}</div></div>)}</div></div>
    {'unresolved_concepts' in record.draft && record.draft.unresolved_concepts.length>0&&<p className="field-warning">Unresolved concepts: {record.draft.unresolved_concepts.join(', ')}. Select canonical concepts below.</p>}
    <Button type="button" variant="secondary" onClick={onSave}>Save review draft</Button>
  </Card>
}

function summarizeImportField(field:ImportDraftField){const value=field.value;if(Array.isArray(value))return value.join(', ').slice(0,180);if(value&&typeof value==='object')return 'Structured suggestion — review before use.';return String(value??'').slice(0,180)}

function Field({ label, children, full = false, error }: { label: string; children: React.ReactNode; full?: boolean; error?: string }) { return <label className={`field ${full ? 'field-full' : ''}`}><span>{label}</span>{children}{error && <span className="field-error">{error}</span>}</label> }
export function TeacherSubmissions() { return <SubmissionsPage teacher/> }
export function TeacherSettings() { return <><PageHeader title="Settings" description="Security-sensitive administration remains server-controlled."/><Card className="unsupported"><h2>Account and platform controls</h2><p>Profile mutation, global user administration, worker controls, arbitrary compiler configuration, and availability management are not exposed by this client.</p></Card></> }
