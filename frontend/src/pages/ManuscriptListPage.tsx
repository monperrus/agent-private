import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../api'
import { ManuscriptListItem } from '../types'
import StatusBadge from '../components/StatusBadge'
import { useAuth } from '../context/AuthContext'
import { formatDistanceToNow } from 'date-fns'
import { PlusCircle } from 'lucide-react'

export default function ManuscriptListPage() {
  const { user } = useAuth()
  const { data: manuscripts, isLoading } = useQuery({
    queryKey: ['manuscripts'],
    queryFn: () => api.get<ManuscriptListItem[]>('/manuscripts').then(r => r.data),
  })

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Manuscripts</h1>
        {user?.role === 'author' && (
          <Link
            to="/manuscripts/submit"
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <PlusCircle className="h-4 w-4" />
            Submit New
          </Link>
        )}
      </div>

      <div className="bg-white rounded-xl border overflow-hidden">
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Manuscript</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Number</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Author</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Submitted</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Editor</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading && (
              <tr><td colSpan={6} className="text-center p-8 text-gray-500">Loading...</td></tr>
            )}
            {manuscripts?.length === 0 && (
              <tr><td colSpan={6} className="text-center p-8 text-gray-500">No manuscripts found</td></tr>
            )}
            {manuscripts?.map(m => (
              <tr key={m.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <Link to={`/manuscripts/${m.id}`} className="font-medium text-primary-600 hover:underline line-clamp-1 max-w-xs block">
                    {m.title}
                  </Link>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">{m.submission_number}</td>
                <td className="px-4 py-3"><StatusBadge status={m.status} /></td>
                <td className="px-4 py-3 text-sm text-gray-600">{m.submitter.full_name}</td>
                <td className="px-4 py-3 text-sm text-gray-500">{formatDistanceToNow(new Date(m.submitted_at), { addSuffix: true })}</td>
                <td className="px-4 py-3 text-sm text-gray-600">{m.handling_editor?.full_name ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
