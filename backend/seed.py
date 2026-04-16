#!/usr/bin/env python3
"""
Seed script: creates the first admin user.
Run after the backend container is up:
  docker compose exec backend python seed.py
"""
import asyncio
import os
import sys

# Add the app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.database import AsyncSessionLocal, engine, Base
from app.models import User, UserRole
from app.auth import get_password_hash
from sqlalchemy import select


async def create_admin():
    email = os.getenv("ADMIN_EMAIL", "admin@journal.org")
    password = os.getenv("ADMIN_PASSWORD", "AdminPassword123!")
    full_name = os.getenv("ADMIN_NAME", "Journal Administrator")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"Admin user '{email}' already exists.")
            return

        admin = User(
            email=email,
            hashed_password=get_password_hash(password),
            full_name=full_name,
            role=UserRole.admin,
            is_active=True,
        )
        session.add(admin)
        await session.commit()
        print(f"Created admin user: {email} / {password}")
        print("IMPORTANT: Change the password after first login!")


if __name__ == "__main__":
    asyncio.run(create_admin())
