import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# If Render provides a DATABASE_URL, use PostgreSQL; otherwise default to local SQLite
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # SQLAlchemy requires URLs starting with "postgresql://", but some cloud
    # providers supply "postgres://". This replaces it if necessary.
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    
    engine = create_engine(DATABASE_URL)
else:
    # Local SQLite fallback for developing on your ThinkPad
    SQLALCHEMY_DATABASE_URL = "sqlite:///./budget.db"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()