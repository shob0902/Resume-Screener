from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
SQLALCHEMY_DATABASE_URL = "sqlite:///./resumes.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
class Resume(Base):
    __tablename__ = "resumes"    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    candidate_name = Column(String)
    email = Column(String)
    phone = Column(String)
    skills = Column(Text)          
    experience = Column(Text)      
    education = Column(Text)  
    raw_text = Column(Text)
    match_score = Column(Float)
    skills_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    justification = Column(Text)
    job_description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Database session dependency"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
