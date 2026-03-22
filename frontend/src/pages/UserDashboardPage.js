import React, { useEffect, useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { checkAuth } from "../store/slices/authSlice";
import "./UserDashboardPage.css";
import UserNavbar from "../components/UserNavbar";
import NotificationBell from "../components/NotificationBell";

const isLocal =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1";
const API_BASE = isLocal
  ? "http://localhost:8000/api"
  : `${window.location.origin}/api`;

function statusClass(status) {
  return `status-badge status-${status || "pending"}`;
}

function getProgressWidth(status) {
  switch (status) {
    case "pending":
        return "20%";
    case "seen":
        return "40%"
    case "in_progress":
        return "60%";
    case "awaiting_response":
        return "75%"
    case "resolved":
      return "90%";
    case "closed":
      return "100%";
    default:
      return "0%";
  }
}


function getStatusLabel(ticket) {
  if (ticket.status !== "closed") {
    return (ticket.status || "pending").replace("_", " ");
  }
  if (!ticket.closed_by_role) return "Closed";
  const label =
    ticket.closed_by_role.charAt(0).toUpperCase() +
    ticket.closed_by_role.slice(1);
  return `Closed by ${label}`;
}

function isTicketClosed(ticket) {
  return (ticket?.status || "") === "closed";
}

export function coerceRepliesToArray(replies) {
  return Array.isArray(replies) ? replies : [];
}

export function getLocalToken() {
  return localStorage.getItem("access") || "";
}

export function isTicketOpenForReply(selectedTicket) {
  return Boolean(selectedTicket) && selectedTicket.status !== "closed";
}

export function canDownloadTicketPdf(ticketStatus) {
  return ticketStatus === "closed";
}

export function getReplyMessageError(message) {
  return message.trim() ? "" : "Reply cannot be empty.";
}

export function guardPdfDownload(ticketStatus, notify = alert) {
  if (canDownloadTicketPdf(ticketStatus)) {
    return true;
  }

  notify("PDF summary is available once the ticket is closed.");
  return false;
}

export function validateReplyBeforeSubmit(message, setError) {
  const messageError = getReplyMessageError(message);
  if (!messageError) {
    return false;
  }

  setError(messageError);
  return true;
}

function UserDashboardPage() {
  const dispatch = useDispatch();
  const { user } = useSelector((state) => state.auth);
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [replyBody, setReplyBody] = useState("");
  const [replySubmitting, setReplySubmitting] = useState(false);
  const [replyError, setReplyError] = useState("");
  const [loadError, setLoadError] = useState("");
  const nav = useNavigate();

  useEffect(() => {
    dispatch(checkAuth());
  }, [dispatch]);

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
        setTickets(data.tickets || []);
      } catch (err) {
        console.error("Dashboard fetch error:", err);
        setLoadError(
          `Could not connect to the server. Is Django running on port 8000? (${err.message})`
        );
      }
    };

    fetchDashboard();
  }, [user, nav]);

  function confirmCloseTwice() {
    if (!window.confirm("Are you sure you want to close this ticket?")) {
      return false;
    }
    if (
      !window.confirm(
        "Please confirm again. This will close the ticket. Do you want to proceed?"
      )
    ) {
      return false;
    }
    return true;
  }

  async function handleCloseTicket(ticketId) {
    if (!confirmCloseTwice()) return;

    const token = localStorage.getItem("access");

    try {
      const res = await fetch(`${API_BASE}/dashboard/tickets/${ticketId}/close/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
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
            ? {
                ...t,
                status: "closed",
                closed_by_role: resData.closed_by_role || "student",
              }
            : t
        )
      );

      setSelectedTicket((prev) =>
        prev && prev.id === ticketId
          ? {
              ...prev,
              status: "closed",
              closed_by_role: resData.closed_by_role || "student",
            }
          : prev
      );
    } catch (err) {
      setLoadError(`Could not close ticket: ${err.message}`);
    }
  }

  async function handleDownloadPdf(ticketId, ticketStatus) {
    if (!guardPdfDownload(ticketStatus)) {
      return;
    }

    const token = getLocalToken();
    try {
      const res = await fetch(`${API_BASE}/tickets/${ticketId}/pdf/`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || `Could not download PDF (${res.status})`);
        return;
      }

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `ticket_${ticketId}_summary.pdf`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF download error:", err);
      alert(`Could not download PDF: ${err.message}`);
    }
  }

  async function fetchTicketReplies(ticketId, token) {
    const res = await fetch(`${API_BASE}/tickets/${ticketId}/replies/`, {
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Failed to fetch replies (${res.status})`);
    }

    const replies = await res.json();
    return coerceRepliesToArray(replies);
  }

  async function handleSendReply() {
    if (!isTicketOpenForReply(selectedTicket)) return;

    if (validateReplyBeforeSubmit(replyBody, setReplyError)) {
      return;
    }

    const token = localStorage.getItem("access");
    if (!token) {
      nav("/login", { replace: true });
      return;
    }

    setReplySubmitting(true);
    setReplyError("");

    try {
      const createRes = await fetch(
        `${API_BASE}/tickets/${selectedTicket.id}/replies/`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ body: replyBody.trim() }),
        }
      );

      if (!createRes.ok) {
        const err = await createRes.json().catch(() => ({}));
        setReplyError(err.error || err.body?.[0] || "Could not send reply.");
        return;
      }

      const updatedReplies = await fetchTicketReplies(selectedTicket.id, token);

      setTickets((prev) =>
        prev.map((t) =>
          t.id === selectedTicket.id ? { ...t, replies: updatedReplies } : t
        )
      );

      setSelectedTicket((prev) =>
        prev && prev.id === selectedTicket.id
          ? { ...prev, replies: updatedReplies }
          : prev
      );

      setReplyBody("");
    } catch (err) {
      setReplyError(`Could not send reply: ${err.message}`);
    } finally {
      setReplySubmitting(false);
    }
  }

  if (loadError) {
    return (
      <>
        <UserNavbar />
        <div className="dashboard-page">
          <div className="error-state">{loadError}</div>
        </div>
      </>
    );
  }

  if (!user) {
    return (
      <>
        <UserNavbar />
        <div className="dashboard-page">
          <div className="loading-state">Loading your dashboard…</div>
        </div>
      </>
    );
  }

  const countByStatus = (s) => tickets.filter((t) => t.status === s).length;

  return (
    <>
      <UserNavbar />

      <div className="dashboard-page">
        <div className="dashboard-topbar">
          <h1>👋 Welcome, {user ? `${user.first_name} ${user.last_name}` : "Student"}</h1>
            <NotificationBell
              onNotificationClick={(notif) => {
                const ticket = tickets.find((t) => t.id === notif.ticket_id);
                if (ticket) setSelectedTicket(ticket);
              }}
            />
        </div>


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
          <div className="summary-card">
            <div className="summary-count">{countByStatus("closed")}</div>
            <div className="summary-label">Closed</div>
          </div>
        </div>

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
                <div
                  key={ticket.id}
                  className="ticket-item"
                  onClick={() => setSelectedTicket(ticket)}
                >
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
                              {" · "}
                              {reply.created_at
                                ? new Date(reply.created_at).toLocaleString()
                                : ""}
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
                        onClick={(e) => {
                          e.stopPropagation();
                          handleCloseTicket(ticket.id);
                        }}
                      >
                        Close ticket
                      </button>
                    )}

                    <button
                      type="button"
                      className={`download-pdf-btn${
                        !isTicketClosed(ticket)
                          ? " download-pdf-btn--disabled"
                          : ""
                      }`}
                      disabled={!isTicketClosed(ticket)}
                      title={
                        !isTicketClosed(ticket)
                          ? "Available once the ticket is closed"
                          : "Download PDF summary"
                      }
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDownloadPdf(ticket.id, ticket.status);
                      }}
                    >
                      📄 Download Summary
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {selectedTicket && (
          <div className="modal-overlay" onClick={() => setSelectedTicket(null)}>
            <div className="ticket-modal" onClick={(e) => e.stopPropagation()}>
              <div className="ticket-modal-header">
                <h2>{selectedTicket.type_of_issue}</h2>
                <button
                  className="modal-close"
                  type="button"
                  aria-label="Close ticket details"
                  onClick={() => setSelectedTicket(null)}
                >
                  X
                </button>
              </div>

              <div className="ticket-modal-body">
                <div className="ticket-progress-container">
                  <div className="ticket-progress-bar">
                    <div
                      className={`ticket-progress-fill status-${selectedTicket.status}`}
                      style={{ width: getProgressWidth(selectedTicket.status) }}
                    />
                    <span className="ticket-progress-text">
                      {getStatusLabel(selectedTicket)} -{" "}
                      {getProgressWidth(selectedTicket.status)}
                    </span>
                  </div>
                </div>

                <p>
                  <strong>Department: </strong>
                  {selectedTicket.department}
                </p>
                <p>
                  <strong>Status: </strong>
                  {getStatusLabel(selectedTicket)}
                </p>
                <p>
                  <strong>Priority: </strong>
                  {selectedTicket.priority}
                </p>
                <p>
                  <strong>Created at: </strong>
                  {new Date(selectedTicket.created_at).toLocaleString()}
                </p>

                <p>
                  <strong>Description:</strong>
                </p>
                <p>{selectedTicket.additional_details}</p>

                {selectedTicket.status !== "closed" && (
                  <button
                    type="button"
                    className="close-ticket-btn"
                    onClick={() => handleCloseTicket(selectedTicket.id)}
                  >
                    Close ticket
                  </button>
                )}

                <div className="ticket-responses">
                  <h4 className="ticket-responses-title">Conversation:</h4>
                  {selectedTicket.replies && selectedTicket.replies.length > 0 ? (
                    selectedTicket.replies.map((reply) => (
                      <div key={reply.id} className="ticket-response">
                        <p className="ticket-response-meta">
                          <strong>{reply.user_username}</strong> ·{" "}
                          {new Date(reply.created_at).toLocaleString()}
                        </p>
                        <p className="ticket-response-body">{reply.body}</p>
                      </div>
                    ))
                  ) : (
                    <p className="ticket-response-none">No Responses Yet.</p>
                  )}
                </div>

                {selectedTicket.status !== "closed" && (
                  <div className="ticket-reply-composer">
                    <label className="ticket-reply-label" htmlFor="student-reply-box">
                      Your reply
                    </label>
                    <textarea
                      id="student-reply-box"
                      className="ticket-reply-textarea"
                      value={replyBody}
                      onChange={(e) => {
                        setReplyBody(e.target.value);
                        if (replyError) setReplyError("");
                      }}
                      placeholder="Write your response to continue the conversation..."
                      rows={4}
                      maxLength={2000}
                    />
                    {replyError && <p className="ticket-reply-error">{replyError}</p>}
                    <button
                      type="button"
                      className="ticket-reply-send-btn"
                      onClick={handleSendReply}
                      disabled={replySubmitting || !replyBody.trim()}
                    >
                      {replySubmitting ? "Sending..." : "Send reply"}
                    </button>
                  </div>
                )}

                <button
                  type="button"
                  className={`download-pdf-btn download-pdf-btn--modal${
                    !isTicketClosed(selectedTicket)
                      ? " download-pdf-btn--disabled"
                      : ""
                  }`}
                  disabled={!isTicketClosed(selectedTicket)}
                  title={
                    !isTicketClosed(selectedTicket)
                      ? "Available once the ticket is closed"
                      : "Download PDF summary"
                  }
                  onClick={() =>
                    handleDownloadPdf(selectedTicket.id, selectedTicket.status)
                  }
                >
                  📄 Download PDF Summary
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  );
}

export default UserDashboardPage;