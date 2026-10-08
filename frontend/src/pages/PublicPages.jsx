import {
  ArrowRight,
  Check,
  CirclePlay,
  FileSearch,
  MessageSquareText,
  Mic2,
  ShieldCheck,
  Sparkles,
  Target,
  TrendingUp,
  Zap,
} from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useState } from "react";
import { Button } from "../components/UI";
import { useApp } from "../context/AppContext";
import { authService } from "../services/api";

const features = [
  [
    FileSearch,
    "Resume, understood",
    "Turn your PDF into a clear picture of the experience you bring.",
  ],
  [
    Target,
    "A sharper role match",
    "See where your experience aligns with a real job description.",
  ],
  [
    MessageSquareText,
    "Practice that feels personal",
    "Questions are generated from your resume and target role.",
  ],
  [
    TrendingUp,
    "Feedback you can use",
    "Get structured notes on relevance, clarity, completeness and accuracy.",
  ],
];

export function LandingPage() {
  const navigate = useNavigate();
  return (
    <div className="landing">
      <header className="landing-nav">
        <Link className="brand" to="/">
          <span className="brand-mark">
            <Sparkles size={19} />
          </span>
          <span>
            interview<span className="brand-light">coach</span>
          </span>
        </Link>
        <nav className="landing-links">
          <a href="#features">What you get</a>
          <a href="#process">How it works</a>
        </nav>
        <div className="landing-actions">
          <Link className="quiet-link" to="/login">
            Log in
          </Link>
          <Button onClick={() => navigate("/dashboard")}>
            Start practicing <ArrowRight size={16} />
          </Button>
        </div>
      </header>
      <main>
        <section className="hero-section">
          <div className="hero-copy">
            <div className="hero-kicker">
              <span className="online-dot" /> YOUR NEXT INTERVIEW, BETTER
              PREPARED
            </div>
            <h1>
              Prepare smarter.
              <br />
              <span>Interview better.</span>
            </h1>
            <p>
              Practice with an AI coach that starts with your resume,
              understands the role, and helps you find the words when it
              matters.
            </p>
            <div className="hero-ctas">
              <Button onClick={() => navigate("/interview/setup")}>
                Build my practice interview <ArrowRight size={16} />
              </Button>
              <a className="watch-link" href="#process">
                <CirclePlay size={18} /> See how it works
              </a>
            </div>
            <div className="hero-proof">
              <ShieldCheck size={16} />
              <span>Your documents stay in your practice session</span>
            </div>
          </div>
          <div
            className="hero-art"
            aria-label="Illustration of a personalized interview practice session"
          >
            <div className="art-orbit orbit-one" />
            <div className="art-orbit orbit-two" />
            <div className="art-spark spark-one">
              <Sparkles size={17} />
            </div>
            <div className="art-spark spark-two">
              <Zap size={15} />
            </div>
            <div className="art-sheet">
              <div className="sheet-top">
                <span className="sheet-dot" />
                <span className="sheet-dot" />
                <span className="sheet-dot" />
                <span>YOUR SESSION</span>
              </div>
              <div className="sheet-rule short" />
              <div className="sheet-label">PERSONALIZED QUESTION</div>
              <div className="sheet-question">
                Tell me about a project where you had to make a difficult
                technical trade-off.
              </div>
              <div className="sheet-feedback">
                <span className="feedback-icon">
                  <Mic2 size={15} />
                </span>
                <div>
                  <strong>Practice at your pace</strong>
                  <small>One thoughtful answer at a time</small>
                </div>
                <span className="feedback-arrow">
                  <ArrowRight size={15} />
                </span>
              </div>
              <div className="sheet-score">
                <span>ANSWER CLARITY</span>
                <strong>Feedback that moves you forward</strong>
                <div className="score-lines">
                  <i />
                  <i />
                  <i />
                  <i />
                  <i />
                </div>
              </div>
            </div>
            <div className="art-badge badge-top">
              <span className="badge-check">
                <Check size={14} />
              </span>
              <div>
                <strong>Built around you</strong>
                <small>Your resume + the role</small>
              </div>
            </div>
            <div className="art-badge badge-bottom">
              <span className="badge-icon">
                <MessageSquareText size={15} />
              </span>
              <div>
                <strong>Ready to practice</strong>
                <small>AI-generated, never generic</small>
              </div>
            </div>
          </div>
          <div className="hero-bottom-note">
            <span>THOUGHTFUL PREPARATION</span>
            <span>MADE FOR THE MOMENT BEFORE</span>
            <span>YOU WALK INTO THE ROOM</span>
          </div>
        </section>
        <section className="feature-section" id="features">
          <div className="section-intro">
            <p className="eyebrow">YOUR PERSONAL PRACTICE PARTNER</p>
            <h2>More than a list of questions.</h2>
            <p>
              Make every practice session feel relevant to the work you want to
              do next.
            </p>
          </div>
          <div className="feature-grid">
            {features.map(([Icon, title, text], index) => (
              <article className="feature-item" key={title}>
                <span className="feature-icon">{<Icon size={19} />}</span>
                <span className="feature-index">0{index + 1}</span>
                <h3>{title}</h3>
                <p>{text}</p>
              </article>
            ))}
          </div>
        </section>
        <section className="process-section" id="process">
          <div className="process-intro">
            <p className="eyebrow">A SIMPLE, USEFUL LOOP</p>
            <h2>
              From your resume
              <br />
              to a calmer answer.
            </h2>
            <p>
              Keep your preparation focused on the opportunity in front of you.
            </p>
            <Button variant="dark" onClick={() => navigate("/resume")}>
              Analyze my resume <ArrowRight size={16} />
            </Button>
          </div>
          <div className="process-steps">
            {[
              ["01", "Add your resume", "Upload a text-based PDF to start."],
              [
                "02",
                "Choose a role",
                "Paste the job description you care about.",
              ],
              [
                "03",
                "Practice out loud",
                "Answer tailored questions in your own words.",
              ],
              [
                "04",
                "Learn from feedback",
                "Review a report built from your answers.",
              ],
            ].map(([number, title, copy]) => (
              <div className="process-step" key={number}>
                <span>{number}</span>
                <div>
                  <h3>{title}</h3>
                  <p>{copy}</p>
                </div>
                <ArrowRight size={16} />
              </div>
            ))}
          </div>
        </section>
      </main>
      <footer className="landing-footer">
        <Link className="brand" to="/">
          <span className="brand-mark">
            <Sparkles size={17} />
          </span>
          <span>
            interview<span className="brand-light">coach</span>
          </span>
        </Link>
        <span>Make the next conversation count.</span>
        <span>AI Interview Coach · 2026</span>
      </footer>
    </div>
  );
}

