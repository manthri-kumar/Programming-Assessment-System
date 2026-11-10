import { ApiError, type AssignmentPayload } from '../api/client'
import type { AssignmentImportDraft, ImportDraftField, Language, TestCase } from '../api/types'

export const importFieldLabels: Record<string, string> = { title: 'Title', description: 'Description', requirements: 'Requirements', language: 'Language', input_notes: 'Input notes', output_notes: 'Output notes', constraints: 'Constraints', examples: 'Examples', concept_ids: 'Concepts', reference_source: 'Reference solution', tests: 'Hidden tests', rubric: 'Rubric', deadline: 'Deadline' }

export function importFailure(error: unknown): string {
  if (!(error instanceof ApiError)) return 'The document could not be processed. Please try again.'
  const code = error.detail && typeof error.detail === 'object' && 'code' in error.detail ? String(error.detail.code) : error.code
  const messages: Record<string, string> = {
    ocr_unavailable: 'Local OCR is unavailable. Retry after it is configured, replace the document with a text PDF, or continue manually.',
    ocr_timeout: 'Extraction timed out. Your private upload is retained; you can retry.',
    ocr_busy: 'Extraction capacity is busy. Try again shortly.',
    ocr_failed: 'Extraction failed. Retry or use a clearer document.',
    ocr_invalid_response: 'Extraction returned an invalid result. No extracted values were accepted.',
    invalid_file_type: 'Choose a PNG, JPEG, WebP, or PDF whose contents match its file type.',
    malformed_image: 'This image could not be read. Please choose another image.',
    malformed_pdf: 'This PDF could not be read. Please choose another PDF.',
    encrypted_pdf: 'Password-protected PDFs are not supported.',
    active_pdf: 'This PDF contains unsupported active or embedded content.',
    image_dimensions_exceeded: 'The image exceeds the allowed dimensions or decoded pixel limit.',
    page_limit_exceeded: 'The PDF exceeds the allowed page limit.',
    upload_size_exceeded: 'The document exceeds the upload size limit.',
    idempotency_conflict: 'This upload conflicts with an earlier request. Choose the document again.',
    import_expired: 'This private import has expired. Upload the document again.',
    import_not_found: 'This private import is no longer available.',
  }
  if (error.status === 401) return 'Your session has expired. Sign in again to continue.'
  if (error.status === 403) return 'You do not have permission to access this private import.'
  if (error.status === 429) return 'Too many import requests. Wait before trying again.'
  if (code && messages[code]) return messages[code]
  if (error.status === 0) return 'Unable to reach the server. Check your connection and try again.'
  if (error.status === 404 || error.status === 410) return 'This private import is no longer available. Upload the document again.'
  if (error.status === 413) return 'The document exceeds an upload, page, or image limit.'
  if (error.status === 409) return 'This import changed or was already confirmed. Refresh before continuing.'
  if (error.status === 503) return 'Extraction is temporarily unavailable. Your private upload can be retried.'
  if (error.status >= 500) return 'The server could not complete the import. Please try again.'
  return 'The document could not be processed. Check the file and try again.'
}

const trusted = (field: ImportDraftField) => field.origin === 'teacher-confirmed' || field.verification === 'teacher-confirmed' || field.verification === 'worker-verified'

/** Recover only supported types, keeping unreviewed grading evidence outside the form. */
export function applyImportFields(current: AssignmentPayload, draft: AssignmentImportDraft, knownConcepts: Set<string>): AssignmentPayload {
  const next = { ...current }
  for (const [name, field] of Object.entries(draft.fields)) {
    const value = field.value
    if (value == null) continue
    if (['title', 'description', 'requirements', 'input_notes', 'output_notes', 'constraints'].includes(name) && typeof value === 'string') Object.assign(next, { [name]: value })
    else if (name === 'language' && typeof value === 'string' && ['python', 'c', 'java'].includes(value)) next.language = value as Language
    else if (name === 'concept_ids' && Array.isArray(value)) next.concept_ids = value.filter((id): id is string => typeof id === 'string' && knownConcepts.has(id))
    else if (name === 'examples' && Array.isArray(value) && value.every(item => typeof item === 'string')) next.examples = value
    else if (name === 'deadline' && typeof value === 'string') next.deadline = value
    else if (name === 'reference_source' && typeof value === 'string' && trusted(field)) next.reference_source = value
    else if (name === 'tests' && Array.isArray(value) && trusted(field)) next.tests = value as TestCase[]
    else if (name === 'rubric' && typeof value === 'object' && !Array.isArray(value) && trusted(field)) next.rubric = value as AssignmentPayload['rubric']
  }
  return next
}

export function clearImportField(current: AssignmentPayload, name: string): AssignmentPayload {
  if (name === 'examples' || name === 'concept_ids' || name === 'tests') return { ...current, [name]: [] }
  if (name === 'rubric') return { ...current, rubric: { policy_version: 'core-v1', weights: {} } }
  if (name === 'deadline') return { ...current, deadline: null }
  return { ...current, [name]: '' }
}
