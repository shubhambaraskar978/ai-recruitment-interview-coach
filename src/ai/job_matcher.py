import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

load_dotenv(dotenv_path=ENV_FILE)


# ============================================================
# GROQ CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

GROQ_BASE_URL = os.getenv(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1"
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b"
)


# ============================================================
# VALIDATION
# ============================================================

if not GROQ_API_KEY:
    raise ValueError(
        f"GROQ_API_KEY was not found. Checked: {ENV_FILE}"
    )


# ============================================================
# GROQ CLIENT
# ============================================================

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL,
)


# ============================================================
# JOB MATCH ANALYZER
# ============================================================

def analyze_job_match(
    resume_text: str,
    job_description: str
) -> str:
    """
    Compare a candidate resume against a job description.

    Returns an AI-generated recruitment match analysis.
    """

    if not resume_text.strip():
        return "Resume text is empty."

    if not job_description.strip():
        return "Job description is empty."

    prompt = f"""
You are an expert technical recruiter and candidate
screening specialist.

Your task is to compare the candidate's resume with
the provided job description.

IMPORTANT RULES:

- Use only information explicitly present in the resume.
- Do not assume a skill because another related skill exists.
- Do not treat GitHub as proof that Git is a candidate skill.
- Do not treat React as proof that JavaScript is explicitly listed.
- Clearly distinguish between matched skills and missing skills.
- Do not invent work experience.
- Do not invent certifications.
- Do not invent projects.
- Give a realistic assessment for an entry-level candidate.

Return the result using EXACTLY these sections:

1. Overall Match Score
Give a percentage from 0 to 100.

2. Matching Skills
List skills explicitly present in BOTH the resume and
job description.

3. Missing or Weak Skills
List important skills required by the job description
that are not clearly demonstrated in the resume.

4. Matching Projects
Identify resume projects that are relevant to the
job description.

5. Candidate Strengths
Explain why the candidate may be suitable for this role.

6. Skill Gaps
Explain the most important areas the candidate should improve.

7. Interview Preparation
Give 5 specific technical topics the candidate should
prepare based on the job description.

8. Recruitment Recommendation
Choose one:
- Strong Match
- Good Match
- Partial Match
- Weak Match

Then briefly explain the recommendation.

--------------------------------------------------
CANDIDATE RESUME
--------------------------------------------------

{resume_text}

--------------------------------------------------
JOB DESCRIPTION
--------------------------------------------------

{job_description}

--------------------------------------------------
"""

    try:

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical recruiter "
                        "who evaluates candidates against "
                        "software engineering job descriptions."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
        )

        return response.choices[0].message.content

    except Exception as e:

        return (
            "An error occurred while analyzing the job match.\n\n"
            f"Error: {str(e)}"
        )