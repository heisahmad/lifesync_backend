from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Database URL - using your SQLite for now
SQLALCHEMY_DATABASE_URL = "sqlite:///./lifesync.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Import all models here to ensure they're registered with SQLAlchemy
from app.models.user import User  # noqa
from app.models.integration import Integration  # noqa

# Create all tables (this should be called after all models are defined)
def create_tables():
    Base.metadata.create_all(bind=engine)