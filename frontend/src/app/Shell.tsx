import { useEffect, useState } from 'react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { BookOpen, Bookmark, Braces, ChartNoAxesColumnIncreasing, ClipboardList, Gauge, GraduationCap, LogOut, Menu, Search, Settings, Users, X } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { api, queryKeys } from '../api/client'
import { useAuth } from '../auth/AuthProvider'
import { Button } from '../components/ui'

const studentLinks = [
  ['Dashboard', '/student', Gauge], ['Assignments', '/student/assignments', Braces], ['My Submissions', '/student/submissions', ClipboardList],
  ['Progress', '/student/progress', ChartNoAxesColumnIncreasing], ['Bookmarks', '/student/bookmarks', Bookmark],
  ['Recommended', '/student/recommended', GraduationCap], ['Learning Path', '/student/learning', BookOpen],
] as const
const teacherLinks = [['Dashboard', '/teacher', Gauge], ['Assignments', '/teacher/assignments', Braces], ['Submissions', '/teacher/submissions', Users]] as const

export function AppShell() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [search, setSearch] = useState('')
  const [searchOpen, setSearchOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const { data: assignments = [] } = useQuery({ queryKey: queryKeys.assignments, queryFn: ({ signal }) => api.assignments(signal) })
  const { data: graph } = useQuery({ queryKey: queryKeys.graph, queryFn: api.graph })
  const links = user?.role === 'teacher' ? teacherLinks : studentLinks
  const results = search.trim() ? [
    ...assignments.filter(item => `${item.title} ${item.description}`.toLowerCase().includes(search.toLowerCase())).map(item => ({ label: item.title, to: user?.role === 'teacher' ? `/teacher/assignments/${item.id}/edit` : `/student/assignments/${item.id}` })),
    ...(user?.role === 'student' ? (graph?.nodes ?? []).filter(item => `${item.label} ${item.guidance}`.toLowerCase().includes(search.toLowerCase())).map(item => ({ label: item.label, to: '/student/learning' })) : []),
  ].slice(0, 8) : []
  useEffect(() => {
    const handler = (event: KeyboardEvent) => { if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); document.getElementById('global-search')?.focus() } }
    document.addEventListener('keydown', handler); return () => document.removeEventListener('keydown', handler)
  }, [])
  return <div className="app-shell">
    <aside className={`sidebar ${open ? 'open' : ''}`} aria-label="Primary navigation">
      <div className="brand"><span className="brand-mark">&lt;/&gt;</span><span>Code<span className="brand-accent">Assess</span></span><Button className="mobile-only" variant="ghost" onClick={() => setOpen(false)} aria-label="Close navigation"><X /></Button></div>
      <nav className="nav">{links.map(([label, to, Icon]) => <NavLink end={to === '/student' || to === '/teacher'} key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`} onClick={() => setOpen(false)}><Icon aria-hidden="true"/>{label}</NavLink>)}</nav>
      <div className="nav-spacer" />
      <nav className="nav"><NavLink to={`/${user?.role}/settings`} className="nav-link"><Settings aria-hidden="true"/>Settings</NavLink><button className="nav-link" onClick={() => { logout(); navigate('/login') }}><LogOut aria-hidden="true"/>Logout</button></nav>
    </aside>
    <header className="topbar">
      <Button className="mobile-toggle" variant="secondary" onClick={() => setOpen(true)} aria-label="Open navigation"><Menu /></Button>
      <div className="search-wrap"><Search aria-hidden="true" size={18}/><label className="sr-only" htmlFor="global-search">Search assignments and concepts</label><input id="global-search" className="search" value={search} onChange={e => { setSearch(e.target.value); setSearchOpen(true) }} onFocus={() => setSearchOpen(true)} placeholder="Search assignments, topics, or concepts…" autoComplete="off"/><span className="key">Ctrl K</span>{searchOpen && search && <div className="search-results" role="listbox">{results.length ? results.map(result => <button key={`${result.to}-${result.label}`} onMouseDown={() => { navigate(result.to); setSearch(''); setSearchOpen(false) }}>{result.label}</button>) : <p>No results</p>}</div>}</div>
      <div className="profile-wrap"><button className="top-user profile-trigger" aria-label="Open profile menu" aria-expanded={profileOpen} aria-haspopup="menu" onClick={() => setProfileOpen(value => !value)}><span className="avatar">{user?.email.slice(0,1).toUpperCase()}</span><span className="user-label">{user?.role === 'teacher' ? 'Teacher' : 'Student'}</span></button>{profileOpen&&<div className="profile-menu" role="menu"><span>{user?.email}</span><button role="menuitem" onClick={()=>{setProfileOpen(false);navigate(`/${user?.role}/settings`)}}>Settings</button><button role="menuitem" onClick={()=>{setProfileOpen(false);logout();navigate('/login')}}>Logout</button></div>}</div>
    </header>
    <main className="main" onClick={() => setSearchOpen(false)}><Outlet /></main>
  </div>
}
