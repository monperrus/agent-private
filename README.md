# Academic Journal Management System

A modern, self-hosted web application for managing academic journal submissions and peer review workflows — designed to be better than Editorial Manager and ManuscriptCentral.

## Features

### For Authors
- Submit manuscripts with PDF/DOCX file upload
- Add co-authors with affiliation details
- Track submission status in real-time
- Receive notifications at every step
- Withdraw submissions when needed

### For Reviewers
- Receive and respond to review invitations (accept/decline)
- Submit structured reviews with scores and recommendations
- Track review history and deadlines

### For Editors
- View and manage assigned manuscripts
- Invite reviewers from the reviewer pool
- Make editorial decisions (accept / minor revision / major revision / reject)
- Access all submitted reviews

### For Editor-in-Chief / Admin
- Assign manuscripts to handling editors
- Manage all users (assign roles, activate/deactivate)
- Full visibility across all submissions

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Auth | JWT (python-jose) + bcrypt |
| Frontend | React 18, TypeScript, Vite, TailwindCSS |
| HTTP client | Axios + TanStack Query |
| Deployment | Docker + Docker Compose |

## Manuscript Workflow

```
submitted → with_editor → under_review → revisions_requested → resubmitted
                                       ↘ accepted
                                       ↘ rejected
```

## Quick Start

### Prerequisites
- Docker and Docker Compose installed

### 1. Clone and configure

```bash
git clone <repo-url>
cd agent-private
```

### 2. Start services

```bash
docker compose up -d
```

### 3. Create admin user

```bash
docker compose exec backend python seed.py
# Default: admin@journal.org / AdminPassword123!
```

### 4. Open the application

Navigate to [http://localhost](http://localhost)

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://journal:journal@db:5432/journal` | PostgreSQL connection string |
| `SECRET_KEY` | (must set in production) | JWT signing key — use a long random string |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `10080` | Token TTL (7 days) |
| `UPLOAD_DIR` | `/uploads` | Directory for uploaded manuscript files |
| `FRONTEND_URL` | `http://localhost` | CORS allowed origin |

## API Documentation

Once running, the interactive API docs are available at:
- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)

## User Roles

| Role | Description |
|------|-------------|
| `author` | Can submit and track manuscripts |
| `reviewer` | Can be invited to review manuscripts |
| `editor` | Handles assigned manuscripts, invites reviewers, makes decisions |
| `editor_in_chief` | Assigns editors, full system access |
| `admin` | Full access including user management |

## Development

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Security Notes

- Change the `SECRET_KEY` before deploying to production
- Use HTTPS in production (add a reverse proxy like Nginx or Traefik)
- Regularly backup the PostgreSQL volume
