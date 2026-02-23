import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./UserDashboard.css";

const API_BASE = "http://localhost:8000/api";

function getAuthHeaders() {
  const token = localStorage.getItem("access");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function statusClass(status) {
  return `status-badge status-${status || "pending"}`;
}

function UserDashboardPage() {
  const [user, setUser] = useState(null);
  const [tickets, setTickets] = useState([]);
  const [loadError, setLoadError] = useState("");
  const nav = useNavigate();
  const { logout } = useAuth();

  useEffect(() => {
    const fetchDashboard = async () => {
      const token = localStorage.getItem("access");
      if (!token) {
        nav("/login", { replace: true });
        return;
      }
      try {
        const res = await fetch(`${API_BASE}/dashboard/`, {
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        });
        if (res.status === 401 || res.status === 403) {
          localStorage.removeItem("access");
          localStorage.removeItem("refresh");
          nav("/login", { replace: true });
          return;
        }
        if (!res.ok) {
          const text = await res.text();
          setLoadError(`Server error (${res.status}): ${text}`);
          return;
        }
        const data = await res.json();
        setUser(data.user);
        setTickets(data.tickets);
      } catch (err) {
        console.error("Dashboard fetch error:", err);
        setLoadError(`Could not connect to the server. Is Django running on port 8000? (${err.message})`);
      }
    };
    fetchDashboard();
  }, [nav]);

  async function handleLogout() {
    await logout();
    nav("/login", { replace: true });
  }

  if (loadError) {
    return (
      <div className="dashboard-page">
        <div className="error-state">{loadError}</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="dashboard-page">
        <div className="loading-state">Loading your dashboard…</div>
      </div>
    );
  }

  const countByStatus = (s) => tickets.filter((t) => t.status === s).length;

  return (
    <div className="dashboard-page">
      {/* Top bar */}
      <div className="dashboard-topbar">
        <h1>👋 Welcome, {user.k_number || "Student"}</h1>
        <button className="logout-btn" onClick={handleLogout}>
          Log Out
        </button>
      </div>

      {/* Summary cards */}
      <div className="dashboard-summary">
        <div className="summary-card">
          <div className="summary-count">{tickets.length}</div>
          <div className="summary-label">Total Tickets</div>
        </div>
        <div className="summary-card">
          <div className="summary-count">{countByStatus("pending")}</div>
          <div className="summary-label">Pending</div>
        </div>
        <div className="summary-card">
          <div className="summary-count">{countByStatus("in_progress")}</div>
          <div className="summary-label">In Progress</div>
        </div>
        <div className="summary-card">
          <div className="summary-count">{countByStatus("resolved")}</div>
          <div className="summary-label">Resolved</div>
        </div>
      </div>

      {/* Ticket list */}
      <div className="dashboard-content">
        <div className="content-header">
          <h2>Your Tickets</h2>
          <Link to="/ticket-form" className="create-ticket-btn">
            ＋ Create New Ticket
          </Link>
        </div>

        {tickets.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🎫</div>
            <p>You haven't submitted any tickets yet.</p>
            <Link to="/ticket-form" className="create-ticket-btn">
              ＋ Create Your First Ticket
            </Link>
          </div>
        ) : (
          <div className="ticket-list">
            {tickets.map((ticket) => (
              <div key={ticket.id} className="ticket-item">
                <div className="ticket-item-info">
                  <h3>{ticket.type_of_issue}</h3>
                  <div className="ticket-dept">📁 {ticket.department}</div>
                  <div className="ticket-details">{ticket.additional_details}</div>
                </div>
                <div className="ticket-item-meta">
                  <span className={statusClass(ticket.status)}>
                    {(ticket.status || "pending").replace("_", " ")}
                  </span>
                  <span className="ticket-date">
                    {new Date(ticket.created_at).toLocaleDateString("en-GB", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default UserDashboardPage;