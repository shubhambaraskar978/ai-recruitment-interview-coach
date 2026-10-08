import { useEffect, useState } from "react";
import {
  ArrowRight,
  Check,
  CircleHelp,
  Clock3,
  Download,
  FileText,
  LoaderCircle,
  MessageSquareText,
  Sparkles,
  Target,
} from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { interviewService } from "../services/api";
import {
  Button,
  EmptyState,
  ErrorNotice,
  Loader,
  Markdown,
  PageHeading,
  Panel,
  ScoreRing,
  SectionTitle,
} from "../components/UI";

export function InterviewPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { session, setSession, refreshAccountData } = useApp();
  const [interview, setInterview] = useState(
    session.interview?.id === id ? session.interview : null,
  );
  const [answer, setAnswer] = useState("");
  const [evaluation, setEvaluation] = useState(session.evaluation || null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    interviewService
      .get(id)
      .then((value) => {
        if (active) {
          setInterview(value);
          if (value.current_evaluation) setEvaluation(value.current_evaluation);
        }
      })
      .catch((requestError) => {
        if (active) setError(requestError.message);
      });
    return () => {
      active = false;
    };
  }, [id]);

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await interviewService.submitAnswer(id, answer);
      setEvaluation(result.evaluation);
      setSession({
        evaluation: result.evaluation,
        interview: { ...interview, current_evaluation: result.evaluation },
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const skipQuestion = async () => {
    setBusy(true);
    setError("");
    try {
      const value = await interviewService.skip(id);
      setInterview(value);
      setAnswer("");
      setEvaluation(null);
      setSession({ interview: value, evaluation: null });
      if (value.status === "complete") {
        const details = await interviewService.report(id);
        setSession({
          report: details.report,
          reportDetails: details,
          interview: value,
        });
        await refreshAccountData();
        navigate(`/interview/${id}/results`);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const next = async () => {
    setBusy(true);
    setError("");
    try {
      const value = await interviewService.next(id);
      setInterview(value);
      setAnswer("");
      setEvaluation(null);
      setSession({ interview: value, evaluation: null });
      if (value.status === "complete") {
        const details = await interviewService.report(id);
        setSession({
          report: details.report,
          reportDetails: details,
          interview: value,
        });
        await refreshAccountData();
        navigate(`/interview/${id}/results`);
      }
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  const endEarly = async () => {
    if (
      !window.confirm(
        "End this interview and create a report from the answers you have submitted? Unanswered questions will not be evaluated.",
      )
    )
      return;
    setBusy(true);
    setError("");
    try {
      const value = await interviewService.complete(id);
      const details = await interviewService.report(id);
      setSession({
        interview: value,
        report: details.report,
        reportDetails: details,
      });
      await refreshAccountData();
      navigate(`/interview/${id}/results`);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  if (error && !interview)
    return (
      <>
        <PageHeading
          title="Interview unavailable"
          description="We couldn't reopen this session."
        />
        <Panel>
          <ErrorNotice message={error} />
          <Link className="button button-secondary" to="/interview/setup">
            Create a new interview
          </Link>
        </Panel>
      </>
    );
  if (!interview) return <Loader label="Loading your interview" />;
  const progress = Math.min(
    (interview.completed_answers / interview.total_questions) * 100,
    100,
  );

  return (
    <>
      <PageHeading
        eyebrow="AI MOCK INTERVIEW"
        title="Your practice session"
        description="Take a breath. There’s no timer, and you can take a moment to think."
        action={
          <div className="interview-heading-actions">
            <span className="session-live">
              <span className="online-dot" /> IN PROGRESS
            </span>
            {interview.answered_questions > 0 && (
              <Button variant="secondary" onClick={endEarly} disabled={busy}>
                End early
              </Button>
            )}
          </div>
        }
      />
      <div className="interview-layout">
        <div className="interview-main">
          <Panel className="question-panel">
            <div className="question-meta">
              <span>
                <MessageSquareText size={15} /> QUESTION{" "}
                {interview.current_question_index + 1} OF{" "}
                {interview.total_questions}
              </span>
              <span>
                <Clock3 size={15} /> TAKE YOUR TIME
              </span>
            </div>
            <div className="question-number">
              {String(interview.current_question_index + 1).padStart(2, "0")}
            </div>
            <h2>{interview.question}</h2>
            <div className="question-prompt">
              <Sparkles size={15} />
              <span>
                Answer as you would in a real conversation. Specific examples
                can help.
              </span>
            </div>
          </Panel>
          {!evaluation ? (
            <Panel className="answer-panel">
              <form onSubmit={submit}>
                <label className="field-label" htmlFor="answer">
                  Your answer
                </label>
                <textarea
                  id="answer"
                  value={answer}
                  onChange={(event) => setAnswer(event.target.value)}
                  rows={9}
                  maxLength={20000}
                  placeholder="Start wherever feels natural. You can structure your answer as you go…"
                  required
                />
                <div className="textarea-meta">
                  <span>
                    {answer.length.toLocaleString()} / 20,000 characters
                  </span>
                  <span>Autosaved in this tab after evaluation</span>
                </div>
                {error && (
                  <ErrorNotice message={error} onRetry={() => setError("")} />
                )}
                <div className="answer-actions">
                  <span className="voice-note">
                    <CircleHelp size={15} /> Voice input is not available in
                    this version.
                  </span>
                  <Button
                    variant="secondary"
                    type="button"
                    onClick={skipQuestion}
                    disabled={busy}
                  >
                    Skip question
                  </Button>
                  <Button type="submit" disabled={busy || !answer.trim()}>
                    {busy ? (
                      <>
                        <LoaderCircle className="spin" size={16} /> Evaluating…
                      </>
                    ) : (
                      <>
                        Submit answer <ArrowRight size={15} />
                      </>
                    )}
                  </Button>
                </div>
              </form>
            </Panel>
          ) : (
            <Panel className="evaluation-panel">
              <div className="evaluation-heading">
                <div>
                  <span className="eyebrow">YOUR ANSWER, REVIEWED</span>
                  <h2>Thoughtful feedback</h2>
                </div>
                <ScoreRing
                  score={evaluation.overall_score}
                  max={10}
                  label="answer"
                  size="small"
                />
              </div>
              <span className="verdict-chip">{evaluation.verdict}</span>
              <div className="evaluation-scores">
                {[
                  ["Technical accuracy", evaluation.technical_correctness],
                  ["Relevance", evaluation.relevance],
                  ["Completeness", evaluation.completeness],
                  ["Clarity", evaluation.clarity],
                ].map(([label, score]) => (
                  <div className="evaluation-score" key={label}>
                    <span>{label}</span>
                    <div className="score-track">
                      <i
                        style={{
                          width: `${Math.max(0, Math.min(100, Number(score) * 10))}%`,
                        }}
                      />
                    </div>
                    <strong>{score}/10</strong>
                  </div>
                ))}
              </div>
              <div className="feedback-columns">
                <div>
                  <h3>
                    <Check size={15} /> What worked
                  </h3>
                  {(evaluation.strengths || []).map((item) => (
                    <p key={item}>{item}</p>
                  ))}
                </div>
                <div>
                  <h3>
                    <Target size={15} /> To make it stronger
                  </h3>
                  {(evaluation.improvements || []).map((item) => (
                    <p key={item}>{item}</p>
                  ))}
                </div>
              </div>
              {evaluation.missing_points?.length > 0 && (
                <div className="missing-points">
                  <strong>Points to consider</strong>
                  <span>{evaluation.missing_points.join(" · ")}</span>
                </div>
              )}
              {error && (
                <ErrorNotice message={error} onRetry={() => setError("")} />
              )}
              <div className="evaluation-next">
                <span>
                  Feedback is based on your answer, not a generic rubric.
                </span>
                <Button onClick={next} disabled={busy}>
                  {busy
                    ? "Preparing…"
                    : interview.current_question_index + 1 >=
                        interview.total_questions
                      ? "Complete interview"
                      : "Next question"}
                  <ArrowRight size={15} />
                </Button>
              </div>
            </Panel>
          )}
        </div>
        <aside className="interview-aside">
          <Panel className="progress-panel">
            <SectionTitle>Your progress</SectionTitle>
            <div className="progress-count">
              <strong>{interview.completed_answers}</strong>
              <span>of {interview.total_questions} answered</span>
            </div>
            <div className="progress-track">
              <i style={{ width: `${progress}%` }} />
            </div>
            <div className="question-list">
              {Array.from({ length: interview.total_questions }, (_, index) => (
                <div
                  className={`question-list-item ${index === interview.current_question_index ? "question-current" : ""} ${index < interview.completed_answers ? "question-done" : ""}`}
                  key={index}
                >
                  <span>
                    {index < interview.completed_answers ? (
                      <Check size={13} />
                    ) : (
                      String(index + 1).padStart(2, "0")
                    )}
                  </span>
                  <span>
                    {index < interview.completed_answers
                      ? "Answered"
                      : index === interview.current_question_index
                        ? "Current question"
                        : "Up next"}
                  </span>
                </div>
              ))}
            </div>
          </Panel>
          <div className="interview-aside-note">
            <Sparkles size={16} />
            <p>
              <strong>There’s no perfect answer.</strong>
              <br />
              This is a space to think clearly, try an approach, and learn from
              it.
            </p>
          </div>
        </aside>
      </div>
    </>
  );
}

export function ResultsPage() {
  const { id } = useParams();
  const { session, setSession } = useApp();
  const [details, setDetails] = useState(session.reportDetails || null);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    interviewService
      .report(id)
      .then((value) => {
        if (active) {
          setDetails(value);
          setSession({ reportDetails: value, report: value.report });
        }
      })
      .catch((requestError) => {
        if (active) setError(requestError.message);
      });
    return () => {
      active = false;
    };
  }, [id]);

  if (!details && error)
    return (
      <>
        <PageHeading
          title="Report unavailable"
          description="This session may have expired after a backend restart."
        />
        <Panel>
          <ErrorNotice message={error} />
          <Link className="button button-secondary" to="/interview/setup">
            Start a new interview
          </Link>
        </Panel>
      </>
    );
  if (!details) return <Loader label="Preparing your interview report" />;
  const report = details.report;
  const downloadReport = () => {
    const content = [
      "AI Interview Coach — Interview Performance",
      "",
      `Overall score: ${report.overall_score}/10`,
      `Hiring readiness: ${report.hiring_readiness}/100`,
      `Recommendation: ${report.hiring_recommendation}`,
      "",
      "Summary",
      report.interviewer_summary,
      "",
      "Strengths",
      ...(report.strengths || []).map((item) => `- ${item}`),
      "",
      "Areas to improve",
      ...(report.weaknesses || []).map((item) => `- ${item}`),
      "",
      ...details.questions.flatMap((question, index) => [
        `Question ${index + 1}: ${question}`,
        `Answer: ${details.answers[index] || (details.skipped_questions?.includes(index) ? "Skipped" : "Not answered")}`,
        `Score: ${details.evaluations[index]?.overall_score ?? "—"}/10`,
        `Feedback: ${(details.evaluations[index]?.improvements || []).join(" ")}`,
        "",
      ]),
    ].join("\n");
    const link = document.createElement("a");
    link.href = URL.createObjectURL(
      new Blob([content], { type: "text/plain;charset=utf-8" }),
    );
    link.download = "interview-report.txt";
    link.click();
    URL.revokeObjectURL(link.href);
  };

  return (
    <>
      <PageHeading
        eyebrow="PRACTICE COMPLETE"
        title="Interview performance"
        description="A grounded review of your answers and the areas to build on."
        action={
          <div className="report-actions">
            <Button variant="secondary" onClick={downloadReport}>
              <Download size={15} /> Download report
            </Button>
            <Link className="button button-primary" to="/interview/setup">
              Practice again <ArrowRight size={15} />
            </Link>
          </div>
        }
      />
      <div className="report-hero">
        <div className="report-score">
          <ScoreRing score={report.overall_score} max={10} label="overall" />
          <div>
            <span className="eyebrow">OVERALL PERFORMANCE</span>
            <h2>{report.hiring_recommendation}</h2>
            <p>{report.interviewer_summary}</p>
          </div>
        </div>
        <div className="readiness-score">
          <strong>
            {report.hiring_readiness}
            <small>/100</small>
          </strong>
          <span>Hiring readiness</span>
          <div className="score-track">
            <i style={{ width: `${report.hiring_readiness}%` }} />
          </div>
        </div>
      </div>
      <div className="report-metrics">
        {[
          ["Technical", report.technical_score],
          ["Communication", report.communication_score],
          ["Job fit", report.job_fit_score],
        ].map(([label, score]) => (
          <Panel className="report-metric" key={label}>
            <span>{label}</span>
            <strong>
              {score}
              <small>/10</small>
            </strong>
            <div className="score-track">
              <i style={{ width: `${Number(score) * 10}%` }} />
            </div>
          </Panel>
        ))}
      </div>
      <div className="report-columns">
        <Panel className="report-observations">
          <SectionTitle>What stood out</SectionTitle>
          <div className="report-list-good">
            {(report.strengths || []).map((item) => (
              <p key={item}>
                <Check size={15} />
                {item}
              </p>
            ))}
          </div>
          <SectionTitle>Where to focus</SectionTitle>
          <div className="report-list-focus">
            {(report.weaknesses || []).map((item) => (
              <p key={item}>
                <Target size={15} />
                {item}
              </p>
            ))}
          </div>
        </Panel>
        <Panel className="report-summary">
          <SectionTitle>Coach’s summary</SectionTitle>
          <div>
            <strong>Technical assessment</strong>
            <p>{report.technical_assessment}</p>
          </div>
          <div>
            <strong>Communication</strong>
            <p>{report.communication_assessment}</p>
          </div>
          <div>
            <strong>Job fit</strong>
            <p>{report.job_fit_assessment}</p>
          </div>
        </Panel>
      </div>
      <Panel className="question-results">
        <SectionTitle>Answer-by-answer</SectionTitle>
        {details.questions.map((question, index) => {
          const evaluation = details.evaluations[index] || {};
          const skipped = details.skipped_questions?.includes(index);
          return (
            <details className="answer-result" key={`${index}-${question}`}>
              <summary>
                <span className="answer-result-number">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="answer-result-question">{question}</span>
                <span className="answer-result-score">
                  {evaluation.overall_score ?? (skipped ? "Skipped" : "—")}
                  {evaluation.overall_score !== undefined ? "/10" : ""}
                </span>
              </summary>
              <div className="answer-result-body">
                <div>
                  <strong>Your answer</strong>
                  <p>
                    {details.answers[index] ||
                      (skipped ? "Skipped" : "Not answered")}
                  </p>
                </div>
                <div>
                  <strong>AI feedback</strong>
                  <p>
                    {skipped
                      ? "Not evaluated"
                      : (evaluation.strengths || []).join(" ")}
                  </p>
                  {(evaluation.improvements || []).map((item) => (
                    <p key={item}>{item}</p>
                  ))}
                </div>
              </div>
            </details>
          );
        })}
      </Panel>
      <div className="next-step-strip">
        <div>
          <strong>Carry one insight into your next practice.</strong>
          <span>
            {(report.recommended_topics || []).slice(0, 2).join(" · ") ||
              "Keep building on what you learned."}
          </span>
        </div>
        <Link className="button button-primary" to="/interview/setup">
          Practice again <ArrowRight size={15} />
        </Link>
      </div>
    </>
  );
}
