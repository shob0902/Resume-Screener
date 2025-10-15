import os
import re
import json
from pathlib import Path
from typing import List, Tuple, Set, Dict

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Float, Text
from sqlalchemy.orm import sessionmaker, Session, declarative_base
import fitz
from dotenv import load_dotenv
import google.generativeai as genai

DATABASE_URL = "sqlite:///resumes.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class Resume(Base):
    __tablename__ = "resumes"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    candidate_name = Column(String)
    email = Column(String)
    phone = Column(String)
    skills = Column(Text)
    skills_score = Column(Float)
    experience_score = Column(Float)
    education_score = Column(Float)
    overall_score = Column(Float)
    strengths = Column(Text)
    gaps = Column(Text)
    justification = Column(Text)
    job_match_percentage = Column(Integer, default=0)
    match_reasoning = Column(Text, default="")

Base.metadata.create_all(bind=engine)

def safe_filename(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]", "_", name)

def parse_pdf_text(file_path: str) -> str:
    try:
        text_chunks = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text_chunks.append(page.get_text(sort=True))
        return "\n".join(text_chunks).strip()
    except Exception as error:
        raise RuntimeError(f"Failed to parse PDF: {error}")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")

def extract_entities(text: str) -> Tuple[str, str, str, List[str]]:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    name = lines[0][:128] if lines else ""
    email_match = EMAIL_RE.search(text) or None
    phone_match = PHONE_RE.search(text) or None
    email = email_match.group(0) if email_match else ""
    phone = phone_match.group(0) if phone_match else ""
    skills_section = []
    skills = []
    for i, ln in enumerate(lines):
        if re.search(r"\bskills?\b[:\-]?\s*$", ln, re.I) or re.search(r"\btechnical skills?\b", ln, re.I):
            for j in range(i + 1, min(i + 10, len(lines))):
                if re.match(r"^[A-Z][A-Za-z0-9 ]{0,40}:$", lines[j]):
                    break
                skills_section.append(lines[j])
            break
    if skills_section:
        blob = " ".join(skills_section)
        parts = re.split(r"[•,\n;]+", blob)
        skills = [p.strip().lower() for p in parts if len(p.strip()) >= 2][:40]
    else:
        toks = tokenize(" ".join(lines[:40]))
        skills = sorted({t for t in toks if re.search(r"[a-z]{2,}[a-z0-9+\-#\.]*", t)})[:30]
    return name, email, phone, skills

STOPWORDS = {
    "the","and","or","for","with","to","of","a","an","in","on","by","as","at","is","are","be","this","that",
    "from","it","its","into","over","under","than","then","via","using","use","used","per","performs",
    "your","you","we","our","their","they","he","she","him","her"
}

def tokenize(text: str) -> List[str]:
    toks = re.findall(r"[A-Za-z0-9+#\-.]+", text.lower())
    return [t for t in toks if t not in STOPWORDS and not t.isdigit()]

def setify(tokens: List[str]) -> Set[str]:
    return set(tokens)

def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0

def estimate_years(text: str) -> float:
    years = 0.0
    for m in re.finditer(r"(\d{1,2})(\s*\+?)\s*(years?|yrs?|yr)", text.lower()):
        try:
            val = float(m.group(1))
            years = max(years, val)
        except:
            continue
    return years

EDU_KEYWORDS = {
    "bsc","b.s.","btech","b.tech","be","b.e.","bs","bachelor","m.sc","ms","m.s.","msc","mtech","m.tech","me","m.e.","master","phd","ph.d","doctorate"
}

def has_requested_education(jd_text: str, resume_text: str) -> Tuple[bool, bool]:
    jd_has = any(k in jd_text.lower() for k in EDU_KEYWORDS)
    res_has = any(k in resume_text.lower() for k in EDU_KEYWORDS)
    return jd_has, res_has

def score_resume_against_jd(jd: str, resume_text: str, resume_skills: List[str]) -> Dict[str, object]:
    jd_tokens = setify(tokenize(jd))
    res_tokens = setify(tokenize(resume_text))
    jd_skill_candidates = [t for t in jd_tokens if re.search(r"[a-z]{2,}[a-z0-9+\-#\.]*", t)]
    jd_skills = set(jd_skill_candidates)
    res_skills = set([s.lower() for s in resume_skills])
    skills_overlap = jaccard(res_skills, jd_skills)
    skills_score = round(10.0 * skills_overlap, 2)
    jd_years = estimate_years(jd)
    res_years = estimate_years(resume_text)
    if jd_years > 0:
        ratio = min(res_years / jd_years, 1.0)
        experience_score = round(10.0 * ratio, 2)
    else:
        experience_score = round(10.0 * jaccard(res_tokens, jd_tokens), 2)
    jd_has_edu, res_has_edu = has_requested_education(jd, resume_text)
    if jd_has_edu and res_has_edu:
        education_score = 9.0
    elif jd_has_edu and not res_has_edu:
        education_score = 5.0
    else:
        education_score = 7.0
    overall_score = round((0.45 * skills_score + 0.4 * experience_score + 0.15 * education_score), 2)
    strengths = sorted((res_skills & jd_skills))[:20]
    gaps = sorted((jd_skills - res_skills))[:20]
    justification = (
        f"Skills overlap: {len(strengths)} matched items; experience years={res_years} "
        f"vs required={jd_years if jd_years else 'n/a'}; education_required={jd_has_edu} "
        f"education_found={res_has_edu}."
    )
    job_match_percentage = int(min(100, round(overall_score * 10)))
    return {
        "skills_score": skills_score,
        "experience_score": experience_score,
        "education_score": education_score,
        "overall_score": overall_score,
        "strengths": strengths,
        "gaps": gaps,
        "justification": justification,
        "job_match_percentage": job_match_percentage,
        "match_reasoning": justification
    }

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def list_gemini_models() -> List[str]:
    try:
        models = genai.list_models()
    except Exception:
        return []
    names = []
    for m in models:
        try:
            if hasattr(m, "supported_generation_methods"):
                if "generateContent" in getattr(m, "supported_generation_methods", []):
                    names.append(m.name)
                    continue
            if hasattr(m, "supported_actions"):
                if "generateContent" in getattr(m, "supported_actions", []):
                    names.append(m.name)
                    continue
            names.append(m.name)
        except Exception:
            continue
    return names

