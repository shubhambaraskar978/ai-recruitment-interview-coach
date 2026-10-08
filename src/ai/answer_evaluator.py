import os
import json
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
# ANSWER EVALUATOR
# ============================================================

def evaluate_answer(
    question: str,
    candidate_answer: str,
    resume_text: str = "",
    job_description: str = "",
) -> dict:
    """
    Evaluate an interview answer and return structured data.
    """

    if not question.strip():
        return {
            "error": "Interview question is empty."
        }

    if not candidate_answer.strip():
        return {
            "error": "Candidate answer is empty."
        }


    # ========================================================
    # AI PROMPT
    # ========================================================

    prompt = f"""
You are an expert technical interviewer.

Evaluate the candidate's answer to the interview question.

Be fair, realistic, and constructive.

IMPORTANT RULES:

- Evaluate only what the candidate actually said.
- Do not assume knowledge that is not demonstrated.
- Do not invent candidate experience.
- Consider the candidate's resume and job description
  when relevant.
- A long answer is not automatically a good answer.
- A short answer can receive a high score if it is correct
  and complete.

Score each category from 0 to 10:

1. Technical Correctness
2. Relevance
3. Completeness
4. Clarity

Calculate the overall score as the average of these
four scores.

Return ONLY valid JSON.

Use EXACTLY this structure:

{{
    "overall_score": 0,
    "technical_correctness": 0,
    "relevance": 0,
    "completeness": 0,
    "clarity": 0,
    "verdict": "Excellent",
    "strengths": [
        "strength 1",
        "strength 2"
    ],
    "improvements": [
        "improvement 1",
        "improvement 2"
    ],
    "missing_points": [
        "missing point 1"
    ],
    "ideal_answer": "A concise ideal answer..."
}}

The verdict MUST be one of:

- Excellent
- Strong
- Good
- Needs Improvement
- Poor

Scores MUST be numbers between 0 and 10.

--------------------------------------------------
INTERVIEW QUESTION
--------------------------------------------------

{question}

--------------------------------------------------
CANDIDATE ANSWER
--------------------------------------------------

{candidate_answer}

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


    # ========================================================
    # CALL GROQ
    # ========================================================

    try:

        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional technical "
                        "interviewer. Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
        )


        raw_response = response.choices[0].message.content


        # ====================================================
        # CLEAN RESPONSE
        # ====================================================

        raw_response = raw_response.strip()


        # Remove Markdown JSON fences if model adds them
        if raw_response.startswith("```json"):
            raw_response = raw_response[7:]

        elif raw_response.startswith("```"):
            raw_response = raw_response[3:]


        if raw_response.endswith("```"):
            raw_response = raw_response[:-3]


        raw_response = raw_response.strip()


        # ====================================================
        # PARSE JSON
        # ====================================================

        evaluation = json.loads(raw_response)


        # ====================================================
        # VALIDATE REQUIRED FIELDS
        # ====================================================

        required_fields = [
            "overall_score",
            "technical_correctness",
            "relevance",
            "completeness",
            "clarity",
            "verdict",
            "strengths",
            "improvements",
            "missing_points",
            "ideal_answer",
        ]


        for field in required_fields:

            if field not in evaluation:

                raise ValueError(
                    f"AI response missing field: {field}"
                )


        return evaluation


    except json.JSONDecodeError as e:

        return {
            "error": (
                "AI returned an invalid JSON response.",
                str(e),
            )
        }


    except Exception as e:

        return {
            "error": str(e)
        }