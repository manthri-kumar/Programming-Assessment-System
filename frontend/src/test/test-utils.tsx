import type { ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { render } from '@testing-library/react'
import { AuthProvider } from '../auth/AuthProvider'

export function renderApp(node: ReactNode) { const client = new QueryClient({ defaultOptions: { queries: { retry: false }, mutations: { retry: false } } }); return render(<QueryClientProvider client={client}><BrowserRouter><AuthProvider>{node}</AuthProvider></BrowserRouter></QueryClientProvider>) }
