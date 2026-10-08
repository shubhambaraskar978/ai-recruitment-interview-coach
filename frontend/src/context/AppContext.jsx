import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { accountService, authService } from "../services/api";

const AppContext = createContext(null);

function workspaceFromDashboard(dashboard) {
  const resume = dashboard.resume;
  const match = dashboard.job_match;
  const latestReport = dashboard.latest_report;
  return {
    resumeText: resume?.resume_text || null,
    resumeAnalysis: resume?.analysis || null,
    resumeName: resume?.filename || null,
    resumeAnalyses: dashboard.resume_analyses || [],
    jobDescription: match?.job_description || "",
    jobMatch: match?.analysis || null,
    jobMatches: dashboard.job_matches || [],
    interviews: dashboard.interviews || [],
    practiceHistory: dashboard.practice_history || [],
    practiceHistoryCount: dashboard.practice_history_count || 0,
    report: latestReport?.report || null,
    reportDetails: latestReport
      ? {
          report: latestReport.report,
          questions: latestReport.questions,
          answers: latestReport.answers,
          evaluations: latestReport.evaluations,
          skipped_questions: latestReport.skipped_questions,
        }
      : null,
    interviewId: latestReport?.interview_id || null,
  };
}

export function AppProvider({ children }) {
  const [session, setSession] = useState({});
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authMessage, setAuthMessage] = useState("");
  const [theme, setTheme] = useState(
    () => localStorage.getItem("coach-theme") || "light",
  );

  useEffect(() => {
    sessionStorage.removeItem("interview-coach-session");
    let active = true;
    authService
      .me()
      .then(({ user: currentUser }) =>
        accountService.dashboard().then((dashboard) => {
          if (active) {
            setUser(currentUser);
            setSession(workspaceFromDashboard(dashboard));
          }
        }),
      )
      .catch((error) => {
        if (active) {
          setUser(null);
          setSession({});
          if (
            error.status === 401 &&
            error.message !== "Please log in to access this feature."
          ) {
            setAuthMessage(error.message);
          }
        }
      })
      .finally(() => {
        if (active) setAuthLoading(false);
      });
    const handleExpiredSession = (event) => {
      setUser(null);
      setSession({});
      setAuthMessage(
        typeof event.detail === "string"
          ? event.detail
          : "Your session has expired. Please log in again.",
      );
      setAuthLoading(false);
    };
    window.addEventListener("auth:expired", handleExpiredSession);
    return () => {
      active = false;
      window.removeEventListener("auth:expired", handleExpiredSession);
    };
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("coach-theme", theme);
  }, [theme]);

  const signIn = useCallback(async (signedInUser) => {
    setAuthLoading(true);
    setSession({});
    setAuthMessage("");
    try {
      const dashboard = await accountService.dashboard();
      setSession(workspaceFromDashboard(dashboard));
      setUser(signedInUser);
    } finally {
      setAuthLoading(false);
    }
  }, []);

  const refreshAccountData = useCallback(async () => {
    const dashboard = await accountService.dashboard();
    setSession((current) => ({
      ...current,
      ...workspaceFromDashboard(dashboard),
    }));
  }, []);

  const signOut = useCallback(async () => {
    await authService.logout();
    setUser(null);
    setSession({});
    setAuthMessage("");
    window.location.replace("/");
  }, []);

  return (
    <AppContext.Provider
      value={{
        user,
        authLoading,
        authMessage,
        clearAuthMessage: () => setAuthMessage(""),
        signIn,
        signOut,
        refreshAccountData,
        session,
        setSession: (updates) =>
          setSession((current) => ({ ...current, ...updates })),
        clearSession: () => setSession({}),
        theme,
        setTheme,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}
