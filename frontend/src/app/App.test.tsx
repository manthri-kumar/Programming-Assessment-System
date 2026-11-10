import { screen } from '@testing-library/react'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import App from './App'
import { renderApp } from '../test/test-utils'
import { API, server } from '../test/server'
import { session } from '../auth/session'

function studentData() {
  server.use(
    http.get(`${API}/assignments`, () => HttpResponse.json([])),
    http.get(`${API}/concept-graph`, () => HttpResponse.json({ version: 'concept-v1', nodes: [], edges: [] })),
    http.get(`${API}/submissions`, () => HttpResponse.json([])),
    http.get(`${API}/student/progress`, () => HttpResponse.json({ student_id: 1, submission_count: 0, evaluated_count: 0, average_score: null, status_counts: {}, category_counts: {} })),
    http.get(`${API}/bookmarks`, () => HttpResponse.json([])),
    http.get(`${API}/student/activity`, () => HttpResponse.json([])),
  )
}

describe('role routes', () => {
  it('redirects unauthenticated protected URLs to login', async () => { history.pushState({}, '', '/student/progress'); renderApp(<App/>); expect(await screen.findByRole('heading', { name: 'Welcome back' })).toBeInTheDocument() })
  it('redirects a student away from teacher routes without a teacher mutation', async () => { let teacherMutation=false; server.use(http.post(`${API}/assignments`, () => { teacherMutation=true; return HttpResponse.json({}, { status: 403 }) })); studentData(); session.setToken('student-token'); history.pushState({}, '', '/teacher/assignments/new'); renderApp(<App/>); expect(await screen.findByText(/Good (morning|afternoon|evening)/)).toBeInTheDocument(); expect(teacherMutation).toBe(false) })
})
