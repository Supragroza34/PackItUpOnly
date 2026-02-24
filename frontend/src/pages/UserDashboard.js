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

function getProgressWidth(status) {
  switch (status) {
    case "pending":
        return "20%";
    case "in_progress":
        return "60%";
    case "resolved":
        return "90%";
    case "closed":
        return "100%";
    default:
      return "0%";
  }
}

function UserDashboardPage() {
  const dispatch = useDispatch();
  const { user, loading } = useSelector((state) => state.auth);
  const [tickets, setTickets] = useState([]);
  const [loadError, setLoadError] = useState("");
  const nav = useNavigate();
  const { logout } = useAuth();
  const [selectedTicket, setSelectedTicket] = useState(null);

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

  return (
    <div className="dashboard-page">
      {/* Top bar */}
      <div className="dashboard-topbar">
        <h1>👋 Welcome, {user ? `${user.first_name} ${user.last_name}` : "Student"}</h1>
        <div className="dashboard-topbar-actions">
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
              <div key={ticket.id} className="ticket-item" onClick={() => setSelectedTicket(ticket)}>
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

        {/* Ticket PopUp */}
        {selectedTicket && (
          <div className="modal-overlay" onClick={() => setSelectedTicket(null)}>
            <div className="ticket-modal" onClick={(e) => e.stopPropagation()}>
              <button className="modal-close" onClick={() => setSelectedTicket(null)}>X</button>
              <h2>{selectedTicket.type_of_issue}</h2>

              {/* Progress Bar */}
              <div className="ticket-progress-container">
                <div className="ticket-progress-bar">
                  <div 
                    className={`ticket-progress-fill status-${selectedTicket.status}`}
                    style={{ width: getProgressWidth(selectedTicket.status) }}
                  ></div>
                  <span className="ticket-progress-text">
                    {selectedTicket.status.replace("_", " ")} - {getProgressWidth(selectedTicket.status.toLowerCase())}
                  </span>
                </div>
              </div>

              <p><strong>Department: </strong>{selectedTicket.department}</p>
              <p><strong>Status: </strong>{selectedTicket.status}</p>
              <p><strong>Priority: </strong>{selectedTicket.priority}</p>

              <p><strong>Created at: </strong>{" "} {new Date(selectedTicket.created_at).toLocaleString()}</p>

              <p><strong>Description:</strong></p>
              <p>{selectedTicket.additional_details}</p>

              
              {/* Responses */}
              <div className="ticket-responses">
                <h4 className="ticket-responses-title">Responses From Staff:</h4>
                {selectedTicket.replies && selectedTicket.replies.length > 0 ? (
                  selectedTicket.replies.map((reply) => (
                    <div key={reply.id} className="ticket-response">
                      <p className="ticket-response-meta">
                        <strong>{reply.user_username}</strong> · {new Date(reply.created_at).toLocaleString()}
                      </p>
                      <p className="ticket-response-body">{reply.body}</p>
                    </div>
                  ))
                ) : (
                  <p className="ticket-response-none">No Responses Yet.</p>
                )}
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default UserDashboardPage;