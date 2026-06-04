# =====================================================================
# Database Session Generator - Plum OPD Adjudication
# =====================================================================

from typing import Generator
from .database import db

def get_db() -> Generator:
    """
    Database dependency yield provider.
    Yields the active MongoDB database reference to API routes.
    """
    yield db
