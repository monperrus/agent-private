import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import DashboardPage from './pages/DashboardPage'
import ManuscriptListPage from './pages/ManuscriptListPage'
import ManuscriptDetailPage from './pages/ManuscriptDetailPage'
import SubmitManuscriptPage from './pages/SubmitManuscriptPage'
import ReviewPage from './pages/ReviewPage'
import AdminPage from './pages/AdminPage'
import Layout from './components/Layout'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center h-screen">Loading...</div>
  if (!user) return <Navigate to="/login" />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route index element={<DashboardPage />} />
        <Route path="manuscripts" element={<ManuscriptListPage />} />
        <Route path="manuscripts/submit" element={<SubmitManuscriptPage />} />
        <Route path="manuscripts/:id" element={<ManuscriptDetailPage />} />
        <Route path="reviews" element={<ReviewPage />} />
        <Route path="admin" element={<AdminPage />} />
      </Route>
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
