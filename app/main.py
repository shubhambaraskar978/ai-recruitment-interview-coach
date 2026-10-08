import sys
from pathlib import Path

import streamlit as st


# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# PROJECT IMPORTS
# ============================================================

from src.resume.pdf_extractor import extract_text_from_pdf

from src.ai.resume_analyzer import analyze_resume

from src.ai.job_matcher import analyze_job_match

from src.ai.interview_generator import (
    generate_interview_questions
)

from src.ai.answer_evaluator import (
    evaluate_answer
)


# ============================================================
# STREAMLIT CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Recruitment Interview Coach",
    page_icon="🎯",
    layout="wide",
)


# ============================================================
# INTERVIEW SESSION STATE
# ============================================================

if "interview_questions" not in st.session_state:
    st.session_state.interview_questions = []

if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0

if "interview_answers" not in st.session_state:
    st.session_state.interview_answers = []

if "interview_evaluations" not in st.session_state:
    st.session_state.interview_evaluations = []

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

if "interview_completed" not in st.session_state:
    st.session_state.interview_completed = False

if "last_interview_evaluation" not in st.session_state:
    st.session_state.last_interview_evaluation = None

if "last_interview_question_index" not in st.session_state:
    st.session_state.last_interview_question_index = -1


# ============================================================
# RESET INTERVIEW
# ============================================================

if st.session_state.interview_started:
    if st.sidebar.button(
        "🔄 Reset Interview",
        use_container_width=True,
    ):
        st.session_state.interview_questions = []
        st.session_state.current_question_index = 0
        st.session_state.interview_answers = []
        st.session_state.interview_evaluations = []
        st.session_state.interview_started = False
        st.session_state.interview_completed = False
        st.session_state.last_interview_evaluation = None
        st.session_state.last_interview_question_index = -1
        st.rerun()


# ============================================================
# HEADER
# ============================================================

st.title("🎯 AI Recruitment Interview Coach")

st.write(
    "Upload your resume, add a job description, "
    "analyze your job match, generate personalized "
    "interview questions, and practice your answers "
    "with AI feedback."
)

st.divider()


# ============================================================
# JOB DESCRIPTION
# ============================================================

st.header("💼 Job Description")

st.write(
    "Paste the job description for the position "
    "you are preparing for."
)

job_description = st.text_area(
    "Paste Job Description",
    height=250,
    placeholder=(
        "Example:\n\n"
        "We are looking for a Python Developer with "
        "experience in Django, REST APIs, SQL and Git.\n\n"
        "Requirements:\n"
        "- Strong Python fundamentals\n"
        "- Object-Oriented Programming\n"
        "- Django or Flask\n"
        "- SQL and databases\n"
        "- REST APIs\n"
        "- Git\n"
        "- Basic cloud knowledge"
    ),
)

st.divider()


# ============================================================
# RESUME UPLOAD
# ============================================================

st.header("📄 Resume Analysis")

st.write(
    "Upload your resume in PDF format. "
    "The system will extract the resume content "
    "for AI analysis."
)

uploaded_resume = st.file_uploader(
    "Upload your Resume",
    type=["pdf"],
)


# ============================================================
# PROCESS RESUME
# ============================================================

