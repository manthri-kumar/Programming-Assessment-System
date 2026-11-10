import { fireEvent, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { AuthPage } from './AuthPage'
import { renderApp } from '../test/test-utils'
import { API, server } from '../test/server'

describe('authentication page', () => {
  it('validates short passwords without sending credentials', async () => {
    renderApp(<AuthPage/>); await userEvent.type(screen.getByLabelText('Email'), 'student@example.test'); await userEvent.type(screen.getByLabelText('Password'), 'short'); fireEvent.click(screen.getAllByRole('button', { name: 'Sign in' }).at(-1)!); expect(await screen.findByRole('alert')).toHaveTextContent('at least 8')
  })
  it('keeps teacher registration invitation-gated', async () => {
    let payload: unknown
    server.use(http.post(`${API}/auth/register`, async ({request}) => { payload = await request.json(); return HttpResponse.json({id:2,email:'teacher@example.test',role:'teacher'},{status:201}) }))
    renderApp(<AuthPage/>); fireEvent.click(screen.getByRole('button',{name:'Register'})); fireEvent.change(screen.getByLabelText('Email'),{target:{value:'teacher@example.test'}}); fireEvent.change(screen.getByLabelText('Password'),{target:{value:'password123'}}); fireEvent.change(screen.getByLabelText('Role'),{target:{value:'teacher'}}); fireEvent.change(screen.getByLabelText('Teacher invitation code'),{target:{value:'invite-code'}}); fireEvent.click(screen.getByRole('button',{name:'Create account'})); await waitFor(()=>expect(payload).toMatchObject({role:'teacher',teacher_registration_code:'invite-code'}))
  })
  it('normalizes student registration and omits teacher credentials', async () => {
    let payload: Record<string, unknown> = {}
    server.use(http.post(`${API}/auth/register`, async ({ request }) => {
      payload = await request.json() as Record<string, unknown>
      return HttpResponse.json({ id: 3, email: 'student@example.test', role: 'student' }, { status: 201 })
    }))
    renderApp(<AuthPage/>); fireEvent.click(screen.getByRole('button', { name: 'Register' })); fireEvent.change(screen.getByLabelText('Email'), { target: { value: '  student@example.test  ' } }); fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } }); fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Account created')
    expect(payload).toEqual({ email: 'student@example.test', password: 'password123', role: 'student' })
  })
  it('shows the safe invitation reason instead of the generic API message', async () => {
    server.use(http.post(`${API}/auth/register`, () => HttpResponse.json({ error: { code: 'authorization_error', message: 'request could not be completed', request_id: 'req-1' }, detail: 'invalid teacher registration code' }, { status: 403 })))
    renderApp(<AuthPage/>); fireEvent.click(screen.getByRole('button', { name: 'Register' })); fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'teacher@example.test' } }); fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } }); fireEvent.change(screen.getByLabelText('Role'), { target: { value: 'teacher' } }); fireEvent.change(screen.getByLabelText('Teacher invitation code'), { target: { value: 'not-the-configured-code' } }); fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Invalid teacher invitation code.')
    expect(screen.queryByText('Account created. Sign in to continue.')).not.toBeInTheDocument()
    expect(screen.queryByText('request could not be completed')).not.toBeInTheDocument()
  })
  it('prevents submission when email or teacher invitation input is missing', async () => {
    let requests = 0
    server.use(http.post(`${API}/auth/register`, () => { requests += 1; return HttpResponse.json({}, { status: 201 }) }))
    renderApp(<AuthPage/>); fireEvent.click(screen.getByRole('button', { name: 'Register' })); fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'teacher@example.test' } }); fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } }); fireEvent.change(screen.getByLabelText('Role'), { target: { value: 'teacher' } }); fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    await waitFor(() => expect(requests).toBe(0))
  })
  it.each([
    [409, 'email already registered', 'An account with this email already exists.'],
    [422, [{ msg: 'invalid email' }], 'Please check the entered details.'],
    [503, 'teacher registration is not configured', 'Teacher registration is currently unavailable. Please contact an administrator.'],
    [500, 'private database failure', 'Registration failed due to a server error. Please try again.'],
  ])('reports safe HTTP %s registration failures', async (status, detail, expected) => {
    server.use(http.post(`${API}/auth/register`, () => HttpResponse.json({ error: { code: 'registration_error', message: 'request could not be completed', request_id: 'req-safe' }, detail }, { status })))
    renderApp(<AuthPage/>); fireEvent.click(screen.getByRole('button', { name: 'Register' })); fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'student@example.test' } }); fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } }); fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(expected)
    expect(screen.queryByText(/private database failure/i)).not.toBeInTheDocument()
  })
  it('distinguishes an unreachable backend', async () => {
    server.use(http.post(`${API}/auth/register`, () => HttpResponse.error()))
    renderApp(<AuthPage/>); fireEvent.click(screen.getByRole('button', { name: 'Register' })); fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'student@example.test' } }); fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'password123' } }); fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Unable to connect to the server. Please try again.')
  })
})
