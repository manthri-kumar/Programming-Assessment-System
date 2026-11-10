import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { ReportView } from './student'

describe('assessment report', () => {
  it('shows exactly two top-level agents and preserves unavailable scores', () => {
    render(<ReportView result={{status:'incomplete',total:null,category:null,policy_version:'core-v1',components:{syntax:100,tests:null},limitations:['Secure execution unavailable']}}/>)
    expect(screen.getByText('ImplementationEvaluationAgent')).toBeInTheDocument(); expect(screen.getByText('FeedbackAgent')).toBeInTheDocument(); expect(screen.getByText('A missing score remains unavailable; weights are not redistributed.')).toBeInTheDocument(); expect(screen.getByText('Unavailable')).toBeInTheDocument()
    expect(screen.queryByText('Recommendations')).not.toBeInTheDocument()
  })

  it('renders structured feedback-v2 evidence without crashing', () => {
    render(<ReportView result={{status:'incomplete',total:null,category:null,policy_version:'core-v1',feedback:[{code:'execution-unavailable',message:'Secure execution is unavailable.',evidence_id:'execution:unavailable',template_version:'feedback-v2'}]}}/>)
    expect(screen.getByText(/Secure execution is unavailable/)).toBeInTheDocument()
    expect(screen.getByText(/Evidence: execution:unavailable/)).toBeInTheDocument()
  })

  it('renders stage findings and real functional outcomes from the assessment contract', () => {
    render(<ReportView result={{status:'complete',total:80,category:'Good',policy_version:'core-v1',analysis:{'syntax-analysis':{service:'syntax-analysis',status:'complete',diagnostics:[],evidence:['syntax:1'],payload:{syntax_ok:true}},'test-execution':{service:'test-execution',status:'complete',diagnostics:[],evidence:['case:one'],payload:{}}},test_outcomes:[{case_id:'one',status:'passed',stdout:'1\n',exit_code:0,weight:1}]}}/>)
    expect(screen.getByText('syntax analysis')).toBeInTheDocument()
    expect(screen.getByText('test execution')).toBeInTheDocument()
    expect(screen.getByText('one')).toBeInTheDocument()
    expect(screen.getByText('Exit code: 0')).toBeInTheDocument()
  })

  it('renders report-v3 sections and keeps teacher evidence audience restricted', () => {
    const result={status:'complete',total:80,category:'Good',policy_version:'core-v1',feedback:[{code:'issue',message:'A branch failed.',evidence_id:'test:one:wrong_output',template_version:'feedback-v3'}],report:{report_version:'assessment-report-v3',overview:{overall_explanation:'Evidence-grounded explanation.',execution_available:true},strengths:['syntax'],issues:[{code:'issue',message:'A branch failed.',explanation:'A branch failed.',category:'functional',source_location:{line:3,column:2},guidance:['Trace the branch.']}],actions:['Trace the branch.'],teacher_explanation:{summary:'Review the evidence.',evidence_refs:['test:one:wrong_output']}}}
    const {rerender}=render(<ReportView result={result}/>)
    expect(screen.getByText('Evidence-grounded explanation.')).toBeInTheDocument()
    expect(screen.getByText('Verified strengths')).toBeInTheDocument()
    expect(screen.getByText(/Line 3, column 2/)).toBeInTheDocument()
    expect(screen.queryByText('Teacher evidence review')).not.toBeInTheDocument()
    rerender(<ReportView result={result} audience="teacher"/>)
    expect(screen.getByText('Teacher evidence review')).toBeInTheDocument()
  })
})
