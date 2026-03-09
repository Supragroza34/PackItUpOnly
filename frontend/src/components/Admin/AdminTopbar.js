import { useNavigate, useLocation } from "react-router-dom";
import NotificationBell from "../NotificationBell";
import "./AdminTopbar.css";

{/*
function AdminTopbar({ user, handleLogout }) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="dashboard-topbar">
      <h1>👋 Welcome, {user?.first_name || user?.username || "Admin"}</h1>

      <div className="dashboard-topbar-actions">
        <NotificationBell
          onNotificationClick={(notif) => {
            if (notif.ticket) {
              navigate(`/admin/tickets/${notif.ticket}`);
            }
          }}
        />

        <button
          className={`nav-tab ${
            location.pathname === "/admin/dashboard" ? "active" : ""
          }`}
          onClick={() => navigate("/admin/dashboard")}
        >
          Dashboard
        </button>

        <button
          className={`nav-tab ${
            location.pathname === "/admin/tickets" ? "active" : ""
          }`}
          onClick={() => navigate("/admin/tickets")}
        >
          Tickets
        </button>

        <button
          className={`nav-tab ${
            location.pathname === "/admin/users" ? "active" : ""
          }`}
          onClick={() => navigate("/admin/users")}
        >
          Users
        </button>

        <button
          className={`nav-tab ${
            location.pathname === "/admin/statistics" ? "active" : ""
          }`}
          onClick={() => navigate("/admin/statistics")}
        >
          Statistics
        </button>

        <button className="logout-btn" onClick={handleLogout}>
          Log Out
        </button>
      </div>
    </div>
  );
}

export default AdminTopbar;
*/}

function AdminTopbar({ user, handleLogout }) {
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <div className="admin-topbar-container">
      {/* Row 1: Welcome left, bell+logout right */}
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

      {/* Row 2: Navigation tabs centered */}
      <div className="topbar-row-2">
        <button
          className={`nav-tab ${
            location.pathname === "/admin/dashboard" ? "active" : ""
          }`}
          onClick={() => navigate("/admin/dashboard")}
        >
          Dashboard
        </button>
        <button
          className={`nav-tab ${
            location.pathname === "/admin/tickets" ? "active" : ""
          }`}
          onClick={() => navigate("/admin/tickets")}
        >
          Tickets
        </button>
        <button
          className={`nav-tab ${
            location.pathname === "/admin/users" ? "active" : ""
          }`}
          onClick={() => navigate("/admin/users")}
        >
          Users
        </button>
        <button
          className={`nav-tab ${
            location.pathname === "/admin/statistics" ? "active" : ""
          }`}
          onClick={() => navigate("/admin/statistics")}
        >
          Statistics
        </button>
      </div>
    </div>
  );
}

export default AdminTopbar;