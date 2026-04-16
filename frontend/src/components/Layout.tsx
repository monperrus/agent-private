import { Outlet, Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useQuery } from '@tanstack/react-query'
import api from '../api'
import { Notification } from '../types'
import { Bell, BookOpen, FileText, LogOut, Users, ClipboardList } from 'lucide-react'
import { useState } from 'react'

export default function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [showNotifs, setShowNotifs] = useState(false)

  const { data: notifications } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => api.get<Notification[]>('/notifications').then(r => r.data),
    refetchInterval: 30000,
  })

  const unread = notifications?.filter(n => !n.read).length ?? 0

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="min-h-screen flex">
      {/* Sidebar */}
      <aside className="w-64 bg-primary-800 text-white flex flex-col">
        <div className="p-6 border-b border-primary-700">
          <div className="flex items-center gap-2">
            <BookOpen className="h-6 w-6" />
            <span className="font-bold text-lg">JournalMS</span>
          </div>
          <p className="text-primary-200 text-sm mt-1 truncate">{user?.full_name}</p>
          <span className="text-xs bg-primary-600 px-2 py-0.5 rounded-full capitalize">
            {user?.role?.replace('_', ' ')}
          </span>
        </div>

        <nav className="flex-1 p-4 space-y-1">
          <NavLink to="/" icon={<FileText className="h-4 w-4" />}>Dashboard</NavLink>
          <NavLink to="/manuscripts" icon={<ClipboardList className="h-4 w-4" />}>Manuscripts</NavLink>
          {user?.role === 'author' && (
            <NavLink to="/manuscripts/submit" icon={<FileText className="h-4 w-4" />}>Submit Manuscript</NavLink>
          )}
          {(user?.role === 'reviewer') && (
            <NavLink to="/reviews" icon={<ClipboardList className="h-4 w-4" />}>My Reviews</NavLink>
          )}
          {(user?.role === 'admin' || user?.role === 'editor_in_chief') && (
            <NavLink to="/admin" icon={<Users className="h-4 w-4" />}>Admin</NavLink>
          )}
        </nav>

        <div className="p-4 border-t border-primary-700">
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 text-primary-200 hover:text-white w-full text-sm"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col">
        {/* Top bar */}
        <header className="bg-white border-b px-6 py-3 flex items-center justify-between">
          <h1 className="text-lg font-semibold text-gray-700">Journal Management System</h1>
          <div className="relative">
            <button
              onClick={() => setShowNotifs(!showNotifs)}
              className="relative p-2 text-gray-500 hover:text-gray-700"
            >
              <Bell className="h-5 w-5" />
              {unread > 0 && (
                <span className="absolute top-1 right-1 bg-red-500 text-white text-xs rounded-full h-4 w-4 flex items-center justify-center">
                  {unread}
                </span>
              )}
            </button>

            {showNotifs && (
              <div className="absolute right-0 top-10 w-96 bg-white rounded-lg shadow-xl border z-50 max-h-96 overflow-y-auto">
                <div className="p-3 border-b flex justify-between">
                  <span className="font-semibold">Notifications</span>
                  <button
                    onClick={() => {
                      api.post('/notifications/read-all')
                      setShowNotifs(false)
                    }}
                    className="text-xs text-primary-600 hover:underline"
                  >
                    Mark all read
                  </button>
                </div>
                {notifications?.length === 0 && (
                  <p className="p-4 text-sm text-gray-500">No notifications</p>
                )}
                {notifications?.map(n => (
                  <div key={n.id} className={`p-3 border-b text-sm ${n.read ? 'opacity-60' : 'bg-blue-50'}`}>
                    <p className="font-medium">{n.title}</p>
                    <p className="text-gray-600 text-xs mt-1">{n.message}</p>
                    <p className="text-gray-400 text-xs mt-1">{new Date(n.created_at).toLocaleString()}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </header>

        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

function NavLink({ to, icon, children }: { to: string; icon: React.ReactNode; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-primary-100 hover:bg-primary-700 hover:text-white text-sm transition-colors"
    >
      {icon}
      {children}
    </Link>
  )
}
