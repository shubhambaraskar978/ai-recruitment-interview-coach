import { lazy, Suspense } from "react";
import { Navigate, Route, Routes, useLocation } from "react-router-dom";
import { Shell } from "./components/Shell";
import { useApp } from "./context/AppContext";

const LandingPage = lazy(() =>
  import("./pages/PublicPages").then((module) => ({
    default: module.LandingPage,
  })),
);
const AuthPage = lazy(() =>
  import("./pages/PublicPages").then((module) => ({
    default: module.AuthPage,
  })),
);
const DashboardPage = lazy(() =>
  import("./pages/WorkspacePages").then((module) => ({
    default: module.DashboardPage,
  })),
);
const ResumePage = lazy(() =>
  import("./pages/WorkspacePages").then((module) => ({
    default: module.ResumePage,
  })),
);
const JobMatchPage = lazy(() =>
  import("./pages/WorkspacePages").then((module) => ({
    default: module.JobMatchPage,
  })),
);
const SetupPage = lazy(() =>
  import("./pages/WorkspacePages").then((module) => ({
    default: module.SetupPage,
  })),
);
const InterviewPage = lazy(() =>
  import("./pages/InterviewPages").then((module) => ({
    default: module.InterviewPage,
  })),
);
const ResultsPage = lazy(() =>
  import("./pages/InterviewPages").then((module) => ({
    default: module.ResultsPage,
  })),
);
const AnalyticsPage = lazy(() =>
  import("./pages/AccountPages").then((module) => ({
    default: module.AnalyticsPage,
  })),
);
const ProfilePage = lazy(() =>
  import("./pages/AccountPages").then((module) => ({
    default: module.ProfilePage,
  })),
);
const SettingsPage = lazy(() =>
  import("./pages/AccountPages").then((module) => ({
    default: module.SettingsPage,
  })),
);

function RequireAuth({ children }) {
  const { user, authLoading } = useApp();
  const location = useLocation();
  if (authLoading) {
    return (
      <div className="route-loading" role="status">
        Restoring your secure session…
      </div>
    );
  }
  if (!user) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: location }}
      />
    );
  }
  return children;
}

function GuestOnly({ children }) {
  const { user, authLoading } = useApp();
  const location = useLocation();
  if (authLoading) {
    return (
      <div className="route-loading" role="status">
        Restoring your secure session…
      </div>
    );
  }
  if (user) {
    const from = location.state?.from;
    const destination =
      typeof from?.pathname === "string" &&
      from.pathname.startsWith("/") &&
      !from.pathname.startsWith("//")
        ? `${from.pathname}${from.search || ""}${from.hash || ""}`
        : "/dashboard";
    return <Navigate to={destination} replace />;
  }
  return children;
}

export default function App() {
  return (
    <Suspense
      fallback={
        <div className="route-loading" role="status">
          Loading your workspace…
        </div>
      }
    >
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/login"
          element={
            <GuestOnly>
              <AuthPage mode="login" />
            </GuestOnly>
          }
        />
        <Route
          path="/register"
          element={
            <GuestOnly>
              <AuthPage mode="register" />
            </GuestOnly>
          }
        />
        <Route
          element={
            <RequireAuth>
              <Shell />
            </RequireAuth>
          }
        >
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/resume" element={<ResumePage />} />
          <Route path="/job-match" element={<JobMatchPage />} />
          <Route path="/interview/setup" element={<SetupPage />} />
          <Route path="/interview/:id" element={<InterviewPage />} />
          <Route path="/interview/:id/results" element={<ResultsPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/profile" element={<ProfilePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
  );
}
