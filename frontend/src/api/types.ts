export type Role = 'student' | 'teacher'
export type Language = 'python' | 'c' | 'java'

export interface User { id: number; email: string; role: Role }
export interface TokenResponse { access_token: string; token_type: 'bearer' }
export interface Rubric { policy_version: 'core-v1'; weights?: Record<string, number> }
export interface TestCase { id: string; input: string; expected_output: string; weight: number; concept_ids: string[] }
export interface Assignment {
  id: number; teacher_id: number; title: string; description: string; language: Language; created_at: string
  requirements: string; input_notes: string; output_notes: string; examples: string[]; constraints_text: string
  concept_ids: string[]; deadline: string | null; rubric?: Rubric; reference_source?: string; tests?: TestCase[]
}
export interface EvaluationSummary { status: string; total: number | null; category: string | null }
export interface Submission { id: number; assignment_id: number; student_id: number; language: Language; status: string; created_at: string; source?: string; evaluation: EvaluationSummary | null }
export interface Evidence { id?: string; kind?: string; message?: string; concept_ids?: string[]; [key: string]: unknown }
export interface SourceLocation { line: number; column: number; end_line?: number | null; end_column?: number | null }
export interface FeedbackItem { code?: string; message: string; evidence_id?: string; template_version?: string; category?: string; severity?: string; explanation?: string; root_cause?: string; evidence_refs?: string[]; concept_ids?: string[]; source_location?: SourceLocation | null; guidance?: string[]; confidence?: number | null; limitations?: string[] }
export interface Recommendation { concept_id?: string; label?: string; guidance?: string; path?: string[]; evidence_ids?: string[]; [key: string]: unknown }
export interface AnalysisStage { service: string; status: string; evidence?: string[]; diagnostics?: string[]; payload?: Record<string, unknown>; service_version?: string; metadata?: { schema_version?: string; classification?: string; confidence?: number | null; limitations?: string[]; diagnostics?: Array<{ code: string; message: string; location?: SourceLocation | null }> } }
export interface TestOutcome { case_id?: string; status: string; stdout?: string; stderr?: string; exit_code?: number | null; weight?: number }
export interface AssessmentResult {
  status: string; total: number | null; category: string | null; policy_version: string
  components?: Record<string, number | null>; weights?: Record<string, number>; evidence?: Evidence[]; diagnostics?: Evidence[]
  feedback?: Array<string | FeedbackItem>; recommendations?: Recommendation[]; limitations?: string[]; report?: Record<string, unknown>
  analysis?: Record<string, AnalysisStage>; test_outcomes?: TestOutcome[]; agent_trace?: string[]; agents?: Array<{ agent: string; [key: string]: unknown }>
}
export interface EvaluationRecord { id: number; submission_id: number; policy_version: string; result: AssessmentResult; created_at: string }
export interface Progress { student_id: number; submission_count: number; evaluated_count: number; average_score: number | null; status_counts: Record<string, number>; category_counts: Record<string, number> }
export interface TeacherAnalytics extends Omit<Progress, 'student_id'> { assignment_count: number }
export interface ConceptNode { id: string; label: string; guidance: string }
export interface ConceptEdge { id: string; source: string; target: string; type: 'prerequisite' }
export interface ConceptGraph { version: string; nodes: ConceptNode[]; edges: ConceptEdge[] }
export interface Draft { student_id: number; assignment_id: number; language: Language; source: string; updated_at: string }
export interface Activity { id: number; kind: string; assignment_id: number | null; submission_id: number | null; created_at: string }

export type ImportOrigin = 'missing' | 'extracted' | 'provider-suggested' | 'teacher-confirmed'
export interface ImportSourceRef { page: number; text: string }
export interface ImportDraftField { value: unknown; origin: ImportOrigin; confidence: number | null; sources: ImportSourceRef[]; warnings: string[]; verification?: 'unverified' | 'source-provided' | 'teacher-confirmed' | 'worker-verified' }
export interface ImportCandidate { id: string; input: string; expected_output: string; origin: 'extracted' | 'provider-generated'; verification: 'unverified' | 'teacher-confirmed' | 'worker-verified'; sources: ImportSourceRef[] }
export interface AssignmentImportDraft { schema_version: 'assignment-import-draft-v1'; fields: Record<string, ImportDraftField>; unresolved_concepts: string[]; candidate_tests: ImportCandidate[]; config_hash: string }
export interface AssignmentImport {
  public_id: string; state: string; media_type: string; original_name: string; byte_size: number; content_hash: string
  metadata: Record<string, unknown>; extraction: { schema_version?: string; segments?: Array<{ page: number; method: string; text: string; confidence: number | null }> }
  draft: AssignmentImportDraft | Record<string, never>; config_hash: string; assignment_id: number | null; expires_at: string; created_at: string; updated_at: string
}
export interface ImportCapabilities { enabled: boolean; embedded_pdf_text: boolean; ocr: boolean; ocr_provider: string | null }

export interface ApiErrorBody { error?: { code?: string; message?: string; request_id?: string }; detail?: unknown }
