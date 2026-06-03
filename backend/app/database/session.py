# =====================================================================
# Database Session Generator - Plum OPD Adjudication
# =====================================================================

from typing import Generator
from .database import SessionLocal

def get_db() -> Generator:
    """
    Database dependency yield provider.
    Yields active database sessions to API routes and closes them after request lifecycles.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
