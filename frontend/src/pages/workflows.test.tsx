import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { http, HttpResponse } from 'msw'
import { describe, expect, it, vi } from 'vitest'
import { AssignmentListPage, ReportView } from './student'
import { AssignmentFormPage, assignmentError, validateAssignment } from './teacher'
import { ApiError, api, type AssignmentPayload } from '../api/client'
import { API, server } from '../test/server'
import type { AssignmentImport } from '../api/types'

const assignment = { id: 1, teacher_id: 2, title: 'Array Sum', description: 'Add values', language: 'python', created_at: '2026-01-01T00:00:00Z', requirements: '', input_notes: '', output_notes: '', examples: [], constraints_text: '', concept_ids: ['loops'], deadline: null }
function renderQuery(node: React.ReactNode) { const client=new QueryClient({defaultOptions:{queries:{retry:false},mutations:{retry:false}}});return render(<QueryClientProvider client={client}><MemoryRouter>{node}</MemoryRouter></QueryClientProvider>) }
const graph = { version: 'concept-v1', nodes: [{ id: 'input', label: 'Input Handling', guidance: 'Read input safely' }, { id: 'loops', label: 'Loops', guidance: 'Practice loops' }], edges: [] }
function mockGraph() { server.use(http.get(`${API}/concept-graph`, () => HttpResponse.json(graph))) }

