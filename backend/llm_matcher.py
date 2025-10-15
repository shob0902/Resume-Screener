import google.generativeai as genai
import json
import re
import os
from dotenv import load_dotenv

def extract_and_match_raw_text(resume_text, job_description):
    load_dotenv()
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    prompt = f"""
    You are an expert technical recruiter and talent evaluator. 
    Your task is to analyze a candidate's resume and evaluate how well they match a given job description. 
    Focus on **structured extraction** of skills, experience, and education, then perform semantic matching.

    ---

    ### INPUTS

    **Resume (raw text):**
    {resume_text}

    **Job Description:**
    {job_description}

    ---

    ### TASK INSTRUCTIONS

    1. **Extract Structured Data:**
       - **Skills:** List all technical skills, tools, frameworks, programming languages, and soft skills
       - **Experience:** Extract work history with company names, roles, durations, and key responsibilities
       - **Education:** Extract degrees, institutions, majors, graduation years, and certifications

    2. **Semantic Matching & Scoring:**
       - Assign scores (0-10) for:
         * `skills_score`: Alignment of technical and soft skills with job requirements
         * `experience_score`: Relevance and depth of professional experience to the role
         * `education_score`: Fit of academic background and certifications
         * `overall_score`: Holistic candidate-job fit considering all factors
       - Evaluate *semantic similarity* not just keyword matching (e.g., "React" ≈ "Frontend Frameworks")

    3. **Analysis:**
       - Identify **strengths**: What makes this candidate stand out for this role?
       - Identify **gaps**: What skills or experience are missing?
       - Provide clear **justification** for scores
       - Give a **recommendation**: Highly Recommended / Recommended / Maybe / Not Recommended

    ---

    ### JSON OUTPUT FORMAT

    Return **strictly valid JSON** with this exact structure:

    {{
      "name": "Candidate Full Name or 'Not Found'",
      "email": "email@example.com or 'Not Found'",
      "phone": "+1234567890 or 'Not Found'",
      
      "skills": ["Python", "React", "Machine Learning", "AWS", "Communication"],
      
      "experience": "5 years as Software Engineer at TechCorp (2019-2024): Led development of ML pipeline processing 1M+ records daily. 2 years as Data Analyst at StartupXYZ (2017-2019): Built dashboards and automated reporting.",
      
      "education": "B.S. Computer Science, MIT, 2017. AWS Solutions Architect Certification, 2022.",
      
      "overall_score": 8.3,
      "skills_score": 8.5,
      "experience_score": 8.0,
      "education_score": 7.5,
      
      "strengths": [
        "Strong expertise in Python and ML frameworks matching job requirements",
        "Proven experience building scalable data pipelines",
        "Relevant AWS cloud experience"
      ],
      
      "gaps": [
        "Limited experience with Kubernetes mentioned in job description",
        "No direct leadership experience required for senior role",
        "Missing experience with specific tool XYZ"
      ],
      
      "justification": "The candidate demonstrates strong technical skills aligned with the role, particularly in Python, ML, and cloud technologies. Their experience building production ML systems is highly relevant. However, they lack some senior-level leadership experience and specific tools mentioned in the job description. Overall, a strong fit with some growth areas.",
      
      "recommendation": "Recommended"
    }}

    ---

    ### SCORING GUIDELINES

    - **9-10:** Exceptional match — exceeds all major requirements, rare find
    - **7-8:** Strong match — meets most requirements well, highly qualified
    - **5-6:** Moderate match — some gaps but shows potential, trainable
    - **3-4:** Weak match — lacks several key qualifications
    - **0-2:** Poor match — fundamentally misaligned with role

    ---

    ### CRITICAL RULES

    - Output **ONLY** the JSON structure — no markdown, no code blocks, no commentary
    - Be consistent and deterministic in scoring
    - Ensure all numbers are floats (e.g., 8.0 not "eight")
    - Use plain text, no special formatting
    - If information is missing, use "Not Found" or empty arrays []
    - Focus on semantic understanding, not just keyword matching

    Begin your analysis now.
    """

    try:
        model = genai.GenerativeModel('gemini-2.0-flash-exp')
        response = model.generate_content(prompt)
        result_text = response.text.strip()
        
        # Clean any markdown formatting
        if result_text.startswith("```"):
            result_text = re.sub(r'```json\n?|\n?```', '', result_text).strip()
        
        data = json.loads(result_text)

        return {
            "name": data.get("name", "Not Found"),
            "email": data.get("email", "Not Found"),
            "phone": data.get("phone", "Not Found"),
            "skills": data.get("skills", []),
            "experience": data.get("experience", "Not Found"),
            "education": data.get("education", "Not Found"),
            "overall_score": data.get("overall_score", 5.0),
            "skills_score": data.get("skills_score", 5.0),
            "experience_score": data.get("experience_score", 5.0),
            "education_score": data.get("education_score", 5.0),
            "strengths": data.get("strengths", []),
            "gaps": data.get("gaps", []),
            "justification": data.get("justification", "Analysis not available"),
            "recommendation": data.get("recommendation", "Needs Review")
        }
    except Exception as e:
        print(f"LLM Error: {str(e)}")
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
            "justification": f"Error: {str(e)}",
            "recommendation": "Needs Manual Review"
        }