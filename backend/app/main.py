import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import settings
from .database import engine, Base
from .routers import auth, users, manuscripts, reviews, decisions, notifications, stats


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="Academic Journal Management System",
    description="A complete system for managing academic journal submissions and peer review",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(manuscripts.router)
app.include_router(reviews.router)
app.include_router(decisions.router)
app.include_router(notifications.router)
app.include_router(stats.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
