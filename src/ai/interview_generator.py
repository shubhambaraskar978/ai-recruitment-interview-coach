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
# INTERVIEW QUESTION GENERATOR
# ============================================================

def generate_interview_questions(
    resume_text: str,
    job_description: str,
    number_of_questions: int = 10,
) -> str:
    """
    Generate personalized interview questions based on
    the candidate resume and job description.
    """

    if not resume_text.strip():
        return "Resume text is empty."

    if not job_description.strip():
        return "Job description is empty."

    prompt = f"""
You are an expert technical interviewer and recruitment
specialist.

Generate a personalized interview for the candidate.

Use BOTH:
1. The candidate's resume
2. The target job description

The questions must be relevant to the candidate's actual
skills, projects, and the requirements of the job.

IMPORTANT RULES:

- Do not invent candidate experience.
- Do not claim the candidate knows a technology unless
  the resume explicitly demonstrates it.
- Ask project-specific questions when possible.
- Include questions about skills required by the job.
- Include questions about gaps between the resume and JD.
- Mix easy, medium, and difficult questions.
- Avoid generic questions whenever a personalized question
  can be created.

Create exactly {number_of_questions} questions.

Use these categories:

1. HR / Introduction
2. Resume / Project
3. Technical
4. Problem Solving
5. Job-Specific
6. Skill Gap

For every question provide:

Question Number
Category
Difficulty
Question
What the interviewer is evaluating

Example format:

### Question 1
**Category:** Project
**Difficulty:** Medium

**Question:**
Explain the architecture of your Gagan Industry project
and describe how the frontend communicates with the backend.

**Interviewer is evaluating:**
Understanding of full-stack architecture and REST APIs.

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
                        "You are an experienced technical "
                        "interviewer specializing in software "
                        "development and AI recruitment."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.3,
        )

        return response.choices[0].message.content

    except Exception as e:

        return (
            "An error occurred while generating "
            f"interview questions.\n\nError: {str(e)}"
        )