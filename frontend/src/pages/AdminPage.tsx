import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api'
import { User, UserRole } from '../types'
import toast from 'react-hot-toast'
import { format } from 'date-fns'

const ROLES: UserRole[] = ['admin', 'editor_in_chief', 'editor', 'reviewer', 'author']

export default function AdminPage() {
  const qc = useQueryClient()
  const { data: users, isLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => api.get<User[]>('/users').then(r => r.data),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, role, is_active }: { id: string; role?: UserRole; is_active?: boolean }) =>
      api.put(`/users/${id}`, { role, is_active }),
    onSuccess: () => { toast.success('User updated'); qc.invalidateQueries({ queryKey: ['admin-users'] }) },
    onError: (e: any) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>

      <div className="bg-white rounded-xl border overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="font-semibold">User Management</h2>
        </div>
        <table className="w-full">
          <thead className="bg-gray-50 border-b">
            <tr>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">User</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Institution</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Role</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Status</th>
              <th className="text-left px-4 py-3 text-sm font-medium text-gray-600">Joined</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {isLoading && <tr><td colSpan={5} className="text-center p-8 text-gray-500">Loading...</td></tr>}
            {users?.map(u => (
              <tr key={u.id} className="hover:bg-gray-50">
                <td className="px-4 py-3">
                  <p className="font-medium text-sm">{u.full_name}</p>
                  <p className="text-xs text-gray-500">{u.email}</p>
                </td>
                <td className="px-4 py-3 text-sm text-gray-600">{u.institution ?? '—'}</td>
                <td className="px-4 py-3">
                  <select
                    value={u.role}
                    onChange={e => updateMutation.mutate({ id: u.id, role: e.target.value as UserRole })}
                    className="text-sm px-2 py-1 border rounded"
                  >
                    {ROLES.map(r => <option key={r} value={r}>{r.replace('_', ' ')}</option>)}
                  </select>
                </td>
                <td className="px-4 py-3">
                  <button
                    onClick={() => updateMutation.mutate({ id: u.id, is_active: !u.is_active })}
                    className={`text-xs px-2 py-1 rounded font-medium ${u.is_active ? 'bg-green-100 text-green-700 hover:bg-green-200' : 'bg-red-100 text-red-700 hover:bg-red-200'}`}
                  >
                    {u.is_active ? 'Active' : 'Disabled'}
                  </button>
                </td>
                <td className="px-4 py-3 text-sm text-gray-500">{format(new Date(u.created_at), 'MMM d, yyyy')}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
