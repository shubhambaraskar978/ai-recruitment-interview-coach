import {
  AlertCircle,
  ArrowUpRight,
  LoaderCircle,
  Sparkles,
} from "lucide-react";
import ReactMarkdown from "react-markdown";

export function Button({
  children,
  variant = "primary",
  className = "",
  ...props
}) {
  return (
    <button className={`button button-${variant} ${className}`} {...props}>
      {children}
    </button>
  );
}

export function Panel({ children, className = "", ...props }) {
  return (
    <section className={`panel ${className}`} {...props}>
      {children}
    </section>
  );
}

export function PageHeading({ eyebrow, title, description, action }) {
  return (
    <div className="page-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        {description && <p className="page-description">{description}</p>}
      </div>
      {action}
    </div>
  );
}

export function Markdown({ children }) {
  return (
    <div className="markdown">
      <ReactMarkdown>{children || ""}</ReactMarkdown>
    </div>
  );
}

export function ScoreRing({
  score,
  max = 100,
  label = "score",
  size = "large",
}) {
  const value = Number.isFinite(Number(score))
    ? Math.min(Math.max(Number(score), 0), max)
    : 0;
  const percent = Math.round((value / max) * 100);
  return (
    <div
      className={`score-ring score-${size}`}
      style={{ "--score": `${percent}%` }}
      role="img"
      aria-label={`${label}: ${value} out of ${max}`}
    >
      <div>
        <strong>{value}</strong>
        <span>/{max}</span>
        <small>{label}</small>
      </div>
    </div>
  );
}

export function Loader({ label = "Working on it" }) {
  return (
    <div className="loader-block" role="status">
      <span className="loader-mark">
        <Sparkles size={18} />
        <LoaderCircle size={38} />
      </span>
      <strong>{label}</strong>
      <span className="muted">This can take a little while.</span>
    </div>
  );
}

export function ErrorNotice({ message, onRetry }) {
  return (
    <div className="notice notice-error" role="alert">
      <AlertCircle size={18} />
      <span>{message}</span>
      {onRetry && (
        <button className="text-button" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ icon: Icon = Sparkles, title, children, action }) {
  return (
    <div className="empty-state">
      <span className="empty-icon">
        <Icon size={21} />
      </span>
      <h3>{title}</h3>
      <div className="empty-description">{children}</div>
      {action}
    </div>
  );
}

export function SectionTitle({ children, aside }) {
  return (
    <div className="section-title">
      <h2>{children}</h2>
      {aside}
    </div>
  );
}

export function LinkAction({ to, children }) {
  return (
    <a className="link-action" href={to}>
      {children}
      <ArrowUpRight size={15} />
    </a>
  );
}
