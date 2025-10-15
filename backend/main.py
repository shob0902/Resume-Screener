from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from sqlalchemy.orm import Session
import os
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
from resume_parser import extract_text_from_pdf
from llm_matcher import extract_and_match_raw_text
from database import init_db, get_db, Resume

app = FastAPI(title="Smart Resume Screener API - Database Integrated")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
init_db()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

executor = ThreadPoolExecutor(max_workers=10)

def get_file_hash(content: bytes) -> str:
    return hashlib.md5(content).hexdigest()

@app.get("/")
def root(db: Session = Depends(get_db)):
    total_resumes = db.query(Resume).count()
    return {
        "message": "Smart Resume Screener API - Database Integrated",
        "version": "3.0",
        "storage": "SQLite Database (Persistent)",
        "total_resumes": total_resumes,
        "endpoints": {
            "POST /batch-upload": "Upload multiple resumes",
            "POST /match": "Match resumes with job description",
            "GET /resumes": "Get all stored resumes",
            "DELETE /resumes/{id}": "Delete specific resume",
            "DELETE /resumes": "Clear all resumes from database"
        }
    }

@app.post("/batch-upload")
async def batch_upload(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    # Clear previously uploaded resumes so new batch replaces prior data
    try:
        db.query(Resume).delete()
        db.commit()
    except Exception:
        db.rollback()

    async def process_single_file(file):
        if not file.filename.endswith('.pdf'):
            return {"filename": file.filename, "status": "error", "message": "Only PDF files supported"}
        
        try:
            # Read file content (using the same method as original)
            file_content = await file.read()
            file_hash = get_file_hash(file_content)
            
            # Save temporarily
            file_path = os.path.join(UPLOAD_DIR, file.filename)
            with open(file_path, "wb") as buffer:
                buffer.write(file_content)
            
            try:
                # Extract text
                loop = asyncio.get_event_loop()
                resume_text = await loop.run_in_executor(executor, extract_text_from_pdf, file_path)
            finally:
                # Clean up temp file
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            # Save to database
            new_resume = Resume(
                filename=file.filename,
                raw_text=resume_text,
                candidate_name="Pending Analysis",
                created_at=datetime.utcnow()
            )
            db.add(new_resume)
            db.commit()
            db.refresh(new_resume)
            
            return {
                "filename": file.filename, 
                "status": "success", 
                "resume_id": new_resume.id, 
                "text_length": len(resume_text)
            }
        except Exception as e:
            db.rollback()
            return {"filename": file.filename, "status": "error", "message": str(e)}

    start_time = datetime.now()
    results = await asyncio.gather(*[process_single_file(file) for file in files])
    elapsed = (datetime.now() - start_time).total_seconds()
    
    successful_count = len([r for r in results if r["status"] == "success"])
    
    return {
        "total_files": len(files),
        "successful": successful_count,
        "failed": len([r for r in results if r["status"] == "error"]),
        "processing_time": f"{elapsed:.2f}s",
        "results": results
    }

@app.post("/match")
async def match_resumes(job_description: str = Form(...), db: Session = Depends(get_db)):
    resumes = db.query(Resume).all()
    
    if not resumes:
        raise HTTPException(status_code=404, detail="No resumes found. Please upload resumes first.")

    start_time = datetime.now()

    async def process_single_resume(resume: Resume):
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                executor, 
                extract_and_match_raw_text, 
                resume.raw_text, 
                job_description
            )
            
            # Update resume with match results
            resume.candidate_name = result['name']
            resume.email = result['email']
            resume.phone = result['phone']
            resume.skills = ", ".join(result['skills'])
            resume.experience = result['experience']
            resume.education = result['education']
            resume.match_score = result['overall_score']
            resume.skills_score = result['skills_score']
            resume.experience_score = result['experience_score']
            resume.education_score = result['education_score']
            resume.justification = result['justification']
            resume.job_description = job_description
            
            db.commit()
            
            return {
                "resume_id": resume.id,
                "candidate_name": result['name'],
                "email": result['email'],
                "phone": result['phone'],
                "filename": resume.filename,
                "skills": result['skills'],
                "overall_score": result['overall_score'],
                "skills_score": result['skills_score'],
                "experience_score": result['experience_score'],
                "education_score": result['education_score'],
                "strengths": result['strengths'],
                "gaps": result['gaps'],
                "justification": result['justification'],
                "recommendation": result['recommendation']
            }
        except Exception as e:
            print(f"Error processing resume {resume.id}: {str(e)}")
            return None

    results = await asyncio.gather(*[process_single_resume(resume) for resume in resumes])
    results = [r for r in results if r is not None]
    elapsed = (datetime.now() - start_time).total_seconds()
    
    # Sort by overall score
    results.sort(key=lambda x: x['overall_score'], reverse=True)
    
    return {
        "total_candidates": len(results),
        "job_description": job_description,
        "processing_time": f"{elapsed:.2f}s",
        "shortlisted_candidates": results
    }

@app.delete("/resumes/{resume_id}")
def delete_resume(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    filename = resume.filename
    db.delete(resume)
    db.commit()
    
    remaining = db.query(Resume).count()
    return {
        "message": "Resume deleted successfully", 
        "deleted_id": resume_id, 
        "filename": filename,
        "remaining": remaining
    }

@app.delete("/resumes")
def delete_all_resumes(db: Session = Depends(get_db)):
    count = db.query(Resume).count()
    db.query(Resume).delete()
    db.commit()
    
    return {
        "message": f"All {count} resumes deleted successfully", 
        "storage_cleared": True
    }

@app.get("/resumes")
def get_all_resumes(db: Session = Depends(get_db)):
    resumes = db.query(Resume).all()
    return {
        "total": len(resumes),
        "resumes": [
            {
                "id": r.id,
                "filename": r.filename,
                "candidate_name": r.candidate_name,
                "email": r.email,
                "match_score": r.match_score,
                "created_at": r.created_at.isoformat() if r.created_at else None
            } 
            for r in resumes
        ]
    }

@app.get("/resume/{resume_id}")
def get_resume_details(resume_id: int, db: Session = Depends(get_db)):
    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    return {
        "id": resume.id,
        "filename": resume.filename,
        "candidate_name": resume.candidate_name,
        "email": resume.email,
        "phone": resume.phone,
        "skills": resume.skills.split(", ") if resume.skills else [],
        "experience": resume.experience,
        "education": resume.education,
        "match_score": resume.match_score,
        "skills_score": resume.skills_score,
        "experience_score": resume.experience_score,
        "education_score": resume.education_score,
        "justification": resume.justification,
        "job_description": resume.job_description,
        "created_at": resume.created_at.isoformat() if resume.created_at else None
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)