import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { Button, Modal, ProgressRing } from './ui'

describe('shared accessible components', () => {
  it('supports keyboard activation and labeled progress', async () => { const clicked=vi.fn();render(<><Button onClick={clicked}>Continue</Button><ProgressRing value={68} label="Average"/></>);screen.getByRole('button',{name:'Continue'}).focus();await userEvent.keyboard('{Enter}');expect(clicked).toHaveBeenCalledOnce();expect(screen.getByText('68%')).toBeInTheDocument() })
  it('exposes dialogs to assistive technology', () => { render(<Modal title="Confirm submission" close={()=>undefined}>Safe action</Modal>);expect(screen.getByRole('dialog',{name:'Confirm submission'})).toBeInTheDocument() })
})
