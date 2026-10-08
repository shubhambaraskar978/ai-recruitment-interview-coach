import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# PROJECT CONFIGURATION
# ============================================================

# Find project root:
# AI_Recruitment_Interview_Coach/
# ├── .env
# └── src/
#     └── ai/
#         └── resume_analyzer.py

PROJECT_ROOT = Path(__file__).resolve().parents[2]

ENV_FILE = PROJECT_ROOT / ".env"

# Load environment variables from project .env
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
    "llama-3.3-70b-versatile"
)


# ============================================================
# VALIDATE CONFIGURATION
# ============================================================

if not GROQ_API_KEY:
    raise ValueError(
        f"GROQ_API_KEY was not found.\n"
        f"Checked: {ENV_FILE}"
    )


if not GROQ_MODEL:
    raise ValueError(
        f"GROQ_MODEL was not found.\n"
        f"Checked: {ENV_FILE}"
    )


# ============================================================
# CREATE GROQ CLIENT
# ============================================================

client = OpenAI(
    api_key=GROQ_API_KEY,
    base_url=GROQ_BASE_URL,
)


# ============================================================
# RESUME ANALYZER
# ============================================================

def analyze_resume(resume_text: str) -> str:
    """
    Analyze resume text using Groq's LLM.

    Args:
        resume_text: Text extracted from the candidate's resume.

    Returns:
        AI-generated resume analysis.
    """

    if not resume_text or not resume_text.strip():
        return "No resume text was provided."

    prompt = f"""
You are an expert technical recruiter specializing in
software development, AI, machine learning, and technology roles.

Analyze the candidate's resume provided below.

Provide the analysis using exactly these sections:

1. Candidate Profile
2. Technical Skills
3. Education
4. Work Experience
5. Projects
6. Key Strengths
7. Areas for Improvement
8. Suitable Job Roles

Rules:
- Do NOT invent information.
- Use ONLY information present in the resume.
- If information is missing, write "Not specified".
- Identify technical skills clearly.
- Mention relevant programming languages, frameworks,
  databases, AI/ML technologies, and tools.
- For projects, mention the technologies used when available.
- Suggest realistic job roles based on the candidate's actual skills.
- Keep the analysis professional and useful for recruitment.
- Do not give false claims about the candidate.

Candidate Resume:
==================================================

{resume_text}

==================================================
"""

    try:

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an expert technical recruiter "
                        "who evaluates software developer and "
                        "AI/ML candidates."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.2,
        )

        return response.choices[0].message.content

    except Exception as e:

        return (
            "An error occurred while analyzing the resume.\n\n"
            f"Error: {str(e)}"
        )