app = FastAPI(title="Smart Resume Screener")

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    results = []
    for file in files:
        if not file.filename:
            raise HTTPException(status_code=400, detail="One file has no filename")
        if (file.content_type or "").lower() not in ("application/pdf", "application/octet-stream"):
            raise HTTPException(status_code=415, detail=f"Unsupported content type for {file.filename} (expected PDF)")
        fname = safe_filename(file.filename)
        path = UPLOAD_DIR / fname
        data = await file.read()
        if not data:
            raise HTTPException(status_code=400, detail=f"Empty file: {fname}")
        with open(path, "wb") as f:
            f.write(data)
        try:
            text = parse_pdf_text(str(path))
        except Exception as e:
            raise HTTPException(status_code=422, detail=str(e))
        name, email, phone, skills = extract_entities(text)
        resume = Resume(
            filename=fname,
            candidate_name=name,
            email=email,
            phone=phone,
            skills=",".join(skills),
            skills_score=0.0,
            experience_score=0.0,
            education_score=0.0,
            overall_score=0.0,
            strengths="",
            gaps="",
            justification="",
            job_match_percentage=0,
            match_reasoning=""
        )
        db.add(resume)
        db.commit()
        db.refresh(resume)
        results.append({"id": resume.id, "filename": fname, "extracted_chars": len(text)})
    return {"uploaded": results}

@app.post("/match")
async def match(job_description: str = Form(...), db: Session = Depends(get_db)):
    if not job_description or not job_description.strip():
        raise HTTPException(status_code=400, detail="job_description is required")
    resumes = db.query(Resume).all()
    shortlisted = []
    for r in resumes:
        path = UPLOAD_DIR / r.filename if r.filename else None
        resume_text = ""
        if path and path.exists():
            try:
                resume_text = parse_pdf_text(str(path))
            except Exception:
                resume_text = ""
        res_skills = [s.strip() for s in (r.skills or "").split(",") if s.strip()]
        scores = score_resume_against_jd(job_description, resume_text, res_skills)
        r.skills_score = scores["skills_score"]
        r.experience_score = scores["experience_score"]
        r.education_score = scores["education_score"]
        r.overall_score = scores["overall_score"]
        r.strengths = ",".join(scores["strengths"])
        r.gaps = ",".join(scores["gaps"])
        r.justification = scores["justification"]
        r.job_match_percentage = scores["job_match_percentage"]
        r.match_reasoning = scores["match_reasoning"]
        db.commit()
        shortlisted.append({
            "id": r.id,
            "filename": r.filename,
            "candidate_name": r.candidate_name,
            "email": r.email,
            "phone": r.phone,
            "skills": res_skills,
            "skills_score": r.skills_score,
            "experience_score": r.experience_score,
            "education_score": r.education_score,
            "overall_score": r.overall_score,
            "job_match_percentage": r.job_match_percentage,
            "strengths": [s for s in (r.strengths or "").split(",") if s],
            "gaps": [g for g in (r.gaps or "").split(",") if g],
            "justification": r.justification,
            "match_reasoning": r.match_reasoning,
        })
    shortlisted.sort(key=lambda x: x["overall_score"], reverse=True)
    return {"shortlisted_candidates": shortlisted}

@app.get("/models")
def get_models():
    try:
        return {"models": list_gemini_models()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {e}")

@app.post("/reset-db")
def reset_db():
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        return {
            "status": "reset",
            "note": "Dropped and recreated tables in existing database file."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

def reset_database_script():
    try:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✓ Dropped and recreated tables")
        print("✓ Database reset complete!")
        print("\nSchema columns include:")
        print("  - job_match_percentage (Integer)")
        print("  - match_reasoning (Text)")
    except Exception as e:
        print("Reset failed:", e)

def list_gemini_models_for_cli():
    try:
        models = list_gemini_models()
        if not models:
            print("No models found or API key not configured")
            return
        print("Models supporting generation:")
        for name in models:
            print(" -", name)
    except Exception as e:
        print("Error listing models:", e)

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