describe('student and teacher workflows', () => {
  it('filters assignments using real API fields', async () => { server.use(http.get(`${API}/assignments`,()=>HttpResponse.json([assignment,{...assignment,id:2,title:'Java Branches',language:'java',concept_ids:['conditionals']}])),http.get(`${API}/bookmarks`,()=>HttpResponse.json([])));renderQuery(<AssignmentListPage/>);expect(await screen.findByText('Array Sum')).toBeInTheDocument();await userEvent.selectOptions(screen.getByLabelText('Language'),'java');expect(screen.queryByText('Array Sum')).not.toBeInTheDocument();expect(screen.getByText('Java Branches')).toBeInTheDocument() })
  it('blocks invalid teacher rubric totals before mutation', async () => { let mutated=false;mockGraph();server.use(http.post(`${API}/assignments`,()=>{mutated=true;return HttpResponse.json({})}));renderQuery(<AssignmentFormPage/>);await userEvent.type(await screen.findByLabelText('Title'),'Safe task');await userEvent.type(screen.getByLabelText('Reference solution'),'print(1)');for(const input of screen.getAllByRole('spinbutton').slice(0,4))await userEvent.clear(input);await userEvent.click(screen.getByRole('button',{name:'Save assignment'}));expect(await screen.findByRole('alert')).toHaveTextContent('highlighted');expect(screen.getByText(/sum to 1/i)).toBeInTheDocument();expect(mutated).toBe(false) })
  it('searches graph concepts and submits canonical assignment fields', async () => {
    mockGraph();let payload:unknown
    server.use(http.post(`${API}/assignments`,async({request})=>{payload=await request.json();return HttpResponse.json({...assignment,id:9,title:'Echo input'},{status:201})}))
    renderQuery(<AssignmentFormPage/>);await screen.findByLabelText('Title')
    await userEvent.type(screen.getByLabelText('Search concepts'),'Input')
    expect(screen.queryByText('Loops')).not.toBeInTheDocument()
    await userEvent.click(screen.getByLabelText(/Input Handling/))
    await userEvent.type(screen.getByLabelText('Title'),'Echo input')
    await userEvent.type(screen.getByLabelText('Reference solution'),'print(input())')
    await userEvent.type(screen.getByLabelText('Deadline'),'2026-12-01T12:00')
    await userEvent.click(screen.getByRole('button',{name:'Save assignment'}))
    await waitFor(()=>expect(payload).toBeTruthy())
    expect(payload).toMatchObject({title:'Echo input',language:'python',reference_source:'print(input())',concept_ids:['input'],tests:[{id:'case-1',weight:1,concept_ids:[]}],rubric:{policy_version:'core-v1',weights:{structure:.25,syntax:.15,tests:.5,originality:.1}}})
    expect((payload as {deadline:string}).deadline).toMatch(/^2026-12-01T/)
  })
  it('shows unknown backend concept IDs as a field error', async () => {
    mockGraph();server.use(http.post(`${API}/assignments`,()=>HttpResponse.json({error:{code:'validation_error',message:'request could not be completed'},detail:{unknown_concepts:['input']}},{status:422})))
    renderQuery(<AssignmentFormPage/>);await screen.findByLabelText('Title')
    await userEvent.click(screen.getByLabelText(/Input Handling/));await userEvent.type(screen.getByLabelText('Title'),'Echo');await userEvent.type(screen.getByLabelText('Reference solution'),'print(input())');await userEvent.click(screen.getByRole('button',{name:'Save assignment'}))
    expect(await screen.findByText(/Unknown concept IDs: input/)).toBeInTheDocument();expect(screen.getByRole('alert')).toHaveTextContent('highlighted')
  })
  it('imports a reviewed draft into the canonical assignment form without publishing automatically', async () => {
    mockGraph(); let confirmed:unknown; let createCalls=0
    const record:AssignmentImport={public_id:'import-1',state:'review-ready',media_type:'application/pdf',original_name:'question.pdf',byte_size:100,content_hash:'a'.repeat(64),metadata:{pages:1},extraction:{segments:[{page:1,method:'embedded-text',text:'Echo input',confidence:1}]},config_hash:'b'.repeat(64),assignment_id:null,expires_at:'2026-12-01T00:00:00Z',created_at:'2026-11-01T00:00:00Z',updated_at:'2026-11-01T00:00:00Z',draft:{schema_version:'assignment-import-draft-v1',config_hash:'b'.repeat(64),unresolved_concepts:[],candidate_tests:[],fields:{title:{value:'Echo input',origin:'extracted',confidence:1,sources:[{page:1,text:'Echo input'}],warnings:[]},description:{value:'Read and echo a value',origin:'extracted',confidence:1,sources:[{page:1,text:'Description'}],warnings:[]},language:{value:'python',origin:'extracted',confidence:1,sources:[{page:1,text:'Python'}],warnings:[]},concept_ids:{value:['input'],origin:'extracted',confidence:1,sources:[{page:1,text:'Input'}],warnings:[]},rubric:{value:{policy_version:'core-v1'},origin:'provider-suggested',confidence:.5,sources:[],warnings:['Review rubric weights.']}}}}
    vi.spyOn(api,'createImport').mockImplementation(async()=>{createCalls++;return {...record,state:'validated',draft:{}}});vi.spyOn(api,'extractImport').mockResolvedValue(record);vi.spyOn(api,'updateImportDraft').mockResolvedValue(record);vi.spyOn(api,'importPreview').mockRejectedValue(new Error('preview omitted in component test'));vi.spyOn(api,'confirmImport').mockImplementation(async(_id,payload)=>{confirmed=payload;return {...assignment,id:12,title:'Echo input',language:'python' as const}})
    renderQuery(<AssignmentFormPage/>);await screen.findByLabelText('Title');await userEvent.click(screen.getByRole('button',{name:/Upload Image\/PDF/}));const file=new File(['%PDF-test'],'question.pdf',{type:'application/pdf'});fireEvent.change(screen.getByLabelText(/Choose document/),{target:{files:[file]}})
    expect(await screen.findByText('Review extracted draft',{}, {timeout:5000})).toBeInTheDocument();expect(screen.getByLabelText('Title')).toHaveValue('Echo input');expect(createCalls).toBe(1);expect(confirmed).toBeUndefined()
    await userEvent.type(screen.getByLabelText('Reference solution'),'print(input())');await userEvent.click(screen.getByRole('button',{name:'Confirm and create assignment'}));await waitFor(()=>expect(confirmed).toBeTruthy());expect(confirmed).toMatchObject({title:'Echo input',language:'python',concept_ids:['input']})
  })
  it('fails closed when the concept graph cannot load', async () => {let mutated=false;server.use(http.get(`${API}/concept-graph`,()=>HttpResponse.json({error:{message:'failure'}},{status:500})),http.post(`${API}/assignments`,()=>{mutated=true;return HttpResponse.json({})}));renderQuery(<AssignmentFormPage/>);expect(await screen.findByText('Concepts could not be loaded.')).toBeInTheDocument();expect(screen.getByRole('button',{name:'Save assignment'})).toBeDisabled();expect(mutated).toBe(false)})
  it('validates blank reference, duplicate tests, and safe server errors', () => {
    const value:AssignmentPayload={title:'Task',description:'',language:'python',reference_source:' ',tests:[{id:'same',input:'',expected_output:'',weight:1,concept_ids:[]},{id:'same',input:'',expected_output:'',weight:0,concept_ids:[]}],rubric:{policy_version:'core-v1',weights:{structure:.25,syntax:.15,tests:.5,originality:.1}},concept_ids:['missing']}
    const errors=validateAssignment(value,new Set(['input']));expect(errors.reference_source).toContain('blank');expect(errors['tests.1.id']).toContain('duplicated');expect(errors['tests.1.weight']).toContain('positive');expect(errors.concept_ids).toContain('missing')
    expect(assignmentError(new ApiError(0,'network')).summary).toContain('connect');expect(assignmentError(new ApiError(403,'hidden')).summary).toContain('not authorized');expect(assignmentError(new ApiError(422,'generic','validation',undefined,[{loc:['body','title'],msg:'Field required',input:'secret'}])).fields.title).toBe('Field required')
  })
  it('renders contradictory/unavailable evidence without inventing a score', async () => { render(<ReportView result={{status:'incomplete',total:null,category:null,policy_version:'core-v1',feedback:['Syntax evidence conflicts with tests'],recommendations:[{concept_id:'loops',guidance:'Review loop bounds'}],limitations:['Execution unavailable']}}/>);expect(screen.getByText('Syntax evidence conflicts with tests')).toBeInTheDocument();expect(screen.getByText('Review loop bounds')).toBeInTheDocument();await waitFor(()=>expect(screen.getByText('—')).toBeInTheDocument()) })
})
