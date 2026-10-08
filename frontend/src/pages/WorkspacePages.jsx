import { useRef, useState } from "react";
import {
  ArrowRight,
  Check,
  ClipboardCheck,
  FileText,
  FileUp,
  FileUser,
  MessageSquareText,
  ShieldCheck,
  Sparkles,
  Target,
  Upload,
  X,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import {
  interviewService,
  jobMatchService,
  resumeService,
} from "../services/api";
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

const formatSize = (bytes) =>
  bytes < 1024 * 1024
    ? `${(bytes / 1024).toFixed(0)} KB`
    : `${(bytes / 1024 / 1024).toFixed(1)} MB`;
const formatDate = (value) => {
  const normalized = value.endsWith("Z")
    ? value
    : `${value.replace(" ", "T")}Z`;
  return new Date(normalized).toLocaleDateString();
};

export function DashboardPage() {
  const { session } = useApp();
  const hasResume = Boolean(session.resumeText);
  const hasReport = Boolean(session.report);
  const interviews = session.interviews || [];
  const resumeAnalyses = session.resumeAnalyses || [];
  const jobMatches = session.jobMatches || [];
  const completedInterviews = interviews.filter(
    (interview) => interview.status === "complete",
  );
  return (
    <>
      <PageHeading
        eyebrow="YOUR PRACTICE SPACE"
        title="Your interview preparation"
        description="A quieter, more focused way to get ready for the conversations ahead."
        action={
          <Link className="button button-primary" to="/interview/setup">
            New practice <ArrowRight size={16} />
          </Link>
        }
      />
      <div className="welcome-band">
        <div>
          <span className="welcome-mark">
            <Sparkles size={19} />
          </span>
          <div>
            <p className="eyebrow">A GOOD PLACE TO BEGIN</p>
            <h2>
              {hasResume
                ? "Your preparation is taking shape."
                : "Start with what makes you, you."}
            </h2>
            <p>
              {hasResume
                ? "Your resume is ready. Add a role and build a focused practice session."
                : "Upload your resume, add a role, and let’s make practice personal."}
            </p>
          </div>
        </div>
        <Link className="text-link" to={hasResume ? "/job-match" : "/resume"}>
          {hasResume ? "Match a role" : "Add resume"}
          <ArrowRight size={15} />
        </Link>
      </div>
      <div className="stats-grid">
        <Panel className="stat-panel">
          <span className="stat-icon">
            <FileUser size={18} />
          </span>
          <span className="stat-label">Resume status</span>
          <strong>{hasResume ? "Analyzed" : "Not added"}</strong>
          <small>
            {hasResume
              ? "Ready for role matching"
              : "Upload a PDF to get started"}
          </small>
        </Panel>
        <Panel className="stat-panel">
          <span className="stat-icon stat-icon-mint">
            <Target size={18} />
          </span>
          <span className="stat-label">Job match</span>
          <strong>{session.jobMatch ? "Complete" : "Not started"}</strong>
          <small>
            {session.jobMatch
              ? "Your latest role comparison"
              : "Compare your resume to a role"}
          </small>
        </Panel>
        <Panel className="stat-panel">
          <span className="stat-icon stat-icon-yellow">
            <ClipboardCheck size={18} />
          </span>
          <span className="stat-label">Interviews completed</span>
          <strong>{completedInterviews.length}</strong>
          <small>
            {session.practiceHistoryCount || 0} practice responses saved
          </small>
        </Panel>
        <Panel className="stat-panel">
          <span className="stat-icon stat-icon-peach">
            <Sparkles size={18} />
          </span>
          <span className="stat-label">Latest report</span>
          <strong>
            {hasReport ? `${session.report.overall_score}/10` : "—"}
          </strong>
          <small>
            {hasReport
              ? "Generated from your answers"
              : "Appears after your first interview"}
          </small>
        </Panel>
      </div>
      <div className="dashboard-columns">
        <Panel className="dashboard-main">
          <SectionTitle>
            Continue preparing{" "}
            <span className="subtle-chip">YOUR WORKFLOW</span>
          </SectionTitle>
          <div className="workflow-list">
            {[
              [
                FileUp,
                "01",
                "Analyze your resume",
                hasResume
                  ? "Your resume has been analyzed"
                  : "See your experience clearly",
                "/resume",
                hasResume ? "Review analysis" : "Upload resume",
                hasResume,
              ],
              [
                Target,
                "02",
                "Compare a job description",
                session.jobMatch
                  ? "Latest comparison is ready"
                  : "Find the overlap and the gaps",
                "/job-match",
                "Check your fit",
                Boolean(session.jobMatch),
              ],
              [
                MessageSquareText,
                "03",
                "Practice a tailored interview",
                hasReport
                  ? "Review your latest interview"
                  : "Questions shaped around your experience",
                hasReport
                  ? `/interview/${session.interviewId}/results`
                  : "/interview/setup",
                hasReport ? "View report" : "Build interview",
                hasReport,
              ],
            ].map(([Icon, number, title, description, href, action, done]) => (
              <div className="workflow-row" key={number}>
                <span
                  className={`workflow-icon ${done ? "workflow-done" : ""}`}
                >
                  {done ? <Check size={17} /> : <Icon size={17} />}
                </span>
                <div className="workflow-copy">
                  <span>{number}</span>
                  <strong>{title}</strong>
                  <small>{description}</small>
                </div>
                <Link className="workflow-action" to={href}>
                  {action}
                  <ArrowRight size={14} />
                </Link>
              </div>
            ))}
          </div>
        </Panel>
        <Panel className="readiness-panel">
          <SectionTitle>Readiness</SectionTitle>
          <div className="readiness-empty">
            <div className="readiness-orbit">
              <div>
                <Sparkles size={21} />
                <strong>{hasReport ? "1" : "0"}</strong>
              </div>
            </div>
            <strong>
              {hasReport ? "First report complete" : "Built as you practice"}
            </strong>
            <p>
              There is no readiness score yet. We’ll use completed practice
              reports to help you see what to focus on.
            </p>
            <Link className="text-link" to="/analytics">
              View progress <ArrowRight size={14} />
            </Link>
          </div>
        </Panel>
      </div>
      <Panel className="activity-panel">
        <SectionTitle>
          Recent activity <span className="subtle-chip">YOUR ACCOUNT</span>
        </SectionTitle>
        {interviews.length ? (
          <div className="account-activity-list">
            {interviews.slice(0, 8).map((interview) => {
              const isComplete = interview.status === "complete";
              const href = isComplete
                ? `/interview/${interview.id}/results`
                : `/interview/${interview.id}`;
              return (
                <div className="activity-line" key={interview.id}>
                  <span className="activity-dot" />
                  <div>
                    <strong>
                      {isComplete
                        ? "Interview practice completed"
                        : "Interview practice in progress"}
                    </strong>
                    <small>
                      {formatDate(interview.created_at)}
                      {interview.overall_score != null &&
                        ` · Score ${interview.overall_score}/10`}
                    </small>
                  </div>
                  <Link className="text-link" to={href}>
                    {isComplete ? "View report" : "Continue"}
                    <ArrowRight size={14} />
                  </Link>
                </div>
              );
            })}
          </div>
        ) : (
          <EmptyState
            icon={ClipboardCheck}
            title="Your activity will appear here"
          >
            Your interview sessions and reports are saved to your account.
          </EmptyState>
        )}
      </Panel>
      {(resumeAnalyses.length > 0 || jobMatches.length > 0) && (
        <Panel className="saved-data-panel">
          <SectionTitle>
            Saved analyses <span className="subtle-chip">YOUR ACCOUNT</span>
          </SectionTitle>
          {resumeAnalyses.length > 0 && (
            <div className="saved-analysis-group">
              <h3>Resume analyses</h3>
              {resumeAnalyses.map((item) => (
                <details className="saved-analysis-item" key={item.id}>
                  <summary>
                    <strong>{item.filename}</strong>
                    <span>
                      {formatDate(item.created_at)}
                    </span>
                  </summary>
                  <Markdown>{item.analysis}</Markdown>
                </details>
              ))}
            </div>
          )}
          {jobMatches.length > 0 && (
            <div className="saved-analysis-group">
              <h3>Role matches</h3>
              {jobMatches.map((item) => (
                <details className="saved-analysis-item" key={item.id}>
                  <summary>
                    <strong>
                      {item.job_description.slice(0, 90)}
                      {item.job_description.length > 90 ? "…" : ""}
                    </strong>
                    <span>
                      {formatDate(item.created_at)}
                    </span>
                  </summary>
                  <Markdown>{item.analysis}</Markdown>
                </details>
              ))}
            </div>
          )}
        </Panel>
      )}
    </>
  );
}

export function ResumePage() {
  const { session, setSession } = useApp();
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [dragging, setDragging] = useState(false);

  const chooseFile = (candidate) => {
    setError("");
    if (!candidate) return;
    if (
      candidate.type !== "application/pdf" &&
      !candidate.name.toLowerCase().endsWith(".pdf")
    )
      return setError("Choose a PDF file to continue.");
    if (candidate.size > 8 * 1024 * 1024)
      return setError("This PDF is larger than the 8 MB limit.");
    setFile(candidate);
  };

  const analyze = async () => {
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const result = await resumeService.analyze(file);
      setSession({
        resumeText: result.resume_text,
        resumeAnalysis: result.analysis,
        resumeName: file.name,
        jobMatch: null,
        jobDescription: "",
        resumeAnalyses: [
          {
            id: result.id,
            filename: result.filename,
            analysis: result.analysis,
            created_at: new Date().toISOString(),
          },
          ...(session.resumeAnalyses || []),
        ],
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <PageHeading
        eyebrow="YOUR EXPERIENCE, CLEARER"
        title="AI resume analysis"
        description="Understand how your experience reads before you walk into the room."
      />
      {!session.resumeAnalysis && (
        <Panel className="upload-panel">
          <div className="upload-heading">
            <span className="section-icon">
              <FileUser size={18} />
            </span>
            <div>
              <h2>Upload your resume</h2>
              <p>We’ll extract the text and return an AI-written analysis.</p>
            </div>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="application/pdf,.pdf"
            hidden
            onChange={(event) => chooseFile(event.target.files?.[0])}
          />
          {!file ? (
            <button
              className={`dropzone ${dragging ? "dropzone-active" : ""}`}
              onClick={() => inputRef.current?.click()}
              onDragOver={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                chooseFile(event.dataTransfer.files?.[0]);
              }}
            >
              <span className="dropzone-icon">
                <Upload size={21} />
              </span>
              <strong>
                Drop your PDF here, or <u>browse files</u>
              </strong>
              <span>PDF format · Maximum 8 MB</span>
            </button>
          ) : (
            <div className="file-selected">
              <span className="file-icon">
                <FileText size={20} />
              </span>
              <div>
                <strong>{file.name}</strong>
                <small>{formatSize(file.size)} · PDF document</small>
              </div>
              <button
                className="icon-button"
                aria-label="Remove selected PDF"
                onClick={() => setFile(null)}
              >
                <X size={17} />
              </button>
            </div>
          )}
          {error && (
            <ErrorNotice message={error} onRetry={() => setError("")} />
          )}
          {file && (
            <div className="upload-actions">
              <span className="muted">
                Your PDF is sent to your configured AI backend for analysis.
              </span>
              <Button onClick={analyze} disabled={busy}>
                {busy ? "Analyzing…" : "Analyze resume"}
                <Sparkles size={16} />
              </Button>
            </div>
          )}
          {busy && (
            <div className="analysis-progress">
              <Loader label="AI is analyzing your resume" />
              <div className="analysis-steps">
                <span>
                  <Check size={13} /> Extracting text
                </span>
                <span className="step-current">
                  <Sparkles size={13} /> Reviewing experience
                </span>
                <span>Preparing insights</span>
              </div>
            </div>
          )}
          <p className="privacy-note">
            <ShieldCheck size={14} /> The original PDF is not retained. Your
            extracted resume text and analysis are saved to your account.
          </p>
        </Panel>
      )}
      {session.resumeAnalysis && (
        <>
          <div className="result-banner">
            <div className="result-file">
              <span className="file-icon">
                <FileText size={19} />
              </span>
              <div>
                <strong>{session.resumeName || "Resume analyzed"}</strong>
                <small>Analysis completed · Text extracted successfully</small>
              </div>
            </div>
            <Button
              variant="secondary"
              onClick={() => {
                setSession({
                  resumeText: null,
                  resumeAnalysis: null,
                  resumeName: null,
                  jobMatch: null,
                });
                setFile(null);
              }}
            >
              Analyze another
            </Button>
          </div>
          <Panel className="analysis-panel">
            <div className="analysis-result-title">
              <div>
                <span className="eyebrow">YOUR RESUME, REVIEWED</span>
                <h2>Resume insights</h2>
              </div>
              <span className="result-source">
                <Sparkles size={14} /> AI-generated analysis
              </span>
            </div>
            <Markdown>{session.resumeAnalysis}</Markdown>
          </Panel>
          <div className="next-step-strip">
            <div>
              <strong>Ready to connect your experience to a role?</strong>
              <span>Compare this resume with a job description.</span>
            </div>
            <Link className="button button-primary" to="/job-match">
              Match a role <ArrowRight size={15} />
            </Link>
          </div>
        </>
      )}
      {!session.resumeAnalysis && !busy && (
        <div className="privacy-footnote">
          <strong>Good to know</strong>
          <span>
            Scanned or image-only PDFs may not contain extractable text. A
            text-based PDF gives the best results.
          </span>
        </div>
      )}
    </>
  );
}

export function JobMatchPage() {
  const { session, setSession } = useApp();
  const [description, setDescription] = useState(session.jobDescription || "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const analyze = async (event) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await jobMatchService.analyze(
        session.resumeText,
        description,
      );
      setSession({
        jobDescription: description,
        jobMatch: result.analysis,
        jobMatches: [
          {
            id: Date.now(),
            job_description: description,
            analysis: result.analysis,
            created_at: new Date().toISOString(),
          },
          ...(session.jobMatches || []),
        ],
      });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageHeading
        eyebrow="RESUME + OPPORTUNITY"
        title="Resume & job match"
        description="Compare what you’ve done with what the role is asking for."
      />
      {!session.resumeText && (
        <Panel className="prerequisite-panel">
          <EmptyState icon={FileUser} title="Add your resume first">
            The matching service needs extracted resume text to compare against
            a job description.
            <Button onClick={() => navigate("/resume")}>
              Go to resume analysis <ArrowRight size={15} />
            </Button>
          </EmptyState>
        </Panel>
      )}
      {session.resumeText && (
        <>
          <Panel className="match-form-panel">
            <div className="match-context">
              <span className="context-chip">
                <FileText size={14} /> {session.resumeName || "Resume added"}
              </span>
              <span className="context-arrow">+</span>
              <span className="context-chip context-chip-role">
                <Target size={14} /> Target role
              </span>
            </div>
            <form onSubmit={analyze}>
              <label className="field-label" htmlFor="job-description">
                Paste the job description
              </label>
              <textarea
                id="job-description"
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Paste the responsibilities, qualifications and skills from the job posting…"
                rows={9}
                required
                maxLength={50000}
              />
              <div className="textarea-meta">
                <span>
                  Include the full description for a more useful comparison.
                </span>
                <span>{description.length.toLocaleString()} / 50,000</span>
              </div>
              {error && (
                <ErrorNotice message={error} onRetry={() => setError("")} />
              )}
              <div className="form-footer">
                <span className="muted">
                  <Sparkles size={14} /> Comparison is generated by your AI
                  backend.
                </span>
                <Button type="submit" disabled={busy || !description.trim()}>
                  {busy ? "Comparing…" : "Analyze job match"}
                  <ArrowRight size={15} />
                </Button>
              </div>
            </form>
          </Panel>
          {busy && (
            <Panel className="busy-panel">
              <Loader label="Comparing your resume with the role" />
            </Panel>
          )}
          {session.jobMatch && !busy && (
            <Panel className="match-result">
              <div className="analysis-result-title">
                <div>
                  <span className="eyebrow">ROLE COMPARISON</span>
                  <h2>Your match analysis</h2>
                </div>
                <span className="result-source">
                  <Sparkles size={14} /> Based on your resume & description
                </span>
              </div>
              <Markdown>{session.jobMatch}</Markdown>
              <div className="next-step-strip">
                <div>
                  <strong>Make the next step a practice round.</strong>
                  <span>
                    Build an interview using your resume and this job
                    description.
                  </span>
                </div>
                <Button onClick={() => navigate("/interview/setup")}>
                  Prepare for this role <ArrowRight size={15} />
                </Button>
              </div>
            </Panel>
          )}
        </>
      )}
    </>
  );
}

export function SetupPage() {
  const { session, setSession } = useApp();
  const [count, setCount] = useState(5);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();
  const canStart = Boolean(
    session.resumeText && session.jobDescription?.trim(),
  );
  const start = async () => {
    setBusy(true);
    setError("");
    try {
      const interview = await interviewService.create({
        resume_text: session.resumeText,
        job_description: session.jobDescription,
        number_of_questions: count,
      });
      setSession({
        interviewId: interview.id,
        interview,
        report: null,
        reportDetails: null,
        evaluation: null,
      });
      navigate(`/interview/${interview.id}`);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageHeading
        eyebrow="A PRACTICE SESSION, BUILT FOR YOU"
        title="Create your AI interview"
        description="Questions will be generated from your resume and the job description you provide."
      />
      {!canStart && (
        <Panel className="prerequisite-panel">
          <EmptyState icon={ClipboardCheck} title="Two things before we begin">
            Add a resume and a job description. The interview generator uses
            both to create the questions.
            <div className="prerequisite-actions">
              <Button variant="secondary" onClick={() => navigate("/resume")}>
                Add resume
              </Button>
              <Button
                onClick={() =>
                  navigate(session.resumeText ? "/job-match" : "/resume")
                }
              >
                Add job description <ArrowRight size={15} />
              </Button>
            </div>
          </EmptyState>
        </Panel>
      )}
      {canStart && (
        <div className="setup-layout">
          <Panel className="setup-panel">
            <div className="setup-panel-heading">
              <span className="section-icon">
                <MessageSquareText size={18} />
              </span>
              <div>
                <h2>Shape your session</h2>
                <p>
                  The question count is the only interview setting currently
                  supported by the generator.
                </p>
              </div>
            </div>
            <label className="field-label" htmlFor="question-count">
              Questions
            </label>
            <div className="count-options">
              {[5, 10, 15, 20].map((value) => (
                <button
                  key={value}
                  className={`count-option ${count === value ? "count-selected" : ""}`}
                  onClick={() => setCount(value)}
                  type="button"
                >
                  <strong>{value}</strong>
                  <span>questions</span>
                </button>
              ))}
            </div>
            {error && (
              <ErrorNotice message={error} onRetry={() => setError("")} />
            )}
            <div className="setup-footer">
              <span>
                <ShieldCheck size={15} /> Your resume and job description ground
                every question.
              </span>
              <Button onClick={start} disabled={busy}>
                {busy ? "Preparing…" : "Generate interview"}
                <Sparkles size={15} />
              </Button>
            </div>
            {busy && (
              <Loader label="AI is preparing your personalized interview" />
            )}
          </Panel>
          <Panel className="session-summary">
            <span className="eyebrow">SESSION CONTEXT</span>
            <h2>What the coach knows</h2>
            <div className="summary-item">
              <span className="summary-icon">
                <FileText size={16} />
              </span>
              <div>
                <small>RESUME</small>
                <strong>{session.resumeName || "Resume provided"}</strong>
              </div>
              <Check size={16} />
            </div>
            <div className="summary-item">
              <span className="summary-icon summary-job">
                <Target size={16} />
              </span>
              <div>
                <small>JOB DESCRIPTION</small>
                <strong>
                  {session.jobDescription.length.toLocaleString()} characters
                  provided
                </strong>
              </div>
              <Check size={16} />
            </div>
            <div className="summary-count">
              <strong>{count}</strong>
              <span>personalized questions</span>
            </div>
            <p>
              Generated questions and reports come from your configured AI
              services, not sample content.
            </p>
          </Panel>
        </div>
      )}
    </>
  );
}
