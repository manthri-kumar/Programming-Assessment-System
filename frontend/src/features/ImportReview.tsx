import { useState } from 'react'
import { X } from 'lucide-react'
import type { AssignmentImport, ImportDraftField } from '../api/types'
import { Badge, Button, Card, Skeleton } from '../components/ui'
import { importFieldLabels } from './import-review'

interface Props {
  record: AssignmentImport
  previewUrl: string
  previewError: string
  busy: boolean
  saved: boolean
  onUse: (name: string) => void
  onReject: (name: string) => void
  onCandidate: (id: string, accept: boolean) => void
  onSave: () => void
  onRemove: () => void
  onRetry: () => void
}

export function ImportReview({ record, previewUrl, previewError, busy, saved, onUse, onReject, onCandidate, onSave, onRemove, onRetry }: Props) {
  const [sourcePage, setSourcePage] = useState<number | null>(null)
  const fields = 'fields' in record.draft ? record.draft.fields : {}
  const candidates = 'candidate_tests' in record.draft ? record.draft.candidate_tests : []
  const segments = record.extraction.segments ?? []
  const pages = [...new Set(segments.map(segment => segment.page))].sort((a, b) => a - b)
  const selectedPage = sourcePage ?? pages[0]
  return <Card className="import-review" aria-busy={busy}>
    <div className="section-title"><div><h2>Review extracted draft</h2><p className="muted">Nothing is published until you confirm the validated form.</p><p role="status">Import status: {record.state.replaceAll('-', ' ')}</p></div><Button type="button" variant="danger" disabled={busy} onClick={onRemove}><X size={16}/> Remove import</Button></div>
    <div className="import-review-grid">
      <div className="import-source">
        {previewError ? <p className="field-warning" role="status">{previewError}</p> : previewUrl && record.media_type.startsWith('image/') ? <img className="import-preview" src={previewUrl} alt="Uploaded assignment preview"/> : previewUrl ? <a className="button button-secondary" href={previewUrl} download={record.original_name}>Download original PDF</a> : <Skeleton lines={4}/>}
        {pages.length > 0 && <section aria-label="Extracted source text"><h3>Source text</h3><label className="field">Source page<select value={selectedPage} onChange={event => setSourcePage(Number(event.target.value))}>{pages.map(page => <option key={page} value={page}>Page {page}</option>)}</select></label>{segments.filter(segment => segment.page === selectedPage).map((segment, index) => <pre className="source-text" key={`${segment.page}-${index}`}>{segment.text}</pre>)}</section>}
        {!pages.length && <p className="muted">Source text will appear after successful extraction.</p>}
      </div>
      <div className="provenance-list">{Object.entries(fields).map(([name, field]) => <div className="provenance-row" key={name}>
        <div><strong>{importFieldLabels[name] ?? name}</strong> <Badge tone={field.origin === 'teacher-confirmed' ? 'green' : 'gold'}>{field.origin}</Badge>
          {field.value != null && <><small> {field.confidence == null ? 'Confidence unknown' : `${Math.round(field.confidence * 100)}% confidence`}</small><Badge>{field.verification ?? 'unverified'}</Badge><p className="muted">{summarize(field)}</p></>}
          {field.value == null && <p className="muted">Missing — enter this field below if required.</p>}
          {field.sources.map((source, index) => <details key={`${source.page}-${index}`}><summary>Source page {source.page}</summary><p className="source-text">{source.text}</p>{pages.includes(source.page) && <Button type="button" variant="ghost" onClick={() => setSourcePage(source.page)} aria-label={`Show source page ${source.page} for ${importFieldLabels[name] ?? name}`}>Show page {source.page}</Button>}</details>)}
          {field.confidence != null && field.confidence < .8 && <p className="field-warning">Low confidence — compare this value with its source.</p>}
          {field.warnings.map(value => <p className="field-warning" key={value}>{value}</p>)}
        </div>
        {field.value != null && <div className="stack"><Button type="button" variant="secondary" disabled={busy} onClick={() => onUse(name)} aria-label={`Accept ${importFieldLabels[name] ?? name}`}>Accept</Button><Button type="button" variant="ghost" disabled={busy} onClick={() => onReject(name)} aria-label={`Reject ${importFieldLabels[name] ?? name}`}>Reject</Button></div>}
      </div>)}</div>
    </div>
    {'unresolved_concepts' in record.draft && record.draft.unresolved_concepts.length > 0 && <p className="field-warning">Unresolved concepts: {record.draft.unresolved_concepts.join(', ')}. Select canonical concepts below.</p>}
    {candidates.length > 0 && <section><h3>Candidate tests — review expected outputs</h3><p className="muted">Candidates stay outside hidden tests until you explicitly verify their input and expected output.</p>{candidates.map(candidate => <Card key={candidate.id}><h4>{candidate.id}</h4><Badge>{candidate.origin}</Badge> <Badge>{candidate.verification}</Badge><dl><dt>Input</dt><dd className="source-text">{candidate.input}</dd><dt>Expected output</dt><dd className="source-text">{candidate.expected_output}</dd></dl><div className="stack"><Button type="button" variant="secondary" disabled={busy} onClick={() => onCandidate(candidate.id, true)}>I verified {candidate.id}; add to tests</Button><Button type="button" variant="ghost" disabled={busy} onClick={() => onCandidate(candidate.id, false)}>Reject candidate {candidate.id}</Button></div></Card>)}</section>}
    <div className="stack"><Button type="button" variant="secondary" disabled={busy || record.state !== 'review-ready'} onClick={onSave}>{busy ? 'Saving…' : 'Save review draft'}</Button>{record.state !== 'review-ready' && <Button type="button" variant="secondary" disabled={busy} onClick={onRetry}>Retry extraction</Button>}{saved && <span role="status">Private review saved.</span>}</div>
  </Card>
}

function summarize(field: ImportDraftField) {
  if (Array.isArray(field.value)) return field.value.every(value => typeof value === 'string') ? field.value.join(', ').slice(0, 180) : 'Structured values — review before accepting.'
  if (field.value && typeof field.value === 'object') return JSON.stringify(field.value).slice(0, 500)
  return String(field.value ?? '').slice(0, 180)
}
