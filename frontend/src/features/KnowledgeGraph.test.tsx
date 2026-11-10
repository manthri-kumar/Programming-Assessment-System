import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'
import KnowledgeGraphView from './KnowledgeGraph'

describe('knowledge graph', () => {
  it('provides a keyboard-accessible equivalent of server relationships', async () => { render(<KnowledgeGraphView graph={{version:'concept-v1',nodes:[{id:'input',label:'Input',guidance:'Read input'},{id:'loops',label:'Loops',guidance:'Bound iteration'}],edges:[{id:'input->loops',source:'input',target:'loops',type:'prerequisite'}]}} result={{status:'complete',total:70,category:'Good',policy_version:'core-v1',recommendations:[{concept_id:'loops'}]}}/>);const loops=screen.getByRole('button',{name:/LoopsRequires: Input/});await userEvent.click(loops);expect(loops).toHaveAttribute('aria-pressed','true');expect(screen.getByText('Bound iteration')).toBeInTheDocument();expect(screen.getByText('Current recommendation')).toBeInTheDocument() })
})