if uploaded_resume is not None:

    st.success(
        f"Resume uploaded: {uploaded_resume.name}"
    )

    try:

        # ====================================================
        # PDF TEXT EXTRACTION
        # ====================================================

        resume_text = extract_text_from_pdf(
            uploaded_resume
        )

        if not resume_text:

            st.warning(
                "No text could be extracted from this PDF. "
                "It may be a scanned/image-based resume."
            )

        else:

            # =================================================
            # EXTRACTED TEXT
            # =================================================

            st.subheader("📋 Extracted Resume Text")

            with st.expander(
                "View extracted resume text"
            ):

                st.text_area(
                    "Resume Content",
                    resume_text,
                    height=400,
                )

            st.success(
                "Resume text extracted successfully! ✅"
            )


            # =================================================
            # AI RESUME ANALYSIS
            # =================================================

            st.divider()

            st.subheader("🧠 AI Resume Analysis")

            analyze_resume_button = st.button(
                "🚀 Analyze Resume with AI",
                type="primary",
                use_container_width=True,
            )

            if analyze_resume_button:

                with st.spinner(
                    "AI is analyzing your resume..."
                ):

                    try:

                        analysis = analyze_resume(
                            resume_text
                        )

                        st.success(
                            "AI resume analysis completed! ✅"
                        )

                        st.markdown(
                            analysis
                        )

                    except Exception as e:

                        st.error(
                            "AI resume analysis failed."
                        )

                        st.exception(e)


            # =================================================
            # JOB MATCHING
            # =================================================

            st.divider()

            st.subheader("🎯 Resume ↔ Job Match")

            st.write(
                "Compare your resume against the "
                "job description using AI."
            )

            if not job_description.strip():

                st.info(
                    "💡 Paste a job description above "
                    "to enable AI job matching."
                )

            else:

                match_button = st.button(
                    "🎯 Analyze Job Match",
                    type="primary",
                    use_container_width=True,
                )

                if match_button:

                    with st.spinner(
                        "AI is comparing your resume "
                        "with the job description..."
                    ):

                        try:

                            match_analysis = analyze_job_match(
                                resume_text,
                                job_description,
                            )

                            st.success(
                                "Job match analysis completed! ✅"
                            )

                            st.markdown(
                                match_analysis
                            )

                        except Exception as e:

                            st.error(
                                "Job match analysis failed."
                            )

                            st.exception(e)


            # =================================================
            # INTERACTIVE MOCK INTERVIEW
            # =================================================

            st.divider()

            st.subheader("🎤 AI Mock Interview")

            st.write(
                "Practice a realistic interview one question at a time "
                "using your resume and target job description."
            )

            if not job_description.strip():

                st.info(
                    "💡 Paste a job description above to start "
                    "your personalized mock interview."
                )

            else:

                # =================================================
                # INTERVIEW SETUP
                # =================================================

                if not st.session_state.interview_started:

                    st.markdown("### 🚀 Start Your Mock Interview")

                    interview_type = st.selectbox(
                        "Interview Type",
                        [
                            "Mixed",
                            "Technical",
                            "HR",
                            "Project Based",
                        ],
                        key="mock_interview_type",
                    )

                    number_of_questions = st.slider(
                        "Number of Questions",
                        min_value=5,
                        max_value=15,
                        value=5,
                        step=1,
                        key="mock_interview_question_count",
                    )

                    start_interview_button = st.button(
                        "🚀 Start Mock Interview",
                        type="primary",
                        use_container_width=True,
                        key="start_mock_interview",
                    )

                    if start_interview_button:

                        with st.spinner(
                            "AI is preparing your personalized interview..."
                        ):

                            try:

                                interview_result = (
                                    generate_interview_questions(
                                        resume_text,
                                        job_description,
                                        number_of_questions,
                                    )
                                )

                                import re

                                # Parse numbered questions from the
                                # existing interview generator output.
                                questions = []

                                for raw_line in interview_result.splitlines():

                                    line = raw_line.strip()

                                    if not line:
                                        continue

                                    # Remove common Markdown formatting.
                                    clean_line = re.sub(
                                        r"^\s*[-*]\s*",
                                        "",
                                        line,
                                    )

                                    clean_line = re.sub(
                                        r"^\*\*",
                                        "",
                                        clean_line,
                                    )

                                    clean_line = re.sub(
                                        r"\*\*$",
                                        "",
                                        clean_line,
                                    )

                                    match = re.match(
                                        r"^(?:Q(?:uestion)?\s*)?"
                                        r"(\d+)"
                                        r"[\.\):\-]\s*(.+)$",
                                        clean_line,
                                        re.IGNORECASE,
                                    )

                                    if match:

                                        question_text = (
                                            match.group(2).strip()
                                        )

                                        # Remove trailing metadata such as
                                        # category/difficulty only when they
                                        # are on the same line.
                                        question_text = re.sub(
                                            r"\s+\*\*(?:Category|Difficulty|Interviewer is evaluating):.*$",
                                            "",
                                            question_text,
                                            flags=re.IGNORECASE,
                                        ).strip()

                                        if len(question_text) >= 10:

                                            questions.append(
                                                question_text
                                            )

                                # Fallback: if the model returned paragraphs
                                # instead of numbered questions, use non-empty
                                # lines that look like actual questions.
                                if len(questions) < 1:

                                    for raw_line in interview_result.splitlines():

                                        line = raw_line.strip()

                                        if (
                                            len(line) >= 20
                                            and (
                                                "?" in line
                                                or line.lower().startswith(
                                                    (
                                                        "what ",
                                                        "why ",
                                                        "how ",
                                                        "explain ",
                                                        "describe ",
                                                        "tell ",
                                                    )
                                                )
                                            )
                                        ):

                                            questions.append(line)

                                questions = questions[
                                    :number_of_questions
                                ]

                                if not questions:

                                    st.error(
                                        "AI generated questions could not "
                                        "be parsed. Please try again."
                                    )

                                else:

                                    st.session_state.interview_questions = (
                                        questions
                                    )

                                    st.session_state.current_question_index = 0

                                    st.session_state.interview_answers = []

                                    st.session_state.interview_evaluations = []

                                    st.session_state.interview_started = True

                                    st.session_state.interview_completed = False

                                    st.rerun()

                            except Exception as e:

                                st.error(
                                    "Could not start the interview."
                                )

                                st.exception(e)


                # =================================================
                # ACTIVE / COMPLETED INTERVIEW
                # =================================================

                else:

                    questions = (
                        st.session_state.interview_questions
                    )

                    current_index = (
                        st.session_state.current_question_index
                    )

                    total_questions = len(questions)

                    # -------------------------------------------------
                    # COMPLETED
                    # -------------------------------------------------

                    if (
                        st.session_state.interview_completed
                        or current_index >= total_questions
                    ):

                        st.session_state.interview_completed = True

                        st.success(
                            "🏁 Mock interview completed!"
                        )

                        st.subheader(
                            "📊 Interview Summary"
                        )

                        evaluations = (
                            st.session_state.interview_evaluations
                        )

                        valid_evaluations = [
                            item
                            for item in evaluations
                            if (
                                isinstance(item, dict)
                                and not item.get("error")
                            )
                        ]

                        scores = []

                        for evaluation in valid_evaluations:

                            try:
                                score = float(
                                    evaluation.get(
                                        "overall_score",
                                        0,
                                    )
                                )

                                score = min(
                                    max(score, 0.0),
                                    10.0,
                                )

                                scores.append(score)

                            except (TypeError, ValueError):
                                pass

                        if scores:

                            average_score = (
                                sum(scores) / len(scores)
                            )

                            st.metric(
                                "🏆 Average Interview Score",
                                f"{average_score:.1f} / 10",
                            )

                        else:

                            st.warning(
                                "No valid evaluation scores were "
                                "available for this interview."
                            )

                        st.write(
                            f"Questions completed: "
                            f"{len(evaluations)} / {total_questions}"
                        )

                        if scores:

                            if average_score >= 8:
                                recommendation = "Excellent performance"
                            elif average_score >= 7:
                                recommendation = "Strong candidate"
                            elif average_score >= 5:
                                recommendation = "Needs more preparation"
                            else:
                                recommendation = "Significant preparation recommended"

                            st.info(
                                f"🎯 Recommendation: **{recommendation}**"
                            )

                        st.divider()

                        for index, evaluation in enumerate(
                            valid_evaluations
                        ):

                            if index >= total_questions:
                                break

                            with st.expander(
                                f"Question {index + 1} — "
                                f"{float(evaluation.get('overall_score', 0)):.1f}/10"
                            ):

                                st.write(
                                    questions[index]
                                )

                                st.write(
                                    "**Verdict:**",
                                    evaluation.get(
                                        "verdict",
                                        "Not specified",
                                    ),
                                )

                                strengths = evaluation.get(
                                    "strengths",
                                    [],
                                )

                                if strengths:

                                    st.write(
                                        "**Strengths:**"
                                    )

                                    for item in strengths:

                                        st.markdown(
                                            f"- {item}"
                                        )

                                improvements = evaluation.get(
                                    "improvements",
                                    [],
                                )

                                if improvements:

                                    st.write(
                                        "**Improvements:**"
                                    )

                                    for item in improvements:

                                        st.markdown(
                                            f"- {item}"
                                        )

                        if st.button(
                            "🔄 Start New Interview",
                            type="primary",
                            use_container_width=True,
                            key="start_new_mock_interview",
                        ):

                            st.session_state.interview_questions = []

                            st.session_state.current_question_index = 0

                            st.session_state.interview_answers = []

                            st.session_state.interview_evaluations = []

                            st.session_state.interview_started = False

                            st.session_state.interview_completed = False

                            st.session_state.last_interview_evaluation = None
                            st.session_state.last_interview_question_index = -1

                            st.rerun()


                    # -------------------------------------------------
                    # CURRENT QUESTION
                    # -------------------------------------------------

                    else:

                        st.progress(
                            current_index / total_questions
                        )

                        st.caption(
                            f"Question {current_index + 1} of "
                            f"{total_questions}"
                        )

                        st.markdown(
                            f"### 🎤 Question "
                            f"{current_index + 1} / "
                            f"{total_questions}"
                        )

                        st.info(
                            questions[current_index]
                        )

                        answer_key = (
                            f"mock_answer_{current_index}"
                        )

                        candidate_answer = st.text_area(
                            "💬 Your Answer",
                            height=220,
                            key=answer_key,
                            placeholder=(
                                "Type your answer as if you "
                                "were speaking to the interviewer..."
                            ),
                        )

                        submit_answer_button = st.button(
                            "🤖 Submit Answer",
                            type="primary",
                            use_container_width=True,
                            key=f"submit_mock_answer_{current_index}",
                        )

                        if submit_answer_button:

                            if not candidate_answer.strip():

                                st.warning(
                                    "Please enter your answer "
                                    "before submitting."
                                )

                            else:

                                with st.spinner(
                                    "AI interviewer is evaluating "
                                    "your answer..."
                                ):

                                    try:

                                        evaluation = evaluate_answer(
                                            question=questions[current_index],
                                            candidate_answer=candidate_answer,
                                            resume_text=resume_text,
                                            job_description=job_description,
                                        )

                                        st.session_state.interview_answers.append(
                                            candidate_answer
                                        )

                                        st.session_state.interview_evaluations.append(
                                            evaluation
                                        )

                                        # Keep the evaluation visible across
                                        # the Streamlit rerun.
                                        st.session_state.last_interview_evaluation = (
                                            evaluation
                                        )

                                        st.session_state.last_interview_question_index = (
                                            current_index
                                        )

                                        st.rerun()

                                    except Exception as e:

                                        st.error(
                                            "Answer evaluation failed."
                                        )

                                        st.exception(e)

                        # -------------------------------------------------
                        # SHOW LATEST EVALUATION
                        # -------------------------------------------------

                        last_evaluation = (
                            st.session_state.get(
                                "last_interview_evaluation"
                            )
                        )

                        last_question_index = (
                            st.session_state.get(
                                "last_interview_question_index",
                                -1,
                            )
                        )

                        if (
                            isinstance(last_evaluation, dict)
                            and last_question_index == current_index
                            and not last_evaluation.get("error")
                        ):

                            st.divider()

                            st.subheader(
                                "📊 AI Feedback"
                            )

                            try:

                                score = float(
                                    last_evaluation.get(
                                        "overall_score",
                                        0,
                                    )
                                )

                                score = min(
                                    max(score, 0.0),
                                    10.0,
                                )

                            except (TypeError, ValueError):

                                score = 0.0

                            st.metric(
                                "🎯 Score",
                                f"{score:.1f} / 10",
                            )

                            st.write(
                                "**Verdict:**",
                                last_evaluation.get(
                                    "verdict",
                                    "Not specified",
                                ),
                            )

                            strengths = last_evaluation.get(
                                "strengths",
                                [],
                            )

                            if strengths:

                                st.write(
                                    "### ✅ Strong Points"
                                )

                                for item in strengths[:3]:

                                    st.markdown(
                                        f"- {item}"
                                    )

                            improvements = last_evaluation.get(
                                "improvements",
                                [],
                            )

                            if improvements:

                                st.write(
                                    "### ⚠️ Improve"
                                )

                                for item in improvements[:3]:

                                    st.markdown(
                                        f"- {item}"
                                    )

                            st.divider()

                            if (
                                current_index + 1
                                < total_questions
                            ):

                                if st.button(
                                    "➡️ Next Question",
                                    type="primary",
                                    use_container_width=True,
                                    key=f"next_mock_question_{current_index}",
                                ):

                                    st.session_state.current_question_index += 1

                                    st.session_state.pop(
                                        "last_interview_evaluation",
                                        None,
                                    )

                                    st.session_state.pop(
                                        "last_interview_question_index",
                                        None,
                                    )

                                    st.rerun()

                            else:

                                if st.button(
                                    "🏁 Finish Interview",
                                    type="primary",
                                    use_container_width=True,
                                    key="finish_mock_interview",
                                ):

                                    st.session_state.current_question_index = (
                                        total_questions
                                    )

                                    st.session_state.interview_completed = True

                                    st.session_state.pop(
                                        "last_interview_evaluation",
                                        None,
                                    )

                                    st.session_state.pop(
                                        "last_interview_question_index",
                                        None,
                                    )

                                    st.rerun()


            # =================================================
            # ANSWER EVALUATION
            # =================================================

            st.divider()

            st.subheader(
                "📝 Practice Your Interview Answer"
            )

            st.write(
                "Enter an interview question and your answer "
                "to receive AI-powered interviewer feedback."
            )


            interview_question = st.text_area(
                "🎤 Interview Question",
                height=120,
                placeholder=(
                    "Example:\n\n"
                    "What is the difference between Django "
                    "and Django REST Framework?"
                ),
            )


            candidate_answer = st.text_area(
                "💬 Your Answer",
                height=220,
                placeholder=(
                    "Type your interview answer here..."
                ),
            )


            evaluate_button = st.button(
                "🤖 Evaluate My Answer",
                type="primary",
                use_container_width=True,
            )


            if evaluate_button:

                if not interview_question.strip():

                    st.warning(
                        "Please enter an interview question."
                    )

                elif not candidate_answer.strip():

                    st.warning(
                        "Please enter your answer."
                    )

                else:

                    with st.spinner(
                        "AI interviewer is evaluating "
                        "your answer..."
                    ):

                        try:

                            evaluation = evaluate_answer(
                                question=interview_question,
                                candidate_answer=candidate_answer,
                                resume_text=resume_text,
                                job_description=job_description,
                            )


                            # =================================================
                            # NORMALIZE EVALUATION RESPONSE
                            # =================================================
                            # The evaluator should return a dict. This safety
                            # layer also handles a JSON string returned by the
                            # model or an older evaluator implementation.

                            import json

                            if isinstance(evaluation, str):

                                raw_evaluation = evaluation.strip()

                                # Remove Markdown code fences if present.
                                if raw_evaluation.startswith("```json"):
                                    raw_evaluation = raw_evaluation[7:]

                                elif raw_evaluation.startswith("```"):
                                    raw_evaluation = raw_evaluation[3:]

                                if raw_evaluation.endswith("```"):
                                    raw_evaluation = raw_evaluation[:-3]

                                raw_evaluation = raw_evaluation.strip()

                                try:
                                    evaluation = json.loads(
                                        raw_evaluation
                                    )
                                except json.JSONDecodeError:
                                    st.error(
                                        "The AI evaluator returned text "
                                        "instead of structured JSON."
                                    )
                                    st.markdown(evaluation)
                                    evaluation = None


                            # =================================================
                            # HANDLE INVALID / ERROR RESPONSE
                            # =================================================

                            if evaluation is None:
                                pass

                            elif not isinstance(evaluation, dict):

                                st.error(
                                    "Answer evaluation returned an "
                                    "unexpected response format."
                                )

                                st.write(
                                    f"Received: {type(evaluation).__name__}"
                                )

                                st.code(str(evaluation))

                            elif evaluation.get("error"):

                                st.error(
                                    "Answer evaluation failed."
                                )

                                st.write(
                                    evaluation["error"]
                                )

                            else:

                                st.success(
                                    "Answer evaluation completed! ✅"
                                )


                                # =============================================
                                # SCORE DASHBOARD
                                # =============================================

                                st.divider()

                                st.subheader(
                                    "🎯 Interview Performance"
                                )


                                # =============================================
                                # GET SCORES SAFELY
                                # =============================================

                                def safe_score(value):
                                    """Convert an AI score to a safe 0–10 float."""
                                    try:
                                        score = float(value)
                                    except (TypeError, ValueError):
                                        return 0.0

                                    return min(
                                        max(score, 0.0),
                                        10.0
                                    )


                                overall_score = safe_score(
                                    evaluation.get(
                                        "overall_score",
                                        0
                                    )
                                )

                                technical_score = safe_score(
                                    evaluation.get(
                                        "technical_correctness",
                                        0
                                    )
                                )

                                relevance_score = safe_score(
                                    evaluation.get(
                                        "relevance",
                                        0
                                    )
                                )

                                completeness_score = safe_score(
                                    evaluation.get(
                                        "completeness",
                                        0
                                    )
                                )

                                clarity_score = safe_score(
                                    evaluation.get(
                                        "clarity",
                                        0
                                    )
                                )


                                # =============================================
                                # OVERALL SCORE
                                # =============================================

                                score_col, verdict_col = st.columns(
                                    [1, 2]
                                )

                                with score_col:

                                    st.metric(
                                        "🏆 Overall Score",
                                        f"{overall_score:.1f} / 10"
                                    )


                                with verdict_col:

                                    verdict = evaluation.get(
                                        "verdict",
                                        "Not specified"
                                    )

                                    st.info(
                                        f"🎯 Interviewer Verdict: **{verdict}**"
                                    )


                                # =============================================
                                # SCORE COLUMNS
                                # =============================================

                                col1, col2, col3, col4 = st.columns(4)


                                with col1:

                                    st.metric(
                                        "Technical Correctness",
                                        f"{technical_score:.1f} / 10"
                                    )

                                    st.progress(
                                        technical_score / 10
                                    )


                                with col2:

                                    st.metric(
                                        "Relevance",
                                        f"{relevance_score:.1f} / 10"
                                    )

                                    st.progress(
                                        relevance_score / 10
                                    )


                                with col3:

                                    st.metric(
                                        "Completeness",
                                        f"{completeness_score:.1f} / 10"
                                    )

                                    st.progress(
                                        completeness_score / 10
                                    )


                                with col4:

                                    st.metric(
                                        "Clarity",
                                        f"{clarity_score:.1f} / 10"
                                    )

                                    st.progress(
                                        clarity_score / 10
                                    )


                                # =============================================
                                # STRENGTHS
                                # =============================================

                                st.divider()

                                st.subheader(
                                    "✅ What You Did Well"
                                )

                                strengths = evaluation.get(
                                    "strengths",
                                    []
                                )

                                if isinstance(strengths, list):

                                    if strengths:

                                        for strength in strengths:

                                            st.markdown(
                                                f"- {strength}"
                                            )

                                    else:

                                        st.write(
                                            "No specific strengths identified."
                                        )

                                else:

                                    st.write(
                                        strengths
                                    )


                                # =============================================
                                # IMPROVEMENTS
                                # =============================================

                                st.subheader(
                                    "⚠️ What You Should Improve"
                                )

                                improvements = evaluation.get(
                                    "improvements",
                                    []
                                )

                                if isinstance(improvements, list):

                                    if improvements:

                                        for improvement in improvements:

                                            st.markdown(
                                                f"- {improvement}"
                                            )

                                    else:

                                        st.write(
                                            "No specific improvements identified."
                                        )

                                else:

                                    st.write(
                                        improvements
                                    )


                                # =============================================
                                # MISSING POINTS
                                # =============================================

                                st.subheader(
                                    "❌ Missing Points"
                                )

                                missing_points = evaluation.get(
                                    "missing_points",
                                    []
                                )

                                if isinstance(missing_points, list):

                                    if missing_points:

                                        for point in missing_points:

                                            st.markdown(
                                                f"- {point}"
                                            )

                                    else:

                                        st.write(
                                            "No major missing points identified."
                                        )

                                else:

                                    st.write(
                                        missing_points
                                    )


                                # =============================================
                                # IDEAL ANSWER
                                # =============================================

                                st.subheader(
                                    "💡 Ideal Answer"
                                )

                                ideal_answer = evaluation.get(
                                    "ideal_answer",
                                    "No ideal answer was generated."
                                )

                                st.info(
                                    ideal_answer
                                )


                        except Exception as e:

                            st.error(
                                "Answer evaluation failed."
                            )

                            st.exception(e)


    except Exception as e:

        st.error(
            f"An error occurred while processing "
            f"the resume: {e}"
        )