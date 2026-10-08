import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import {
  Activity,
  BriefcaseBusiness,
  ChevronDown,
  FileUser,
  House,
  Menu,
  MessageSquareText,
  Moon,
  Settings,
  Sparkles,
  Sun,
  X,
} from "lucide-react";
import { useApp } from "../context/AppContext";
import { healthService } from "../services/api";

const navigation = [
  { to: "/dashboard", label: "Overview", icon: House },
  { to: "/resume", label: "Resume analysis", icon: FileUser },
  { to: "/job-match", label: "Job match", icon: BriefcaseBusiness },
  { to: "/interview/setup", label: "Mock interview", icon: MessageSquareText },
  { to: "/analytics", label: "Your progress", icon: Activity },
];

const titleForPath = (pathname) =>
  navigation.find((item) => pathname.startsWith(item.to))?.label ||
  (pathname.includes("results")
    ? "Interview report"
    : pathname === "/profile"
      ? "Profile"
      : pathname === "/settings"
        ? "Settings"
        : "AI Interview Coach");

export function Shell() {
  const [drawer, setDrawer] = useState(false);
  const [profileMenu, setProfileMenu] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  const { theme, setTheme, user, signOut } = useApp();
  const location = useLocation();
  const title = titleForPath(location.pathname);
  const [apiStatus, setApiStatus] = useState("checking");
  const initials = user.full_name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();

  const logout = async () => {
    setLogoutError("");
    try {
      await signOut();
    } catch (error) {
      setLogoutError(error.message);
    }
  };

  useEffect(() => {
    let active = true;
    healthService
      .check()
      .then(() => {
        if (active) setApiStatus("connected");
      })
      .catch(() => {
        if (active) setApiStatus("unavailable");
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <div className="app-shell">
      {drawer && (
        <button
          className="drawer-scrim"
          aria-label="Close navigation"
          onClick={() => setDrawer(false)}
        />
      )}
      <aside className={`sidebar ${drawer ? "sidebar-open" : ""}`}>
        <NavLink
          className="brand"
          to="/dashboard"
          onClick={() => setDrawer(false)}
        >
          <span className="brand-mark">
            <Sparkles size={19} />
          </span>
          <span>
            interview<span className="brand-light">coach</span>
          </span>
        </NavLink>
        <p className="nav-caption">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {navigation.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              onClick={() => setDrawer(false)}
              className={({ isActive }) =>
                `nav-link ${isActive ? "nav-active" : ""}`
              }
            >
              <Icon size={17} strokeWidth={1.8} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <p className="nav-caption nav-caption-lower">PERSONAL</p>
        <nav aria-label="Personal settings">
          <NavLink
            to="/profile"
            onClick={() => setDrawer(false)}
            className={({ isActive }) =>
              `nav-link ${isActive ? "nav-active" : ""}`
            }
          >
            <FileUser size={17} />
            <span>Profile</span>
          </NavLink>
          <NavLink
            to="/settings"
            onClick={() => setDrawer(false)}
            className={({ isActive }) =>
              `nav-link ${isActive ? "nav-active" : ""}`
            }
          >
            <Settings size={17} />
            <span>Settings</span>
          </NavLink>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-note">
            <span className={`status-dot status-${apiStatus}`} />
            <div>
              <strong>Backend status</strong>
              <small>
                {apiStatus === "connected"
                  ? "API is responding"
                  : apiStatus === "checking"
                    ? "Checking connection…"
                    : "API unavailable"}
              </small>
            </div>
          </div>
          <div className="profile-menu">
            <button
              className="mini-profile"
              type="button"
              aria-expanded={profileMenu}
              aria-haspopup="menu"
              onClick={() => setProfileMenu((open) => !open)}
            >
              <span className="avatar">{initials || "U"}</span>
              <div>
                <strong>{user.full_name}</strong>
                <small>{user.email}</small>
              </div>
              <ChevronDown size={15} />
            </button>
            {profileMenu && (
              <div className="profile-menu-popover" role="menu">
                {logoutError && (
                  <p className="logout-error" role="alert">
                    {logoutError}
                  </p>
                )}
                <NavLink
                  to="/profile"
                  role="menuitem"
                  onClick={() => setProfileMenu(false)}
                >
                  Your profile
                </NavLink>
                <button type="button" role="menuitem" onClick={logout}>
                  Log out
                </button>
              </div>
            )}
          </div>
        </div>
      </aside>
      <div className="main-column">
        <header className="topbar">
          <button
            className="icon-button mobile-menu"
            aria-label="Open navigation"
            onClick={() => setDrawer(true)}
          >
            <Menu size={19} />
          </button>
          <div className="topbar-title">{title}</div>
          <div className="topbar-actions">
            <span className={`connected-label connected-${apiStatus}`}>
              <span className={`status-dot status-${apiStatus}`} />
              {apiStatus === "connected"
                ? "API connected"
                : apiStatus === "checking"
                  ? "Checking API"
                  : "API unavailable"}
            </span>
            <button
              className="icon-button"
              aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
              onClick={() => setTheme(theme === "light" ? "dark" : "light")}
            >
              {theme === "light" ? <Moon size={17} /> : <Sun size={17} />}
            </button>
            {drawer && (
              <button
                className="icon-button close-drawer"
                aria-label="Close navigation"
                onClick={() => setDrawer(false)}
              >
                <X size={18} />
              </button>
            )}
          </div>
        </header>
        <main className="page-content">
          <Outlet />
        </main>
        <footer className="app-footer">
          <span>AI Interview Coach</span>
          <span>
            Private by design · Session data stays in this browser tab
          </span>
        </footer>
      </div>
    </div>
  );
}
