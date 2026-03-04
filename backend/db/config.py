"""
backend/db/config.py — re-exports database primitives from backend.database.
"""
from backend.database import Base, SessionLocal, engine, init_db

__all__ = ["Base", "SessionLocal", "engine", "init_db"]
