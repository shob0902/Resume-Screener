import os
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import fitz 
from dotenv import load_dotenv
import google.generativeai as genai

DATABASE_URL = "sqlite:///resumes.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    candidate_name = Column(String)
    email = Column(String)
    phone = Column(String)
    skills = Column(String)
    skills_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    overall_score = Column(Float)
    strengths = Column(String)
    gaps = Column(String)
    justification = Column(String)

Base.metadata.create_all(bind=engine)
def extract_text_from_pdf(pdf_path: str) -> str:
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text.strip()
    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
# Example: list models (for test)
def list_gemini_models():
    return [m.name for m in genai.list_models()]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/batch-upload")
async def batch_upload(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    results = []
    for file in files:
        path = f"uploads/{file.filename}"
        with open(path, "wb") as f:
            f.write(await file.read())
        text = extract_text_from_pdf(path)
        resume = Resume(filename=file.filename, candidate_name="", email="", phone="", skills="", skills_score=0, experience_score=0, education_score=0, overall_score=0, strengths="", gaps="", justification="")
        db.add(resume)
        db.commit()
        db.refresh(resume)
        results.append({"filename": file.filename, "length": len(text)})
    return {"uploaded": results}

@app.post("/match")
async def match(job_description: str = Form(...), db: Session = Depends(get_db)):
    import random
    resumes = db.query(Resume).all()
    shortlisted = []
    for r in resumes:
        r.skills_score = random.uniform(5,10)
        r.experience_score = random.uniform(5,10)
        r.education_score = random.uniform(5,10)
        r.overall_score = (r.skills_score + r.experience_score + r.education_score)/3
        db.commit()
        shortlisted.append({
            "filename": r.filename,
            "candidate_name": r.candidate_name,
            "email": r.email,
            "phone": r.phone,
            "skills": r.skills.split(",") if r.skills else [],
            "skills_score": r.skills_score,
            "experience_score": r.experience_score,
            "education_score": r.education_score,
            "overall_score": r.overall_score,
            "strengths": r.strengths.split(",") if r.strengths else [],
            "gaps": r.gaps.split(",") if r.gaps else [],
            "justification": r.justification,
        })
    return {"shortlisted_candidates": shortlisted}

@app.get("/models")
def get_models():
    return {"models": list_gemini_models()}

@app.post("/reset-db")
def reset_db():
    db_path = "resumes.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    Base.metadata.create_all(bind=engine)
    return {"status": "reset"}


def reset_database_script():
    """Run the reset database routine from a script context (prints progress)."""
    db_path = "resumes.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ Deleted old database: {db_path}")

    Base.metadata.create_all(bind=engine)
    print("✓ Created new database with updated schema")
    print("✓ Database reset complete!")
    print("\nNew columns added:")
    print("  - job_match_percentage (Integer)")
    print("  - match_reasoning (Text)")


def list_gemini_models_for_cli():
    """List available Gemini models to stdout (same logic as test_gemini.py).

    Prints models that support generation.
    """
    try:
        models = genai.list_models()
    except Exception as e:
        print("Error listing models:", e)
        return
    for model in models:
        try:
            if hasattr(model, 'supported_generation_methods') and 'generateContent' in model.supported_generation_methods:
                print(model.name)
        except Exception:
            continue


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ('reset-db', 'reset_database', 'reset'):
            reset_database_script()
            sys.exit(0)
        if cmd in ('test-gemini', 'list-models', 'models'):
            list_gemini_models_for_cli()
            sys.exit(0)
    print('No CLI command provided. Start the FastAPI server with: uvicorn app:app --reload')
