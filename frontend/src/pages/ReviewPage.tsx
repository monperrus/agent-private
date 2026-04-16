import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import api from '../api'
import { Review } from '../types'
import toast from 'react-hot-toast'
import { format } from 'date-fns'
import { useState } from 'react'
import { useForm } from 'react-hook-form'

export default function ReviewPage() {
  const qc = useQueryClient()
  const { data: reviews, isLoading } = useQuery({
    queryKey: ['my-reviews'],
    queryFn: () => api.get<Review[]>('/reviews/my').then(r => r.data),
  })

  const acceptMutation = useMutation({
    mutationFn: (id: string) => api.post(`/reviews/${id}/accept`),
    onSuccess: () => { toast.success('Review accepted'); qc.invalidateQueries({ queryKey: ['my-reviews'] }) },
    onError: (e: any) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  const declineMutation = useMutation({
    mutationFn: (id: string) => api.post(`/reviews/${id}/decline`),
    onSuccess: () => { toast.success('Review declined'); qc.invalidateQueries({ queryKey: ['my-reviews'] }) },
    onError: (e: any) => toast.error(e.response?.data?.detail ?? 'Failed'),
  })

  const [submittingReviewId, setSubmittingReviewId] = useState<string | null>(null)

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-gray-900">My Reviews</h1>

      {isLoading && <p className="text-center text-gray-500">Loading...</p>}
      {reviews?.length === 0 && <p className="text-center text-gray-500 py-12">No reviews assigned</p>}

      <div className="space-y-4">
        {reviews?.map(review => (
          <div key={review.id} className="bg-white rounded-xl border p-6">
            <div className="flex justify-between items-start mb-3">
              <div>
                <Link to={`/manuscripts/${review.manuscript_id}`} className="font-medium text-primary-600 hover:underline">
                  View Manuscript
                </Link>
                <p className="text-xs text-gray-500 mt-1">Invited {format(new Date(review.invited_at), 'MMM d, yyyy')}</p>
                {review.due_date && <p className="text-xs text-orange-600">Due: {format(new Date(review.due_date), 'MMM d, yyyy')}</p>}
              </div>
              <span className={`text-xs px-2 py-1 rounded font-medium ${
                review.status === 'submitted' ? 'bg-green-100 text-green-700' :
                review.status === 'accepted' ? 'bg-blue-100 text-blue-700' :
                review.status === 'declined' ? 'bg-red-100 text-red-700' :
                'bg-yellow-100 text-yellow-700'
              }`}>{review.status}</span>
            </div>

            {review.status === 'invited' && (
              <div className="flex gap-3">
                <button onClick={() => acceptMutation.mutate(review.id)} className="px-3 py-1.5 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700">
                  Accept
                </button>
                <button onClick={() => declineMutation.mutate(review.id)} className="px-3 py-1.5 bg-red-600 text-white text-sm rounded-lg hover:bg-red-700">
                  Decline
                </button>
              </div>
            )}

            {review.status === 'accepted' && submittingReviewId !== review.id && (
              <button onClick={() => setSubmittingReviewId(review.id)} className="px-3 py-1.5 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700">
                Submit Review
              </button>
            )}

            {review.status === 'accepted' && submittingReviewId === review.id && (
              <SubmitReviewForm reviewId={review.id} onSubmitted={() => {
                setSubmittingReviewId(null)
                qc.invalidateQueries({ queryKey: ['my-reviews'] })
              }} />
            )}

            {review.status === 'submitted' && review.recommendation && (
              <div className="mt-2 text-sm text-gray-600">
                <span className="font-medium">Your recommendation: </span>
                <span className={`px-2 py-0.5 rounded text-xs ${
                  review.recommendation === 'accept' ? 'bg-green-100 text-green-700' :
                  review.recommendation === 'reject' ? 'bg-red-100 text-red-700' :
                  'bg-yellow-100 text-yellow-700'
                }`}>{review.recommendation.replace('_', ' ')}</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

function SubmitReviewForm({ reviewId, onSubmitted }: { reviewId: string; onSubmitted: () => void }) {
  const { register, handleSubmit, formState: { isSubmitting } } = useForm()

  const onSubmit = async (data: any) => {
    try {
      await api.post(`/reviews/${reviewId}/submit`, data)
      toast.success('Review submitted successfully!')
      onSubmitted()
    } catch (e: any) {
      toast.error(e.response?.data?.detail ?? 'Failed to submit review')
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="mt-4 space-y-4 border-t pt-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Recommendation *</label>
        <select {...register('recommendation', { required: true })} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm">
          <option value="">Select...</option>
          <option value="accept">Accept</option>
          <option value="minor_revision">Minor Revision</option>
          <option value="major_revision">Major Revision</option>
          <option value="reject">Reject</option>
        </select>
      </div>

      <div className="grid grid-cols-4 gap-3">
        {(['score_overall', 'score_originality', 'score_methodology', 'score_clarity'] as const).map(field => (
          <div key={field}>
            <label className="block text-xs text-gray-600 mb-1">{field.replace('score_', '').replace('_', ' ')} (1-10)</label>
            <input {...register(field, { valueAsNumber: true, min: 1, max: 10 })} type="number" min="1" max="10" className="w-full px-2 py-1.5 border rounded text-sm" />
          </div>
        ))}
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Comments to Author *</label>
        <textarea {...register('comments_to_author', { required: true })} rows={5} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" placeholder="Detailed feedback for the authors..." />
      </div>
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Confidential Comments to Editor</label>
        <textarea {...register('comments_to_editor')} rows={3} className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm" placeholder="Private notes for the editor..." />
      </div>

      <div className="flex gap-3">
        <button type="submit" disabled={isSubmitting} className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 text-sm">
          {isSubmitting ? 'Submitting...' : 'Submit Review'}
        </button>
        <button type="button" onClick={() => onSubmitted()} className="px-4 py-2 border rounded-lg text-sm hover:bg-gray-50">
          Cancel
        </button>
      </div>
    </form>
  )
}
