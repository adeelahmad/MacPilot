# automation_framework/models/db_session.py
# Revision No: 001
# Goals: Manage database sessions.
# Type of Code Response: Add new code

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
from .base import Base  # Import Base from base.py

DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///./automation.db')

engine = create_engine(DATABASE_URL)
SessionLocal = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))


@contextmanager
def get_db():
    """Provides a transactional scope around a series of operations."""
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Commit changes after successful operations
    except Exception:
        db.rollback()  # Rollback changes on error
        raise
    finally:
        db.close()


Base.metadata.create_all(bind=engine)  # Create tables if they don't exist

# Dependencies: sqlalchemy, os, contextlib
# Required Actions: Ensure database URL is correctly configured.
# CLI Commands: None
# Is the script complete? Yes
# Is the code chunked version? No
# Is the code finished and commit-ready? Yes
# Are there any gaps that should be fixed in the next iteration? No
# Goals for the file in the following code block in case it's incomplete: N/A
