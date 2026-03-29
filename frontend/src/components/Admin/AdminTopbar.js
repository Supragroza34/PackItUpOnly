import { useNavigate, useLocation } from "react-router-dom";
import NotificationBell from "../NotificationBell";
import "./AdminTopbar.css";

function AdminTopbar({ user, handleLogout }) {
  const navigate = useNavigate();
  const location = useLocation();

  const navTabs = [
    { path: "/admin/dashboard", label: "Dashboard" },
    { path: "/admin/tickets", label: "Tickets" },
    { path: "/admin/users", label: "Users" },
    { path: "/admin/statistics", label: "Statistics" },
  ];

  const handleTabClick = (path) => navigate(path);

  return (
    <div className="admin-topbar-container">
      <div className="topbar-row-1">
        <h1>👋 Welcome, {user?.first_name || user?.username || "Admin"}</h1>
        <div className="topbar-row-1-actions">
          <NotificationBell
            onNotificationClick={(notif) => {
              if (notif.ticket) navigate(`/admin/tickets/${notif.ticket}`);
            }}
          />
          <button className="logout-btn" onClick={handleLogout}>
            Log Out
          </button>
        </div>
      </div>
      <div className="topbar-row-2">
        {navTabs.map((tab) => (
          <button
            key={tab.path}
            className={`nav-tab ${location.pathname === tab.path ? "active" : ""}`}
            onClick={() => handleTabClick(tab.path)}
          >
            {tab.label}
          </button>
        ))}
      </div>
    </div>
  );
}

export default AdminTopbar;