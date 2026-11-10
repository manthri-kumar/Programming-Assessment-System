import axios, { AxiosError } from 'axios'
import { session } from '../auth/session'
import type { Activity, ApiErrorBody, Assignment, AssignmentImport, AssessmentResult, ConceptGraph, Draft, EvaluationRecord, ImportCapabilities, Language, Progress, Role, Submission, TeacherAnalytics, TestCase, TokenResponse, User } from './types'

export class ApiError extends Error {
  constructor(public status: number, message: string, public code?: string, public requestId?: string, public detail?: unknown) { super(message) }
  get isExecutionUnavailable() { return this.status === 503 }
}

export const http = axios.create({ baseURL: import.meta.env.VITE_API_BASE_URL || '/api', timeout: 15_000 })
http.interceptors.request.use((config) => { const token = session.token(); if (token) config.headers.Authorization = `Bearer ${token}`; return config })
http.interceptors.response.use((response) => response, (error: AxiosError<ApiErrorBody>) => {
  const status = error.response?.status ?? 0
  const body = error.response?.data
  if (status === 401) { session.clear(); window.dispatchEvent(new CustomEvent('codeassess:session-expired')) }
  return Promise.reject(new ApiError(status, body?.error?.message || (status ? 'Request could not be completed' : 'The API is unreachable'), body?.error?.code, body?.error?.request_id, body?.detail))
})

export const queryKeys = {
  me: ['auth', 'me'] as const,
  assignments: ['assignments'] as const,
  assignment: (id: number) => ['assignments', id] as const,
  submissions: (assignmentId?: number, limit = 50, offset = 0) => ['submissions', assignmentId ?? 'all', limit, offset] as const,
  evaluation: (id: number) => ['evaluation', id] as const,
  progress: ['student', 'progress'] as const,
  analytics: ['teacher', 'analytics'] as const,
  graph: ['concept-graph'] as const,
  bookmarks: ['bookmarks'] as const,
  draft: (id: number) => ['draft', id] as const,
  activity: ['student', 'activity'] as const,
  importCapabilities: ['assignment-imports', 'capabilities'] as const,
  assignmentImport: (id: string) => ['assignment-imports', id] as const,
  assignmentImports: ['assignment-imports'] as const,
}

export const api = {
  login: (email: string, password: string) => http.post<TokenResponse>('/auth/login', { email, password }).then(r => r.data),
  register: (email: string, password: string, role: Role, teacher_registration_code?: string) => http.post<User>('/auth/register', { email, password, role, teacher_registration_code }).then(r => r.data),
  me: (signal?: AbortSignal) => http.get<User>('/auth/me', { signal }).then(r => r.data),
  assignments: (input?: AbortSignal | { signal: AbortSignal }) => http.get<Assignment[]>('/assignments', { signal: input instanceof AbortSignal ? input : input?.signal }).then(r => r.data),
  assignment: (id: number, signal?: AbortSignal) => http.get<Assignment>(`/assignments/${id}`, { signal }).then(r => r.data),
  createAssignment: (value: AssignmentPayload) => http.post<Assignment>('/assignments', value).then(r => r.data),
  updateAssignment: (id: number, value: Partial<AssignmentPayload>) => http.patch<Assignment>(`/assignments/${id}`, value).then(r => r.data),
  submissions: (assignmentId?: number, limit = 50, offset = 0, signal?: AbortSignal) => http.get<Submission[]>('/submissions', { params: { ...(assignmentId ? { assignment_id: assignmentId } : {}), limit, offset }, signal }).then(r => r.data),
  submission: (id: number) => http.get<Submission>(`/submissions/${id}`).then(r => r.data),
  submit: (assignment_id: number, language: Language, source: string) => http.post<Submission>('/submissions', { assignment_id, language, source }).then(r => r.data),
  evaluate: (id: number) => http.post<AssessmentResult>(`/submissions/${id}/evaluate`).then(r => r.data),
  evaluation: (id: number) => http.get<EvaluationRecord>(`/submissions/${id}/evaluation`).then(r => r.data),
  progress: () => http.get<Progress>('/student/progress').then(r => r.data),
  analytics: () => http.get<TeacherAnalytics>('/teacher/analytics').then(r => r.data),
  graph: () => http.get<ConceptGraph>('/concept-graph').then(r => r.data),
  bookmarks: () => http.get<Assignment[]>('/bookmarks').then(r => r.data),
  addBookmark: (id: number) => http.put(`/bookmarks/${id}`),
  removeBookmark: (id: number) => http.delete(`/bookmarks/${id}`),
  draft: (id: number) => http.get<Draft>(`/assignments/${id}/draft`).then(r => r.data),
  saveDraft: (id: number, language: Language, source: string) => http.put<Draft>(`/assignments/${id}/draft`, { language, source }).then(r => r.data),
  deleteDraft: (id: number) => http.delete(`/assignments/${id}/draft`),
  activity: () => http.get<Activity[]>('/student/activity').then(r => r.data),
  importCapabilities: () => http.get<ImportCapabilities>('/assignment-imports/capabilities').then(r => r.data),
  assignmentImports: () => http.get<AssignmentImport[]>('/assignment-imports').then(r => r.data),
  assignmentImport: (id: string) => http.get<AssignmentImport>(`/assignment-imports/${id}`).then(r => r.data),
  createImport: (file: File, idempotencyKey: string) => { const body = new FormData(); body.append('file', file); return http.post<AssignmentImport>('/assignment-imports', body, { headers: { 'Idempotency-Key': idempotencyKey } }).then(r => r.data) },
  extractImport: (id: string) => http.post<AssignmentImport>(`/assignment-imports/${id}/extract`, undefined, { timeout: 125_000 }).then(r => r.data),
  updateImportDraft: (id: string, fields: Record<string, unknown>, rejected_fields: string[] = [], confirmed_candidate_ids: string[] = [], rejected_candidate_ids: string[] = []) => http.patch<AssignmentImport>(`/assignment-imports/${id}/draft`, { fields, rejected_fields, confirmed_candidate_ids, rejected_candidate_ids }).then(r => r.data),
  confirmImport: (id: string, value: AssignmentPayload) => http.post<Assignment>(`/assignment-imports/${id}/confirm`, value).then(r => r.data),
  deleteImport: (id: string) => http.delete(`/assignment-imports/${id}`),
  importPreview: (id: string) => http.get<Blob>(`/assignment-imports/${id}/preview`, { responseType: 'blob' }).then(r => r.data),
}

export interface AssignmentPayload {
  title: string; description: string; language: Language; reference_source: string; tests: TestCase[]; rubric: { policy_version: 'core-v1'; weights?: Record<string, number> }
  requirements?: string; input_notes?: string; output_notes?: string; examples?: string[]; constraints?: string; concept_ids?: string[]; deadline?: string | null
}
