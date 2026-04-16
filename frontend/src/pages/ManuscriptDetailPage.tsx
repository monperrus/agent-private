import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import api from '../api'
import { Manuscript, Review, Decision, User, DecisionType } from '../types'
import { useAuth } from '../context/AuthContext'
import StatusBadge from '../components/StatusBadge'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { useState } from 'react'
import { useForm } from 'react-hook-form'

export default function ManuscriptDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()
  const qc = useQueryClient()

  const { data: manuscript, isLoading } = useQuery({
    queryKey: ['manuscript', id],
    queryFn: () => api.get<Manuscript>(`/manuscripts/${id}`).then(r => r.data),
  })

  const { data: reviews } = useQuery({
    queryKey: ['reviews', id],
    queryFn: () => api.get<Review[]>(`/reviews/manuscript/${id}`).then(r => r.data),
    enabled: ['editor', 'editor_in_chief', 'admin'].includes(user?.role ?? ''),
  })

  const { data: decisions } = useQuery({
    queryKey: ['decisions', id],
    queryFn: () => api.get<Decision[]>(`/decisions/manuscript/${id}`).then(r => r.data),
  })

  const { data: reviewers } = useQuery({
    queryKey: ['reviewers'],
    queryFn: () => api.get<User[]>('/users/reviewers').then(r => r.data),
    enabled: ['editor', 'editor_in_chief', 'admin'].includes(user?.role ?? ''),
  })

  const { data: editors } = useQuery({
    queryKey: ['editors'],
    queryFn: () => api.get<User[]>('/users/editors').then(r => r.data),
    enabled: ['editor_in_chief', 'admin'].includes(user?.role ?? ''),
  })

  if (isLoading) return <div className="p-8 text-center text-gray-500">Loading...</div>
  if (!manuscript) return <div className="p-8 text-center text-gray-500">Manuscript not found</div>

  const isEditor = ['editor', 'editor_in_chief', 'admin'].includes(user?.role ?? '')
  const isEditorInChief = ['editor_in_chief', 'admin'].includes(user?.role ?? '')

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl border p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <p className="text-sm text-gray-500">{manuscript.submission_number} · Version {manuscript.version}</p>
            <h1 className="text-2xl font-bold text-gray-900 mt-1">{manuscript.title}</h1>
          </div>
          <StatusBadge status={manuscript.status} />
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Submitter:</span>
            <span className="ml-2 text-gray-900">{manuscript.submitter.full_name}</span>
          </div>
          <div>
            <span className="text-gray-500">Submitted:</span>
            <span className="ml-2 text-gray-900">{format(new Date(manuscript.submitted_at), 'MMM d, yyyy')}</span>
          </div>
          <div>
            <span className="text-gray-500">Handling Editor:</span>
            <span className="ml-2 text-gray-900">{manuscript.handling_editor?.full_name ?? 'Not assigned'}</span>
          </div>
          {manuscript.keywords && (
            <div>
              <span className="text-gray-500">Keywords:</span>
              <span className="ml-2 text-gray-900">{manuscript.keywords}</span>
            </div>
          )}
        </div>
      </div>

      {/* Abstract */}
      <div className="bg-white rounded-xl border p-6">
        <h2 className="font-semibold mb-3">Abstract</h2>
        <p className="text-gray-700 leading-relaxed">{manuscript.abstract}</p>
      </div>

      {/* Authors */}
      <div className="bg-white rounded-xl border p-6">
        <h2 className="font-semibold mb-3">Authors</h2>
        <div className="space-y-2">
          {manuscript.authors.map(a => (
            <div key={a.id} className="flex items-center gap-3 text-sm">
              <span className="font-medium">{a.full_name}</span>
              {a.institution && <span className="text-gray-500">({a.institution})</span>}
              {a.is_corresponding && <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">Corresponding</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Editor Actions */}
      {isEditorInChief && !manuscript.handling_editor && editors && (
        <AssignEditorPanel manuscriptId={id!} editors={editors} onSuccess={() => qc.invalidateQueries({ queryKey: ['manuscript', id] })} />
      )}

      {isEditor && reviewers && (
        <InviteReviewerPanel manuscriptId={id!} reviewers={reviewers} onSuccess={() => qc.invalidateQueries({ queryKey: ['reviews', id] })} />
      )}

      {/* Reviews (visible to editors) */}
      {isEditor && reviews && reviews.length > 0 && (
        <div className="bg-white rounded-xl border p-6">
          <h2 className="font-semibold mb-4">Reviews ({reviews.length})</h2>
          <div className="space-y-4">
            {reviews.map(r => (
              <ReviewCard key={r.id} review={r} />
            ))}
          </div>
        </div>
      )}

      {/* Make Decision */}
      {isEditor && (
        <MakeDecisionPanel manuscriptId={id!} onSuccess={() => {
          qc.invalidateQueries({ queryKey: ['manuscript', id] })
          qc.invalidateQueries({ queryKey: ['decisions', id] })
        }} />
      )}

      {/* Decisions history */}
      {decisions && decisions.length > 0 && (
        <div className="bg-white rounded-xl border p-6">
          <h2 className="font-semibold mb-4">Decision History</h2>
          <div className="space-y-4">
            {decisions.map(d => (
              <div key={d.id} className="border rounded-lg p-4">
                <div className="flex justify-between items-start mb-2">
                  <span className={`px-2 py-1 rounded text-sm font-medium ${
                    d.decision === 'accept' ? 'bg-green-100 text-green-800' :
                    d.decision === 'reject' ? 'bg-red-100 text-red-800' :
                    'bg-yellow-100 text-yellow-800'
                  }`}>
                    {d.decision.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
                  </span>
                  <span className="text-xs text-gray-500">{format(new Date(d.created_at), 'MMM d, yyyy')} by {d.editor.full_name}</span>
                </div>
                {d.comments_to_author && (
                  <div>
                    <p className="text-xs text-gray-500 mb-1">Comments to Author:</p>
                    <p className="text-sm text-gray-700 whitespace-pre-wrap">{d.comments_to_author}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Withdraw (author only) */}
      {user?.role === 'author' && manuscript.submitter.id === user.id &&
       !['accepted', 'published', 'withdrawn', 'rejected'].includes(manuscript.status) && (
        <WithdrawButton manuscriptId={id!} />
      )}
    </div>
  )
}

function AssignEditorPanel({ manuscriptId, editors, onSuccess }: { manuscriptId: string; editors: User[]; onSuccess: () => void }) {
  const [editorId, setEditorId] = useState('')

  const mutation = useMutation({
    mutationFn: () => api.post(`/manuscripts/${manuscriptId}/assign-editor`, { editor_id: editorId }),
    onSuccess: () => { toast.success('Editor assigned'); onSuccess() },
    onError: (e: any) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  return (
    <div className="bg-white rounded-xl border p-6">
      <h2 className="font-semibold mb-3">Assign Handling Editor</h2>
      <div className="flex gap-3">
        <select value={editorId} onChange={e => setEditorId(e.target.value)} className="flex-1 px-3 py-2 border rounded-lg text-sm">
          <option value="">Select editor...</option>
          {editors.map(e => <option key={e.id} value={e.id}>{e.full_name} ({e.role})</option>)}
        </select>
        <button
          onClick={() => mutation.mutate()}
          disabled={!editorId || mutation.isPending}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm"
        >
          Assign
        </button>
      </div>
    </div>
  )
}

function InviteReviewerPanel({ manuscriptId, reviewers, onSuccess }: { manuscriptId: string; reviewers: User[]; onSuccess: () => void }) {
  const [reviewerId, setReviewerId] = useState('')

  const mutation = useMutation({
    mutationFn: () => api.post(`/reviews/invite?manuscript_id=${manuscriptId}`, { reviewer_id: reviewerId }),
    onSuccess: () => { toast.success('Reviewer invited'); onSuccess(); setReviewerId('') },
    onError: (e: any) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  return (
    <div className="bg-white rounded-xl border p-6">
      <h2 className="font-semibold mb-3">Invite Reviewer</h2>
      <div className="flex gap-3">
        <select value={reviewerId} onChange={e => setReviewerId(e.target.value)} className="flex-1 px-3 py-2 border rounded-lg text-sm">
          <option value="">Select reviewer...</option>
          {reviewers.map(r => <option key={r.id} value={r.id}>{r.full_name} ({r.institution ?? 'No institution'})</option>)}
        </select>
        <button
          onClick={() => mutation.mutate()}
          disabled={!reviewerId || mutation.isPending}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm"
        >
          Invite
        </button>
      </div>
    </div>
  )
}

function ReviewCard({ review }: { review: Review }) {
  return (
    <div className="border border-gray-200 rounded-lg p-4">
      <div className="flex justify-between items-start mb-3">
        <div>
          <span className="font-medium text-sm">{review.reviewer.full_name}</span>
          <span className={`ml-2 text-xs px-2 py-0.5 rounded ${
            review.status === 'submitted' ? 'bg-green-100 text-green-700' :
            review.status === 'accepted' ? 'bg-blue-100 text-blue-700' :
            review.status === 'declined' ? 'bg-red-100 text-red-700' :
            'bg-gray-100 text-gray-700'
          }`}>{review.status}</span>
        </div>
        {review.recommendation && (
          <span className={`text-xs px-2 py-1 rounded font-medium ${
            review.recommendation === 'accept' ? 'bg-green-100 text-green-800' :
            review.recommendation === 'reject' ? 'bg-red-100 text-red-800' :
            'bg-yellow-100 text-yellow-800'
          }`}>
            {review.recommendation.replace('_', ' ')}
          </span>
        )}
      </div>
      {review.status === 'submitted' && (
        <div className="space-y-2">
          {review.score_overall && (
            <div className="flex gap-4 text-xs text-gray-600">
              <span>Overall: {review.score_overall}/10</span>
              {review.score_originality && <span>Originality: {review.score_originality}/10</span>}
              {review.score_methodology && <span>Methodology: {review.score_methodology}/10</span>}
              {review.score_clarity && <span>Clarity: {review.score_clarity}/10</span>}
            </div>
          )}
          {review.comments_to_author && (
            <div>
              <p className="text-xs text-gray-500 font-medium">Comments to Author:</p>
              <p className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{review.comments_to_author}</p>
            </div>
          )}
          {review.comments_to_editor && (
            <div>
              <p className="text-xs text-gray-500 font-medium">Comments to Editor (confidential):</p>
              <p className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{review.comments_to_editor}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function MakeDecisionPanel({ manuscriptId, onSuccess }: { manuscriptId: string; onSuccess: () => void }) {
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<{ decision: DecisionType; comments_to_author: string; comments_to_editor: string }>()

  const onSubmit = async (data: any) => {
    try {
      await api.post(`/decisions/manuscript/${manuscriptId}`, data)
      toast.success('Decision recorded')
      reset()
      onSuccess()
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed')
    }
  }

  return (
    <div className="bg-white rounded-xl border p-6">
      <h2 className="font-semibold mb-4">Make Editorial Decision</h2>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Decision *</label>
          <select {...register('decision', { required: true })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
            <option value="">Select decision...</option>
            <option value="accept">Accept</option>
            <option value="minor_revision">Minor Revision</option>
            <option value="major_revision">Major Revision</option>
            <option value="reject">Reject</option>
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Comments to Author *</label>
          <textarea {...register('comments_to_author', { required: true })} rows={4} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Comments to Editor (confidential)</label>
          <textarea {...register('comments_to_editor')} rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" />
        </div>
        <button type="submit" disabled={isSubmitting} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm">
          Submit Decision
        </button>
      </form>
    </div>
  )
}

function WithdrawButton({ manuscriptId }: { manuscriptId: string }) {
  const navigate = useNavigate()
  const mutation = useMutation({
    mutationFn: () => api.post(`/manuscripts/${manuscriptId}/withdraw`),
    onSuccess: () => { toast.success('Manuscript withdrawn'); navigate('/manuscripts') },
    onError: (e: any) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  return (
    <div className="bg-white rounded-xl border p-6">
      <h2 className="font-semibold mb-2 text-red-700">Withdraw Manuscript</h2>
      <p className="text-sm text-gray-600 mb-4">Once withdrawn, you cannot undo this action.</p>
      <button
        onClick={() => { if (confirm('Are you sure you want to withdraw this manuscript?')) mutation.mutate() }}
        disabled={mutation.isPending}
        className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 text-sm"
      >
        Withdraw
      </button>
    </div>
  )
}
