import {
  Activity,
  ArrowRight,
  BriefcaseBusiness,
  Check,
  FileUser,
  LockKeyhole,
  Moon,
  ShieldCheck,
  Sun,
} from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { EmptyState, PageHeading, Panel, SectionTitle } from "../components/UI";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from "recharts";

export function AnalyticsPage() {
  const { session } = useApp();
  const hasReport = Boolean(session.report && session.reportDetails);
  const practiceHistory = session.practiceHistory || [];
  const chartData = hasReport
    ? session.reportDetails.evaluations
        .filter((item) => Number.isFinite(Number(item.overall_score)))
        .map((item, index) => ({
        name: `Q${index + 1}`,
        score: Number(item.overall_score) || 0,
        }))
    : [];
  return (
    <>
      <PageHeading
        eyebrow="LEARN FROM EVERY REP"
        title="Your progress"
        description="Your account’s completed sessions and saved practice history."
      />
      {!hasReport ? (
        <Panel className="analytics-empty">
          <EmptyState
            icon={Activity}
            title="Your progress starts with a first interview"
          >
            Complete a practice session to see your reports and answer history.
            <Link className="button button-primary" to="/interview/setup">
              Build an interview <ArrowRight size={15} />
            </Link>
          </EmptyState>
        </Panel>
      ) : (
        <>
          <div className="analytics-stats">
            <Panel>
              <small>COMPLETED INTERVIEWS</small>
              <strong>
                {session.interviews?.filter(
                  (interview) => interview.status === "complete",
                ).length || 0}
              </strong>
              <span>Saved to your account</span>
            </Panel>
            <Panel>
              <small>AVERAGE ANSWER SCORE</small>
              <strong>
                {(
                  chartData.reduce((sum, item) => sum + item.score, 0) /
                  Math.max(chartData.length, 1)
                ).toFixed(1)}
                <em>/10</em>
              </strong>
              <span>Across {chartData.length} answers</span>
            </Panel>
            <Panel>
              <small>BEST ANSWER</small>
              <strong>
                {Math.max(...chartData.map((item) => item.score)).toFixed(1)}
                <em>/10</em>
              </strong>
              <span>From your latest report</span>
            </Panel>
            <Panel>
              <small>QUESTIONS ANSWERED</small>
              <strong>{chartData.length}</strong>
              <span>Across your latest report</span>
            </Panel>
          </div>
          <Panel className="analytics-chart">
            <SectionTitle>
              Answer scores{" "}
              <span className="subtle-chip">LATEST REPORT</span>
            </SectionTitle>
            <p>
              Individual answer evaluations from your most recently completed
              practice.
            </p>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={chartData}
                  margin={{ top: 10, right: 16, bottom: 0, left: -20 }}
                >
                  <CartesianGrid
                    strokeDasharray="3 3"
                    vertical={false}
                    stroke="var(--line)"
                  />
                  <XAxis
                    dataKey="name"
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: "var(--muted)", fontSize: 12 }}
                  />
                  <YAxis
                    domain={[0, 10]}
                    tickLine={false}
                    axisLine={false}
                    tick={{ fill: "var(--muted)", fontSize: 12 }}
                  />
                  <Tooltip
                    cursor={{ fill: "var(--wash)" }}
                    contentStyle={{
                      background: "var(--panel)",
                      border: "1px solid var(--line)",
                      borderRadius: 8,
                    }}
                  />
                  <Bar
                    dataKey="score"
                    name="Answer score"
                    fill="#176b5b"
                    radius={[4, 4, 0, 0]}
                    maxBarSize={44}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Panel>
          <Panel className="analytics-insight">
            <span className="section-icon">
              <BriefcaseBusiness size={17} />
            </span>
            <div>
              <strong>Keep the trend in perspective</strong>
              <p>
                These scores reflect one practice session, not a prediction
                about hiring outcomes. Use the report’s recommended topics to
                guide your next round.
              </p>
            </div>
            <Link to={`/interview/${session.interviewId}/results`}>
              Open report <ArrowRight size={14} />
            </Link>
          </Panel>
        </>
      )}
      {practiceHistory.length > 0 && (
        <Panel className="practice-history-panel">
          <SectionTitle>
            Recent answers <span className="subtle-chip">YOUR HISTORY</span>
          </SectionTitle>
          <div className="practice-history-list">
            {practiceHistory.map((item) => (
              <article
                className="practice-history-item"
                key={`${item.interview_id}-${item.question_index}`}
              >
                <div>
                  <span>
                    QUESTION {String(item.question_index + 1).padStart(2, "0")}
                  </span>
                  <strong>{item.question}</strong>
                  <p>{item.skipped ? "Skipped" : item.answer}</p>
                </div>
                {item.evaluation.overall_score != null && (
                  <strong className="practice-history-score">
                    {item.evaluation.overall_score}/10
                  </strong>
                )}
              </article>
            ))}
          </div>
        </Panel>
      )}
    </>
  );
}

