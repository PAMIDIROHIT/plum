from typing import Generator
from .database import SessionLocal

def get_db() -> Generator:
    """
    Database dependency yield provider.
    Yields active database sessions to routers and closes them after requests finish.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
