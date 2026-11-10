import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './app/App'
import { AuthProvider } from './auth/AuthProvider'
import './styles/index.css'

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: (count, error) => !(error instanceof Error && 'status' in error && ([401,403,404,422].includes(Number((error as {status?:number}).status)))) && count < 2, staleTime: 15_000 }, mutations: { retry: false } } })
createRoot(document.getElementById('root')!).render(<StrictMode><QueryClientProvider client={queryClient}><BrowserRouter><AuthProvider><App/></AuthProvider></BrowserRouter></QueryClientProvider></StrictMode>)
