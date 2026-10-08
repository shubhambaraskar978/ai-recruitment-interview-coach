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
    "https://api.groq.com/openai/v1",
)

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
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
# FINAL INTERVIEW REPORT
# ============================================================

def generate_interview_report(
    resume_text: str,
    job_description: str,
    questions: list,
    answers: list,
    evaluations: list,
) -> dict:
    """
    Generate a final AI-powered interview performance report.

    Returns:
        Structured dictionary containing:
        - overall_score
        - hiring_readiness
        - strengths
        - weaknesses
        - recommendations
        - technical_assessment
        - communication_assessment
        - job_fit_assessment
        - interviewer_summary
        - hiring_recommendation
    """

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    if not questions:

        return {
            "error": "No interview questions were provided."
        }

    if not answers:

        return {
            "error": "No candidate answers were provided."
        }

    if not evaluations:

        return {
            "error": "No interview evaluations were provided."
        }


    # ========================================================
    # BUILD INTERVIEW DATA
    # ========================================================

    interview_data = []


    for index, question in enumerate(questions):

        answer = (
            answers[index]
            if index < len(answers)
            else "No answer provided."
        )

        evaluation = (
            evaluations[index]
            if index < len(evaluations)
            else {}
        )

        interview_data.append(
            {
                "question_number": index + 1,
                "question": question,
                "answer": answer,
                "evaluation": evaluation,
            }
        )


    interview_json = json.dumps(
        interview_data,
        indent=2,
        ensure_ascii=False,
    )


    # ========================================================
    # AI PROMPT
    # ========================================================

    prompt = f"""
You are a senior technical recruiter and interview evaluator.

Generate a final recruitment interview performance report
for the candidate.

You have access to:

1. Candidate resume
2. Job description
3. Interview questions
4. Candidate answers
5. Individual AI evaluations

Analyze the COMPLETE interview, not just the individual scores.

IMPORTANT:

- Do not invent candidate experience.
- Base your assessment only on the supplied information.
- Be realistic and professional.
- Identify repeated strengths and weaknesses.
- Consider the job requirements.
- Distinguish technical knowledge from communication.
- Give actionable preparation recommendations.
- Do not automatically recommend hiring because of a high score.
- Do not automatically reject because of a low score.

Return ONLY valid JSON.

Use EXACTLY this structure:

{{
    "overall_score": 0,
    "hiring_readiness": 0,
    "technical_score": 0,
    "communication_score": 0,
    "job_fit_score": 0,

    "strengths": [
        "strength 1",
        "strength 2",
        "strength 3"
    ],

    "weaknesses": [
        "weakness 1",
        "weakness 2",
        "weakness 3"
    ],

    "technical_assessment": "Detailed but concise assessment.",

    "communication_assessment": "Detailed but concise assessment.",

    "job_fit_assessment": "Detailed but concise assessment.",

    "recommended_topics": [
        "topic 1",
        "topic 2",
        "topic 3"
    ],

    "action_plan": [
        "action 1",
        "action 2",
        "action 3"
    ],

    "hiring_recommendation": "Strong Candidate",

    "interviewer_summary": "Professional final recruiter summary."
}}

SCORING:

All scores must be between 0 and 10.

"hiring_readiness" must be between 0 and 100.

"overall_score" is the candidate's overall interview
performance out of 10.

"technical_score" measures technical knowledge.

"communication_score" measures clarity, structure,
confidence and ability to explain concepts.

"job_fit_score" measures alignment with the supplied
job description.

"hiring_recommendation" MUST be one of:

- Strong Candidate
- Potential Candidate
- Needs Improvement
- Not Ready

Candidate resume:

--------------------------------------------------
{resume_text}
--------------------------------------------------

Job description:

--------------------------------------------------
{job_description}
--------------------------------------------------

Interview questions, answers and evaluations:

--------------------------------------------------
{interview_json}
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
                        "You are a senior technical recruiter. "
                        "Return ONLY valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],

            temperature=0.1,
        )


        raw_response = (
            response.choices[0]
            .message
            .content
        )


        # ====================================================
        # CLEAN RESPONSE
        # ====================================================

        raw_response = raw_response.strip()


        if raw_response.startswith(
            "```json"
        ):

            raw_response = raw_response[7:]


        elif raw_response.startswith(
            "```"
        ):

            raw_response = raw_response[3:]


        if raw_response.endswith(
            "```"
        ):

            raw_response = raw_response[:-3]


        raw_response = raw_response.strip()


        # ====================================================
        # PARSE JSON
        # ====================================================

        report = json.loads(
            raw_response
        )


        # ====================================================
        # REQUIRED FIELDS
        # ====================================================

        required_fields = [
            "overall_score",
            "hiring_readiness",
            "technical_score",
            "communication_score",
            "job_fit_score",
            "strengths",
            "weaknesses",
            "technical_assessment",
            "communication_assessment",
            "job_fit_assessment",
            "recommended_topics",
            "action_plan",
            "hiring_recommendation",
            "interviewer_summary",
        ]


        for field in required_fields:

            if field not in report:

                raise ValueError(
                    f"AI report missing field: {field}"
                )


        # ====================================================
        # NORMALIZE SCORES
        # ====================================================

        def safe_score(
            value,
            maximum,
        ):

            try:

                value = float(value)

            except (
                TypeError,
                ValueError,
            ):

                value = 0.0


            return min(
                max(
                    value,
                    0.0,
                ),
                maximum,
            )


        report["overall_score"] = safe_score(
            report["overall_score"],
            10,
        )

        report["technical_score"] = safe_score(
            report["technical_score"],
            10,
        )

        report["communication_score"] = safe_score(
            report["communication_score"],
            10,
        )

        report["job_fit_score"] = safe_score(
            report["job_fit_score"],
            10,
        )

        report["hiring_readiness"] = safe_score(
            report["hiring_readiness"],
            100,
        )


        return report


    # ========================================================
    # ERRORS
    # ========================================================

    except json.JSONDecodeError as e:

        return {
            "error": (
                "AI returned invalid JSON.",
                str(e),
            )
        }


    except Exception as e:

        return {
            "error": str(e)
        }