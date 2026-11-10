import { ApiError } from '../api/client'

const INVALID_INVITATION = 'invalid teacher registration code'
const UNCONFIGURED_INVITATION = 'teacher registration is not configured'
const DUPLICATE_EMAIL = 'email already registered'

export function registrationErrorMessage(value: unknown): string {
  if (!(value instanceof ApiError)) return 'Registration failed. Please check the entered details and try again.'
  if (value.status === 0) return 'Unable to connect to the server. Please try again.'

  const detail = typeof value.detail === 'string' ? value.detail : null
  if (value.status === 403 && detail === INVALID_INVITATION) return 'Invalid teacher invitation code.'
  if (value.status === 409 && detail === DUPLICATE_EMAIL) return 'An account with this email already exists.'
  if (value.status === 422) return 'Please check the entered details.'
  if (value.status === 503 && detail === UNCONFIGURED_INVITATION) {
    return 'Teacher registration is currently unavailable. Please contact an administrator.'
  }
  if (value.status >= 500) return 'Registration failed due to a server error. Please try again.'
  return 'Registration failed. Please check the entered details and try again.'
}
