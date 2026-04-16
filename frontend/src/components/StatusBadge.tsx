import { ManuscriptStatus } from '../types'

const statusConfig: Record<ManuscriptStatus, { label: string; color: string }> = {
  submitted: { label: 'Submitted', color: 'bg-blue-100 text-blue-800' },
  with_editor: { label: 'With Editor', color: 'bg-purple-100 text-purple-800' },
  under_review: { label: 'Under Review', color: 'bg-yellow-100 text-yellow-800' },
  revisions_requested: { label: 'Revisions Requested', color: 'bg-orange-100 text-orange-800' },
  resubmitted: { label: 'Resubmitted', color: 'bg-blue-100 text-blue-800' },
  accepted: { label: 'Accepted', color: 'bg-green-100 text-green-800' },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-800' },
  withdrawn: { label: 'Withdrawn', color: 'bg-gray-100 text-gray-800' },
  published: { label: 'Published', color: 'bg-green-200 text-green-900' },
}

export default function StatusBadge({ status }: { status: ManuscriptStatus }) {
  const config = statusConfig[status] ?? { label: status, color: 'bg-gray-100 text-gray-800' }
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
      {config.label}
    </span>
  )
}
