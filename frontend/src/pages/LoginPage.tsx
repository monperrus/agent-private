import { useForm } from 'react-hook-form'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import api from '../api'
import toast from 'react-hot-toast'
import { BookOpen } from 'lucide-react'

interface FormData {
  username: string
  password: string
}

export default function LoginPage() {
  const { register, handleSubmit, formState: { isSubmitting } } = useForm<FormData>()
  const { login } = useAuth()
  const navigate = useNavigate()

  const onSubmit = async (data: FormData) => {
    try {
      const formData = new FormData()
      formData.append('username', data.username)
      formData.append('password', data.password)
      const res = await api.post('/auth/login', formData)
      await login(res.data.access_token)
      navigate('/')
    } catch (err: any) {
      toast.error(err.response?.data?.detail ?? 'Login failed')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-800 to-primary-600 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-xl p-8 w-full max-w-md">
        <div className="flex items-center justify-center gap-2 mb-6">
          <BookOpen className="h-8 w-8 text-primary-600" />
          <h1 className="text-2xl font-bold text-gray-900">JournalMS</h1>
        </div>
        <h2 className="text-xl font-semibold text-gray-700 mb-6 text-center">Sign in to your account</h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              {...register('username', { required: true })}
              type="email"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              {...register('password', { required: true })}
              type="password"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full py-2 px-4 bg-primary-600 hover:bg-primary-700 text-white font-medium rounded-lg transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Signing in...' : 'Sign in'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-600">
          Don't have an account?{' '}
          <Link to="/register" className="text-primary-600 hover:underline font-medium">Register</Link>
        </p>
      </div>
    </div>
  )
}
