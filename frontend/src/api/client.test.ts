import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'
import { ApiError, api } from './client'
import { server, API } from '../test/server'
import { session } from '../auth/session'

describe('API transport', () => {
  it('attaches the bearer token and returns typed resources', async () => {
    session.setToken('secret-test-token')
    server.use(http.get(`${API}/assignments`, ({ request }) => {
      expect(request.headers.get('authorization')).toBe('Bearer secret-test-token')
      return HttpResponse.json([])
    }))
    await expect(api.assignments()).resolves.toEqual([])
  })
  it.each([401, 403, 404, 422, 503, 500])('maps HTTP %s into a stable ApiError', async status => {
    session.setToken('secret-test-token')
    server.use(http.get(`${API}/assignments`, () => HttpResponse.json({ error: { code: 'test_error', message: 'Request failed', request_id: 'req-1' } }, { status })))
    await expect(api.assignments()).rejects.toMatchObject({ status, code: 'test_error', requestId: 'req-1' })
    if (status === 401) expect(session.token()).toBeNull()
  })
  it('recognizes fail-closed execution unavailability', () => expect(new ApiError(503, 'Unavailable').isExecutionUnavailable).toBe(true))
  it('supports caller cancellation for idempotent reads', async () => {
    const controller = new AbortController()
    controller.abort()
    await expect(api.assignments(controller.signal)).rejects.toMatchObject({ status: 0 })
  })
  it('sends bounded submission pagination parameters', async () => {
    server.use(http.get(`${API}/submissions`, ({ request }) => {
      const url = new URL(request.url)
      expect(url.searchParams.get('limit')).toBe('20')
      expect(url.searchParams.get('offset')).toBe('40')
      return HttpResponse.json([])
    }))
    await expect(api.submissions(undefined, 20, 40)).resolves.toEqual([])
  })
})
