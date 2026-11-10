import { http, HttpResponse } from 'msw'
import { setupServer } from 'msw/node'

export const API = 'http://localhost/api'
export const server = setupServer(
  http.get(`${API}/auth/me`, () => HttpResponse.json({ id: 1, email: 'student@example.test', role: 'student' })),
  http.post(`${API}/auth/login`, () => HttpResponse.json({ access_token: 'test-token', token_type: 'bearer' })),
  http.get(`${API}/assignment-imports/capabilities`, () => HttpResponse.json({ enabled: true, embedded_pdf_text: true, ocr: false, ocr_provider: null })),
  http.get(`${API}/assignment-imports`, () => HttpResponse.json([])),
)
