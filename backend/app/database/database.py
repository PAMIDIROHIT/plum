# =====================================================================
# Database Core Configuration - Plum OPD Adjudication
# =====================================================================

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# Load database configuration from environment
load_dotenv()

# Default local SQLite database file path
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./claims.db")

# check_same_thread=False allows multi-threaded concurrency for sqlite
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Local database session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for SQL models mapping
Base = declarative_base()
