import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../api'
import { useAuth } from '../context/AuthContext'
import { DashboardStats, ManuscriptListItem } from '../types'
import StatusBadge from '../components/StatusBadge'
import { FileText, Clock, CheckCircle, XCircle, BookOpen, PlusCircle } from 'lucide-react'
import { formatDistanceToNow } from 'date-fns'

export default function DashboardPage() {
  const { user } = useAuth()

  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: () => api.get<DashboardStats>('/stats').then(r => r.data),
  })

  const { data: manuscripts } = useQuery({
    queryKey: ['manuscripts', 'recent'],
    queryFn: () => api.get<ManuscriptListItem[]>('/manuscripts').then(r => r.data.slice(0, 5)),
  })

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Welcome back, {user?.full_name}</p>
        </div>
        {user?.role === 'author' && (
          <Link
            to="/manuscripts/submit"
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <PlusCircle className="h-4 w-4" />
            Submit Manuscript
          </Link>
        )}
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard icon={<BookOpen className="h-6 w-6 text-primary-600" />} label="Total" value={stats?.total_manuscripts ?? 0} color="bg-primary-50" />
        <StatCard icon={<Clock className="h-6 w-6 text-blue-600" />} label="Submitted" value={stats?.pending_review ?? 0} color="bg-blue-50" />
        <StatCard icon={<FileText className="h-6 w-6 text-yellow-600" />} label="Under Review" value={stats?.under_review ?? 0} color="bg-yellow-50" />
        <StatCard icon={<CheckCircle className="h-6 w-6 text-green-600" />} label="Accepted" value={stats?.accepted ?? 0} color="bg-green-50" />
        <StatCard icon={<XCircle className="h-6 w-6 text-red-600" />} label="Rejected" value={stats?.rejected ?? 0} color="bg-red-50" />
      </div>

      {/* Recent manuscripts */}
      <div className="bg-white rounded-xl border">
        <div className="p-4 border-b flex justify-between items-center">
          <h2 className="font-semibold text-gray-900">Recent Manuscripts</h2>
          <Link to="/manuscripts" className="text-sm text-primary-600 hover:underline">View all</Link>
        </div>
        <div className="divide-y">
          {manuscripts?.length === 0 && (
            <p className="p-6 text-center text-gray-500">No manuscripts yet</p>
          )}
          {manuscripts?.map(m => (
            <Link key={m.id} to={`/manuscripts/${m.id}`} className="flex items-center justify-between p-4 hover:bg-gray-50">
              <div>
                <p className="font-medium text-gray-900 truncate max-w-lg">{m.title}</p>
                <p className="text-sm text-gray-500">{m.submission_number} · {formatDistanceToNow(new Date(m.submitted_at), { addSuffix: true })}</p>
              </div>
              <StatusBadge status={m.status} />
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: string }) {
  return (
    <div className={`${color} rounded-xl p-4 flex items-center gap-3`}>
      {icon}
      <div>
        <p className="text-2xl font-bold">{value}</p>
        <p className="text-sm text-gray-600">{label}</p>
      </div>
    </div>
  )
}
