import { describe, expect, it } from 'vitest'
import { ApiError } from '../api/client'
import { registrationErrorMessage } from './registration-errors'

describe('registration error messages', () => {
  it.each([
    [new ApiError(0, 'transport failed'), 'Unable to connect to the server. Please try again.'],
    [new ApiError(403, 'generic', 'authorization_error', 'req', 'invalid teacher registration code'), 'Invalid teacher invitation code.'],
    [new ApiError(409, 'generic', 'conflict', 'req', 'email already registered'), 'An account with this email already exists.'],
    [new ApiError(422, 'generic', 'validation_error', 'req', [{ msg: 'invalid' }]), 'Please check the entered details.'],
    [new ApiError(503, 'generic', 'infrastructure_error', 'req', 'teacher registration is not configured'), 'Teacher registration is currently unavailable. Please contact an administrator.'],
    [new ApiError(500, 'generic', 'internal_error', 'req', 'private database detail'), 'Registration failed due to a server error. Please try again.'],
    [new ApiError(403, 'generic', 'authorization_error', 'req', 'private authorization detail'), 'Registration failed. Please check the entered details and try again.'],
  ])('maps a safe registration failure', (error, expected) => {
    expect(registrationErrorMessage(error)).toBe(expected)
    expect(registrationErrorMessage(error)).not.toContain('private')
  })
})
