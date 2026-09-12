from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Define the location of the SQLite database file on your machine
DATABASE_URL = "sqlite:///./budget.db"

# Create the database engine
# connect_args={"check_same_thread": False} is required only for SQLite in FastAPI
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Each instance of SessionLocal will be a working session with the database
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class that our data models will inherit from
Base = declarative_base()

# Helper function to open and automatically close database sessions safely
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()