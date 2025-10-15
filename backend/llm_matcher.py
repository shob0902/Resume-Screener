import os
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv

def analyze_resume_fit(resume_text, job_description):
    """
    Function: Analyze resume and match it with the given job description.
    Uses Gemini API to extract structured data and generate semantic fit scores.
    """
    # Load environment variables and configure Gemini
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    # Construct prompt for Gemini
    analysis_prompt = f"""
        analysis_prompt = f"""
    You are an experienced recruiter and talent evaluator.
    Carefully review the following candidate resume and job description.
    Extract structured insights, assess compatibility, and respond with a valid JSON report only.

    ---

    **Candidate Resume (Text):**
    {resume_text}

    **Job Description Provided:**
    {job_description}

    ---

    ### TASK OBJECTIVES

    1. **Information Extraction**
       - Identify all technical, analytical, and interpersonal skills.
       - Summarize professional experience: roles, organizations, timelines, and key contributions.
       - Include educational background with degrees, institutions, majors, and certifications.

    2. **Relevance Evaluation & Scoring**
       - Assign numeric values between 0–10 for:
         - skills_score
         - experience_score
         - education_score
         - overall_score
       - Focus on contextual understanding rather than mere keyword overlap.

    3. **Comprehensive Review**
       - Highlight main strengths and improvement areas.
       - Give a concise justification for the evaluation.
       - Conclude with a hiring recommendation: Highly Recommended / Recommended / Maybe / Not Recommended.

    ---

    ### EXPECTED OUTPUT

    Provide strictly JSON output following this schema:
    {{
      "name": "Full Candidate Name or 'Not Found'",
      "email": "email@example.com or 'Not Found'",
      "phone": "+1234567890 or 'Not Found'",
      "skills": ["Python", "React", "Machine Learning", "AWS", "Communication"],
      "experience": "Worked as Software Engineer at TechCorp (2019–2024): Built scalable ML pipelines. Prior role as Data Analyst at StartupXYZ (2017–2019).",
      "education": "B.Tech in Computer Science, MIT, 2017; AWS Solutions Architect Certificate, 2022.",
      "overall_score": 8.3,
      "skills_score": 8.5,
      "experience_score": 8.0,
      "education_score": 7.5,
      "strengths": [
        "Strong Python and ML background",
        "Hands-on cloud experience",
        "Good match for listed technologies"
      ],
      "gaps": [
        "Missing Kubernetes experience",
        "Limited leadership exposure"
      ],
      "justification": "Candidate aligns well with core technical requirements, though lacks some management and containerization experience.",
      "recommendation": "Recommended"
    }}

    ### IMPORTANT GUIDELINES
    - Return *only* the JSON (no markdown, quotes, or comments)
    - All numerical values must be floats (e.g., 8.0)
    - If any data is unavailable, use 'Not Found' or an empty array []
    - Maintain logical, consistent scoring throughout
    """

    try:
        # Call Gemini model
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        output = model.generate_content(analysis_prompt)
        raw_response = output.text.strip()

        # Clean any markdown formatting (if present)
        if raw_response.startswith("```"):
            raw_response = re.sub(r"```json\n?|\n?```", "", raw_response).strip()

        # Parse JSON safely
        parsed_data = json.loads(raw_response)

        # Return standardized structure
        return {
            "name": parsed_data.get("name", "Not Found"),
            "email": parsed_data.get("email", "Not Found"),
            "phone": parsed_data.get("phone", "Not Found"),
            "skills": parsed_data.get("skills", []),
            "experience": parsed_data.get("experience", "Not Found"),
            "education": parsed_data.get("education", "Not Found"),
            "overall_score": parsed_data.get("overall_score", 5.0),
            "skills_score": parsed_data.get("skills_score", 5.0),
            "experience_score": parsed_data.get("experience_score", 5.0),
            "education_score": parsed_data.get("education_score", 5.0),
            "strengths": parsed_data.get("strengths", []),
            "gaps": parsed_data.get("gaps", []),
            "justification": parsed_data.get("justification", "Analysis not available"),
            "recommendation": parsed_data.get("recommendation", "Needs Review")
        }

    except Exception as error:
        print(f"[Gemini Error] {str(error)}")
        return {
            "name": "Error",
            "email": "Error",
            "phone": "Error",
            "skills": [],
            "experience": "Error analyzing resume",
            "education": "Error analyzing resume",
            "overall_score": 0.0,
            "skills_score": 0.0,
            "experience_score": 0.0,
            "education_score": 0.0,
            "strengths": ["Error analyzing resume"],
            "gaps": ["Error analyzing resume"],
            "justification": f"Error: {str(error)}",
            "recommendation": "Needs Manual Review"
        }