export function AuthPage({ mode }) {
  const navigate = useNavigate();
  const location = useLocation();
  const { signIn, authMessage, clearAuthMessage } = useApp();
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const returnTo = location.state?.from;
  const destination =
    typeof returnTo?.pathname === "string" &&
    returnTo.pathname.startsWith("/") &&
    !returnTo.pathname.startsWith("//")
      ? `${returnTo.pathname}${returnTo.search || ""}${returnTo.hash || ""}`
      : "/dashboard";
  const isLogin = mode === "login";
  return (
    <div className="auth-page">
      <div className="auth-aside">
        <Link className="brand" to="/">
          <span className="brand-mark">
            <Sparkles size={19} />
          </span>
          <span>
            interview<span className="brand-light">coach</span>
          </span>
        </Link>
        <div>
          <p className="eyebrow">A LITTLE PRACTICE GOES A LONG WAY</p>
          <h1>
            Show up as
            <br />
            your best self.
          </h1>
          <p>Build confidence one thoughtful answer at a time.</p>
        </div>
        <div className="auth-aside-foot">
          Personalized practice, built around your next opportunity.
        </div>
      </div>
      <div className="auth-form-wrap">
        <div className="auth-form">
          <Link className="back-link" to="/">
            ← Back to home
          </Link>
          <p className="eyebrow">{isLogin ? "WELCOME BACK" : "GET STARTED"}</p>
          <h2>{isLogin ? "Good to see you." : "Create your account."}</h2>
          <p className="auth-subtitle">
            {isLogin
              ? "Pick up where your preparation left off."
              : "Start preparing for the conversations ahead."}
          </p>
          <form
            onSubmit={async (event) => {
              event.preventDefault();
              setMessage("");
              clearAuthMessage();
              const formData = new FormData(event.currentTarget);
              const password = formData.get("password");

              if (
                !isLogin &&
                password !== formData.get("confirmPassword")
              ) {
                setMessage("The passwords do not match.");
                return;
              }

              setIsSubmitting(true);
              try {
                const result = isLogin
                  ? await authService.login({
                      email: formData.get("email"),
                      password,
                    })
                  : await authService.register({
                      full_name: formData.get("fullName"),
                      email: formData.get("email"),
                      password,
                    });
                await signIn(result.user);
                navigate(destination, { replace: true });
              } catch (error) {
                setMessage(error.message);
              } finally {
                setIsSubmitting(false);
              }
            }}
          >
            {!isLogin && (
              <label>
                Full name
                <input
                  name="fullName"
                  autoComplete="name"
                  placeholder="Your name"
                  maxLength={120}
                  required
                />
              </label>
            )}
            <label>
              Email address
              <input
                name="email"
                type="email"
                autoComplete="email"
                autoCapitalize="none"
                maxLength={254}
                placeholder="you@example.com"
                required
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                autoComplete={isLogin ? "current-password" : "new-password"}
                placeholder="At least 8 characters"
                minLength={8}
                maxLength={isLogin ? 128 : 72}
                required
              />
            </label>
            {!isLogin && (
              <label>
                Confirm password
                <input
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  placeholder="Enter your password again"
                  minLength={8}
                  maxLength={72}
                  required
                />
              </label>
            )}
            {(message || authMessage) && (
              <p className="notice notice-error" role="alert">
                {message || authMessage}
              </p>
            )}
            <Button className="full-width" type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? isLogin
                  ? "Logging in…"
                  : "Creating account…"
                : isLogin
                  ? "Log in"
                  : "Create account"}{" "}
              {!isSubmitting && <ArrowRight size={16} />}
            </Button>
          </form>
          <p className="auth-switch">
            {isLogin ? "New here?" : "Already have an account?"}{" "}
            <Link to={isLogin ? "/register" : "/login"}>
              {isLogin ? "Create an account" : "Log in"}
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
