import { useForm, useFieldArray } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import api from '../api'
import toast from 'react-hot-toast'
import { useAuth } from '../context/AuthContext'
import { PlusCircle, Trash2 } from 'lucide-react'

interface Author {
  full_name: string
  email: string
  institution?: string
  is_corresponding: boolean
  order: number
}

interface FormData {
  title: string
  abstract: string
  keywords: string
  cover_letter: string
  authors: Author[]
  manuscript_file: FileList
}

export default function SubmitManuscriptPage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { register, handleSubmit, control, formState: { isSubmitting, errors } } = useForm<FormData>({
    defaultValues: {
      authors: [{
        full_name: user?.full_name ?? '',
        email: user?.email ?? '',
        institution: user?.institution ?? '',
        is_corresponding: true,
        order: 0,
      }],
    },
  })

  const { fields, append, remove } = useFieldArray({ control, name: 'authors' })

  const onSubmit = async (data: FormData) => {
    try {
      const manuscriptData = {
        title: data.title,
        abstract: data.abstract,
        keywords: data.keywords,
        cover_letter: data.cover_letter,
        authors: data.authors.map((a, i) => ({ ...a, order: i })),
      }

      const formData = new FormData()
      formData.append('manuscript_data', JSON.stringify(manuscriptData))
      formData.append('manuscript_file', data.manuscript_file[0])

      const res = await api.post('/manuscripts', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      toast.success(`Manuscript submitted! Submission number: ${res.data.submission_number}`)
      navigate(`/manuscripts/${res.data.id}`)
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Submission failed')
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Submit New Manuscript</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        <div className="bg-white rounded-xl border p-6 space-y-4">
          <h2 className="text-lg font-semibold">Manuscript Details</h2>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Title *</label>
            <input
              {...register('title', { required: 'Title is required' })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            {errors.title && <p className="text-red-500 text-xs mt-1">{errors.title.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Abstract *</label>
            <textarea
              {...register('abstract', { required: 'Abstract is required' })}
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            {errors.abstract && <p className="text-red-500 text-xs mt-1">{errors.abstract.message}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Keywords (comma-separated)</label>
            <input
              {...register('keywords')}
              placeholder="machine learning, neural networks, deep learning"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cover Letter</label>
            <textarea
              {...register('cover_letter')}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Manuscript File (PDF) *</label>
            <input
              {...register('manuscript_file', { required: 'Manuscript file is required' })}
              type="file"
              accept=".pdf,.doc,.docx"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
            {errors.manuscript_file && <p className="text-red-500 text-xs mt-1">{errors.manuscript_file.message}</p>}
          </div>
        </div>

        <div className="bg-white rounded-xl border p-6 space-y-4">
          <div className="flex justify-between items-center">
            <h2 className="text-lg font-semibold">Authors</h2>
            <button
              type="button"
              onClick={() => append({ full_name: '', email: '', institution: '', is_corresponding: false, order: fields.length })}
              className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700"
            >
              <PlusCircle className="h-4 w-4" />
              Add Author
            </button>
          </div>

          {fields.map((field, index) => (
            <div key={field.id} className="border border-gray-200 rounded-lg p-4 space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-sm font-medium text-gray-700">Author {index + 1}</span>
                {index > 0 && (
                  <button type="button" onClick={() => remove(index)} className="text-red-500 hover:text-red-700">
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Full Name *</label>
                  <input {...register(`authors.${index}.full_name`, { required: true })} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Email *</label>
                  <input {...register(`authors.${index}.email`, { required: true })} type="email" className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">Institution</label>
                  <input {...register(`authors.${index}.institution`)} className="w-full px-2 py-1.5 border border-gray-300 rounded text-sm" />
                </div>
                <div className="flex items-center gap-2 pt-4">
                  <input {...register(`authors.${index}.is_corresponding`)} type="checkbox" id={`corresponding-${index}`} />
                  <label htmlFor={`corresponding-${index}`} className="text-xs text-gray-600">Corresponding Author</label>
                </div>
              </div>
            </div>
          ))}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full py-3 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
        >
          {isSubmitting ? 'Submitting...' : 'Submit Manuscript'}
        </button>
      </form>
    </div>
  )
}
