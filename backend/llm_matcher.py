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
    You are a professional technical recruiter and hiring specialist.
    Examine the following resume text and job description.
    Extract structured data, evaluate candidate-job fit, and output a strictly valid JSON result.

    ---

    **Resume (Raw):**
    {resume_text}

    **Job Description:**
    {job_description}

    ---

    ### TASKS TO PERFORM

    1. **Data Extraction**
       - *Skills:* Extract all relevant technical and soft skills.
       - *Experience:* List job titles, companies, durations, and main responsibilities.
       - *Education:* Mention degrees, institutions, majors, and certifications.

    2. **Matching & Scoring**
       - Assign numerical scores (0–10) for:
         - skills_score
         - experience_score
         - education_score
         - overall_score
       - Ensure semantic understanding, not just keyword matching.

    3. **Detailed Review**
       - List strengths and gaps.
       - Write a short justification.
       - Provide a recommendation: Highly Recommended / Recommended / Maybe / Not Recommended.

    ---

    ### OUTPUT FORMAT

    Respond ONLY with JSON using this exact schema:
    {{
      "name": "Candidate Full Name or 'Not Found'",
      "email": "email@example.com or 'Not Found'",
      "phone": "+1234567890 or 'Not Found'",
      "skills": ["Python", "React", "Machine Learning", "AWS", "Communication"],
      "experience": "5 years as Software Engineer at TechCorp (2019–2024): Developed ML pipeline processing 1M+ records daily.",
      "education": "B.S. Computer Science, MIT, 2017. AWS Solutions Architect Certification, 2022.",
      "overall_score": 8.3,
      "skills_score": 8.5,
      "experience_score": 8.0,
      "education_score": 7.5,
      "strengths": [
        "Strong expertise in Python and ML frameworks",
        "Proven experience with scalable data systems",
        "Relevant cloud computing exposure"
      ],
      "gaps": [
        "Missing Kubernetes experience",
        "Limited leadership exposure"
      ],
      "justification": "The candidate demonstrates strong alignment in technical and cloud skills, with moderate leadership exposure gaps.",
      "recommendation": "Recommended"
    }}

    ### RULES
    - Return plain JSON (no markdown or commentary)
    - Use floats for all scores
    - Missing values should be 'Not Found' or []
    - Be deterministic in scoring
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
