import type { User } from '../api/types'

const TOKEN_KEY = 'codeassess.session.token'
let memoryToken: string | null = null
let memoryUser: User | null = null

export const session = {
  token(): string | null {
    if (memoryToken) return memoryToken
    memoryToken = sessionStorage.getItem(TOKEN_KEY)
    return memoryToken
  },
  user(): User | null { return memoryUser },
  setToken(token: string) { memoryToken = token; sessionStorage.setItem(TOKEN_KEY, token) },
  setUser(user: User | null) { memoryUser = user },
  clear() { memoryToken = null; memoryUser = null; sessionStorage.removeItem(TOKEN_KEY) },
}
