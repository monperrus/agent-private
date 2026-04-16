export type UserRole = 'admin' | 'editor_in_chief' | 'editor' | 'reviewer' | 'author'

export type ManuscriptStatus =
  | 'submitted'
  | 'with_editor'
  | 'under_review'
  | 'revisions_requested'
  | 'resubmitted'
  | 'accepted'
  | 'rejected'
  | 'withdrawn'
  | 'published'

export type ReviewStatus = 'invited' | 'accepted' | 'declined' | 'submitted'

export type DecisionType = 'accept' | 'minor_revision' | 'major_revision' | 'reject'

export interface User {
  id: string
  email: string
  full_name: string
  institution?: string
  country?: string
  orcid?: string
  bio?: string
  role: UserRole
  is_active: boolean
  created_at: string
}

export interface ManuscriptAuthor {
  id: string
  full_name: string
  email: string
  institution?: string
  is_corresponding: boolean
  order: number
}

export interface ManuscriptFile {
  id: string
  filename: string
  original_filename: string
  file_type: string
  file_size: number
  uploaded_at: string
}

export interface Manuscript {
  id: string
  title: string
  abstract: string
  keywords?: string
  cover_letter?: string
  status: ManuscriptStatus
  submission_number: string
  version: number
  doi?: string
  submitted_at: string
  updated_at: string
  submitter: User
  handling_editor?: User
  authors: ManuscriptAuthor[]
  files: ManuscriptFile[]
}

export interface ManuscriptListItem {
  id: string
  title: string
  status: ManuscriptStatus
  submission_number: string
  version: number
  submitted_at: string
  updated_at: string
  submitter: User
  handling_editor?: User
}

export interface Review {
  id: string
  manuscript_id: string
  reviewer_id: string
  status: ReviewStatus
  recommendation?: string
  comments_to_author?: string
  comments_to_editor?: string
  score_overall?: number
  score_originality?: number
  score_methodology?: number
  score_clarity?: number
  invited_at: string
  responded_at?: string
  submitted_at?: string
  due_date?: string
  reviewer: User
}

export interface Decision {
  id: string
  manuscript_id: string
  decision: DecisionType
  comments_to_author?: string
  comments_to_editor?: string
  created_at: string
  editor: User
}

export interface Notification {
  id: string
  title: string
  message: string
  type: string
  read: boolean
  manuscript_id?: string
  created_at: string
}

export interface DashboardStats {
  total_manuscripts: number
  pending_review: number
  under_review: number
  accepted: number
  rejected: number
}
