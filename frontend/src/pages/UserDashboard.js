import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { useAuth } from "../context/AuthContext";
import { apiFetch, authHeaders } from "../api";
import { checkAuth, logout as logoutAction } from "../store/slices/authSlice";
import "./UserDashboard.css";

const API_BASE = "http://localhost:8000/api";

function getAuthHeaders() {
  const token = localStorage.getItem("access");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

function statusClass(status) {
  return `status-badge status-${status || "pending"}`;
}

function getStatusLabel(ticket) {
  if (ticket.status !== "closed") {
    return (ticket.status || "pending").replace("_", " ");
  }
  if (!ticket.closed_by_role) return "Closed";
  const label = ticket.closed_by_role.charAt(0).toUpperCase() + ticket.closed_by_role.slice(1);
  return `Closed by ${label}`;
}

function UserDashboardPage() {
  const dispatch = useDispatch();
  const { user, loading } = useSelector((state) => state.auth);
  const [tickets, setTickets] = useState([]);
  const [loadError, setLoadError] = useState("");
  const nav = useNavigate();
  const { logout } = useAuth();

  // Check auth on mount
  useEffect(() => {
    dispatch(checkAuth());
  }, [dispatch]);

  // Fetch tickets when user is loaded
  useEffect(() => {
    if (!user) return;

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
        setTickets(data.tickets);
      } catch (err) {
        console.error("Dashboard fetch error:", err);
        setLoadError(`Could not connect to the server. Is Django running on port 8000? (${err.message})`);
      }
    };
    fetchDashboard();
  }, [user, nav]);

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

  function confirmCloseTwice(ticketId) {
    if (!window.confirm("Are you sure you want to close this ticket?")) return false;
    if (!window.confirm("Please confirm again. This will close the ticket. Do you want to proceed?")) return false;
    return true;
  }

  async function handleCloseTicket(ticketId) {
    if (!confirmCloseTwice(ticketId)) return;
    const token = localStorage.getItem("access");
    try {
      const res = await fetch(`${API_BASE}/dashboard/tickets/${ticketId}/close/`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        setLoadError(err.error || `Failed to close ticket (${res.status})`);
        return;
      }
      const resData = await res.json();
      setTickets((prev) =>
        prev.map((t) =>
          t.id === ticketId
            ? { ...t, status: "closed", closed_by_role: resData.closed_by_role || "student" }
            : t
        )
      );
    } catch (err) {
      setLoadError(`Could not close ticket: ${err.message}`);
    }
  }

  return (
    <div className="dashboard-page">
      {/* Top bar */}
      <div className="dashboard-topbar">
        <h1>👋 Welcome, {user.k_number || "Student"}</h1>
        <div className="dashboard-topbar-actions">
          <a href={`${window.location.protocol}//${window.location.hostname}:8000/chat/`} className="ai-helper-btn">AI Helper</a>
          <Link to="/faqs" className="faq-btn">View FAQs</Link>
          <button className="logout-btn" onClick={handleLogout}>
            Log Out
          </button>
        </div>
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
          <Link to="/create-ticket" className="create-ticket-btn">
            ＋ Create New Ticket
          </Link>
        </div>

        {tickets.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">🎫</div>
            <p>You haven't submitted any tickets yet.</p>
            <Link to="/create-ticket" className="create-ticket-btn">
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
                  {ticket.replies && ticket.replies.length > 0 && (
                    <div className="ticket-responses">
                      <h4 className="ticket-responses-title">Responses from staff</h4>
                      {ticket.replies.map((reply) => (
                        <div key={reply.id} className="ticket-response">
                          <p className="ticket-response-meta">
                            <strong>{reply.user_username}</strong>
                            {' · '}
                            {reply.created_at ? new Date(reply.created_at).toLocaleString() : ''}
                          </p>
                          <p className="ticket-response-body">{reply.body}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
                <div className="ticket-item-meta">
                  <span className={statusClass(ticket.status)}>
                    {getStatusLabel(ticket)}
                  </span>
                  <span className="ticket-date">
                    {new Date(ticket.created_at).toLocaleDateString("en-GB", {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}
                  </span>
                  {ticket.status !== "closed" && (
                    <button
                      type="button"
                      className="close-ticket-btn"
                      onClick={(e) => { e.stopPropagation(); handleCloseTicket(ticket.id); }}
                    >
                      Close ticket
                    </button>
                  )}
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