export function ProfilePage() {
  const { session, user } = useApp();
  const preferenceKey = `coach-profile-preferences:${user.id}`;
  const [preferences, setPreferences] = useState(() => {
    try {
      return (
        JSON.parse(localStorage.getItem(preferenceKey)) || {
          roles: "",
          skills: "",
        }
      );
    } catch {
      return { roles: "", skills: "" };
    }
  });
  const [saved, setSaved] = useState(false);

  const savePreferences = (event) => {
    event.preventDefault();
    localStorage.setItem(
      preferenceKey,
      JSON.stringify(preferences),
    );
    setSaved(true);
  };

  return (
    <>
      <PageHeading
        eyebrow="YOUR SPACE"
        title="Profile"
        description="Your account and personal practice preferences."
      />
      <Panel className="profile-panel">
        <div className="profile-intro">
          <span className="profile-avatar">
            {user.full_name
              .trim()
              .split(/\s+/)
              .slice(0, 2)
              .map((part) => part[0])
              .join("")
              .toUpperCase()}
          </span>
          <div>
            <h2>{user.full_name}</h2>
            <p>{user.email}</p>
          </div>
          <span className="subtle-chip">ACCOUNT</span>
        </div>
        <form onSubmit={savePreferences}>
          <div className="profile-grid">
            <div className="profile-field">
              <span>Resume</span>
              <strong>{session.resumeName || "Not added"}</strong>
              <small>
                {session.resumeText
                  ? "Text and analysis saved to your account"
                  : "Upload a resume to begin"}
              </small>
            </div>
            <div className="profile-field">
              <label htmlFor="preferred-roles">Preferred roles</label>
              <input
                id="preferred-roles"
                value={preferences.roles}
                onChange={(event) => {
                  setPreferences({ ...preferences, roles: event.target.value });
                  setSaved(false);
                }}
                placeholder="e.g. Backend Engineer, Data Analyst"
                maxLength={240}
              />
              <small>Saved in this browser for this account</small>
            </div>
            <div className="profile-field">
              <label htmlFor="practice-skills">Skills to practice</label>
              <input
                id="practice-skills"
                value={preferences.skills}
                onChange={(event) => {
                  setPreferences({
                    ...preferences,
                    skills: event.target.value,
                  });
                  setSaved(false);
                }}
                placeholder="e.g. Python, system design, communication"
                maxLength={240}
              />
              <small>
                Use these as personal reminders; they do not alter AI
                evaluations
              </small>
            </div>
            <div className="profile-field">
              <span>Contact information</span>
              <strong>{user.email}</strong>
              <small>Verified by your signed-in account</small>
            </div>
          </div>
          <div className="profile-save-row">
            <span>
              {saved
                ? "Preferences saved for this account in this browser."
                : "Preferences are kept separate for each signed-in account."}
            </span>
            <button className="button button-secondary" type="submit">
              Save preferences
            </button>
          </div>
        </form>
        <div className="profile-footer">
          <ShieldCheck size={16} />
          <span>
            Your resume analyses, practice sessions and reports are stored with
            your account. The original uploaded PDF is not retained.
          </span>
        </div>
      </Panel>
    </>
  );
}

export function SettingsPage() {
  const { theme, setTheme } = useApp();
  return (
    <>
      <PageHeading
        eyebrow="MAKE THIS SPACE YOURS"
        title="Settings"
        description="Appearance preferences are saved in this browser."
      />
      <Panel className="settings-panel">
        <SectionTitle>Appearance</SectionTitle>
        <p className="settings-copy">
          Choose the display that feels right for your practice sessions.
        </p>
        <div className="theme-options">
          <button
            className={`theme-option ${theme === "light" ? "theme-selected" : ""}`}
            onClick={() => setTheme("light")}
          >
            <span className="theme-preview theme-preview-light">
              <i />
              <i />
              <i />
            </span>
            <span>
              <Sun size={16} /> Light
            </span>
            {theme === "light" && <Check size={16} />}
          </button>
          <button
            className={`theme-option ${theme === "dark" ? "theme-selected" : ""}`}
            onClick={() => setTheme("dark")}
          >
            <span className="theme-preview theme-preview-dark">
              <i />
              <i />
              <i />
            </span>
            <span>
              <Moon size={16} /> Dark
            </span>
            {theme === "dark" && <Check size={16} />}
          </button>
        </div>
        <div className="settings-divider" />
        <SectionTitle>Account & notifications</SectionTitle>
        <div className="unavailable-setting">
          <span>
            <LockKeyhole size={17} />
          </span>
          <div>
            <strong>Account active</strong>
            <small>
              Your practice data and reports are associated with your signed-in
              account. Password reset by email is not configured.
            </small>
          </div>
        </div>
      </Panel>
    </>
  );
}
