import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { logout as logoutAction } from "../store/slices/authSlice";
import { apiFetch } from "../api";
import NotificationBell from "../components/NotificationBell";
import WeeklyCalendar from "./WeeklyCalendar";
import "./StaffDashboardPage.css";
import "./StaffMeetingRequestsPage.css";

const DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

const TABS = [
  { key: "pending",  label: "Pending" },
  { key: "accepted", label: "Accepted" },
  { key: "denied",   label: "Declined" },
];

function initials(name = "") {
  const parts = name.trim().split(/\s+/);
  return ((parts[0]?.[0] || "") + (parts[1]?.[0] || "")).toUpperCase();
}

function StatusBadge({ status }) {
  const labels = { pending: "Pending", accepted: "Accepted", denied: "Declined" };
  return (
    <span className={`smr-badge smr-badge-${status}`}>
      {labels[status] || status}
    </span>
  );
}

function RequestCard({ req, onAccept, onDeny }) {
  const dt = new Date(req.meeting_datetime).toLocaleString("en-GB", {
    weekday: "short", day: "numeric", month: "short",
    year: "numeric", hour: "2-digit", minute: "2-digit",
  });

  return (
    <div className="smr-card">
      <div className="smr-card-avatar">{initials(req.student_name)}</div>
      <div className="smr-card-body">
        <div className="smr-card-top-row">
          <div>
            <span className="smr-card-name">{req.student_name}</span>
            <span className="smr-card-knumber"> ({req.student_k_number})</span>
          </div>
          <StatusBadge status={req.status} />
        </div>
        <div className="smr-card-email">{req.student_email}</div>
        <div className="smr-card-when">{dt}</div>
        <div className="smr-card-desc">{req.description}</div>
        {req.status === "pending" && (
          <div className="smr-card-actions">
            <button className="smr-btn smr-btn-accept" onClick={() => onAccept(req.id)}>
              Accept
            </button>
            <button className="smr-btn smr-btn-deny" onClick={() => onDeny(req.id)}>
              Decline
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Page
function StaffMeetingRequestsPage() {
  const dispatch = useDispatch();
  const navigate = useNavigate();

  const [meetingRequests, setMeetingRequests] = useState([]);
  const [officeHours, setOfficeHours]         = useState([]);
  const [loading, setLoading]                 = useState(true);
  const [err, setErr]                         = useState("");
  const [success, setSuccess]                 = useState("");
  const [activeTab, setActiveTab]             = useState("pending");

  // Office-hours form state
  const [dayOfWeek, setDayOfWeek]     = useState("Monday");
  const [startTime, setStartTime]     = useState("09:00");
  const [endTime, setEndTime]         = useState("17:00");
  const [addingHours, setAddingHours] = useState(false);

  const handleLogout = async () => {
    await dispatch(logoutAction());
    navigate("/login");
  };

  // Data Loading
  useEffect(() => { loadData(); }, []);

  async function loadData() {
    setLoading(true);
    setErr("");
    try {
      const [requestsData, hoursData] = await Promise.all([
        apiFetch("/staff/dashboard/meeting-requests/", {}, { auth: true }),
        apiFetch("/staff/office-hours/", {}, { auth: true }),
      ]);
      setMeetingRequests(requestsData);
      setOfficeHours(hoursData);
    } catch (e) {
      setErr(String(e.message || e).replace(/^HTTP \d+:\s*/, ""));
    } finally {
      setLoading(false);
    }
  }

  // Meeting request actions (optimistic updates) 
  async function handleAccept(requestId) {
    // Optimistic: move to accepted immediately
    setMeetingRequests((prev) =>
      prev.map((r) => (r.id === requestId ? { ...r, status: "accepted" } : r))
    );
    try {
      await apiFetch(
        `/staff/dashboard/meeting-requests/${requestId}/accept/`,
        { method: "POST" },
        { auth: true }
      );
    } catch (e) {
      // Rollback on failure
      setMeetingRequests((prev) =>
        prev.map((r) => (r.id === requestId ? { ...r, status: "pending" } : r))
      );
      setErr(String(e.message || e).replace(/^HTTP \d+:\s*/, ""));
    }
  }

  async function handleDeny(requestId) {
    setMeetingRequests((prev) =>
      prev.map((r) => (r.id === requestId ? { ...r, status: "denied" } : r))
    );
    try {
      await apiFetch(
        `/staff/dashboard/meeting-requests/${requestId}/deny/`,
        { method: "POST" },
        { auth: true }
      );
    } catch (e) {
      setMeetingRequests((prev) =>
        prev.map((r) => (r.id === requestId ? { ...r, status: "pending" } : r))
      );
      setErr(String(e.message || e).replace(/^HTTP \d+:\s*/, ""));
    }
  }

  // Office-hours actions 
  async function handleAddOfficeHours(e) {
    e.preventDefault();
    setAddingHours(true);
    setErr("");
    try {
      const created = await apiFetch(
        "/staff/office-hours/",
        {
          method: "POST",
          body: JSON.stringify({ day_of_week: dayOfWeek, start_time: startTime, end_time: endTime }),
        },
        { auth: true }
      );
      setOfficeHours((prev) =>
        [...prev, created].sort(
          (a, b) => DAY_ORDER.indexOf(a.day_of_week) - DAY_ORDER.indexOf(b.day_of_week)
        )
      );
      setDayOfWeek("Monday");
      setStartTime("09:00");
      setEndTime("17:00");
      setSuccess("Office hours added.");
      setTimeout(() => setSuccess(""), 3000);
    } catch (e) {
      setErr(String(e.message || e).replace(/^HTTP \d+:\s*/, ""));
    } finally {
      setAddingHours(false);
    }
  }

  async function handleDeleteOfficeHours(hoursId) {
    if (!window.confirm("Delete this office hours block?")) return;
    try {
      await apiFetch(`/staff/office-hours/${hoursId}/`, { method: "DELETE" }, { auth: true });
      setOfficeHours((prev) => prev.filter((oh) => oh.id !== hoursId));
      setSuccess("Office hours deleted.");
      setTimeout(() => setSuccess(""), 3000);
    } catch (e) {
      setErr(String(e.message || e).replace(/^HTTP \d+:\s*/, ""));
    }
  }

  // Derived data

  const tabCounts = {
    pending:  meetingRequests.filter((r) => r.status === "pending").length,
    accepted: meetingRequests.filter((r) => r.status === "accepted").length,
    denied:   meetingRequests.filter((r) => r.status === "denied").length,
  };

  const filteredRequests  = meetingRequests.filter((r) => r.status === activeTab);
  const acceptedMeetings  = meetingRequests.filter((r) => r.status === "accepted");
  const sortedOfficeHours = [...officeHours].sort(
    (a, b) => DAY_ORDER.indexOf(a.day_of_week) - DAY_ORDER.indexOf(b.day_of_week)
  );

  // Render 

  return (
    <div className="sd-page">

      {/*  Topbar */}
      <div className="sd-topbar">
        <h1>Meeting Requests</h1>
        <div className="sd-topbar-actions">
          <NotificationBell
            onNotificationClick={(notif) => {
              if (notif.meeting_request_id) navigate("/staff/dashboard/meeting-requests");
              else if (notif.ticket_id)     navigate(`/staff/dashboard/${notif.ticket_id}`);
            }}
          />
          <button className="sd-meeting-btn" onClick={() => navigate("/staff/dashboard")}>
            ← Dashboard
          </button>
          <button className="sd-logout-btn" onClick={handleLogout}>Log Out</button>
        </div>
      </div>

      {/* Global alerts */}
      {err     && <div className="smr-alert smr-alert-error">{err}</div>}
      {success && <div className="smr-alert smr-alert-success">{success}</div>}

      {/* Body */}
      {loading ? (
        <p className="smr-loading">Loading…</p>
      ) : (
        <div className="smr-layout">

          {/* ══ Left column ══ */}
          <div className="smr-main">

            {/* Requests panel */}
            <div className="smr-panel">

              {/* Tabs */}
              <div className="smr-tabs" role="tablist">
                {TABS.map(({ key, label }) => (
                  <button
                    key={key}
                    role="tab"
                    aria-selected={activeTab === key}
                    className={`smr-tab${activeTab === key ? " smr-tab-active" : ""}`}
                    onClick={() => setActiveTab(key)}
                  >
                    {label}
                    {tabCounts[key] > 0 && (
                      <span className="smr-tab-count">{tabCounts[key]}</span>
                    )}
                  </button>
                ))}
              </div>

              {/* Scrollable request cards */}
              <div className="smr-requests-scroll">
                {filteredRequests.length === 0 ? (
                  <p className="smr-empty">
                    No {TABS.find((t) => t.key === activeTab)?.label.toLowerCase()} requests.
                  </p>
                ) : (
                  filteredRequests.map((req) => (
                    <RequestCard
                      key={req.id}
                      req={req}
                      onAccept={handleAccept}
                      onDeny={handleDeny}
                    />
                  ))
                )}
              </div>
            </div>

            {/* Calendar panel */}
            <div className="smr-panel">
              <h2 className="smr-panel-title">Weekly Schedule</h2>
              <WeeklyCalendar
                officeHours={officeHours}
                acceptedMeetings={acceptedMeetings}
              />
            </div>
          </div>

          {/* ══ Right sidebar ══ */}
          <aside className="smr-sidebar">

            {/* Office hours list */}
            <div className="smr-panel">
              <h2 className="smr-panel-title">Office Hours</h2>
              {sortedOfficeHours.length === 0 ? (
                <p className="smr-empty">No office hours set.</p>
              ) : (
                <ul className="smr-oh-list">
                  {sortedOfficeHours.map((oh) => (
                    <li key={oh.id} className="smr-oh-item">
                      <span className="smr-oh-day">{oh.day_of_week.slice(0, 3)}</span>
                      <span className="smr-oh-time">
                        {oh.start_time.slice(0, 5)} – {oh.end_time.slice(0, 5)}
                      </span>
                      <button
                        className="smr-oh-del"
                        onClick={() => handleDeleteOfficeHours(oh.id)}
                        title="Delete block"
                      >
                        ×
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>

            {/* Add office hours form */}
            <div className="smr-panel">
              <h2 className="smr-panel-title">Add Office Hours</h2>
              <form onSubmit={handleAddOfficeHours} className="smr-oh-form">
                <div className="smr-oh-field">
                  <label className="smr-oh-label">Day</label>
                  <select
                    value={dayOfWeek}
                    onChange={(e) => setDayOfWeek(e.target.value)}
                    className="smr-oh-input"
                  >
                    {DAY_ORDER.map((d) => <option key={d}>{d}</option>)}
                  </select>
                </div>
                <div className="smr-oh-field">
                  <label className="smr-oh-label">Start</label>
                  <input
                    type="time"
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)}
                    className="smr-oh-input"
                    required
                  />
                </div>
                <div className="smr-oh-field">
                  <label className="smr-oh-label">End</label>
                  <input
                    type="time"
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)}
                    className="smr-oh-input"
                    required
                  />
                </div>
                <button
                  type="submit"
                  disabled={addingHours}
                  className="smr-btn smr-btn-primary"
                >
                  {addingHours ? "Adding…" : "Add Block"}
                </button>
              </form>
            </div>

          </aside>
        </div>
      )}
    </div>
  );
}

export default StaffMeetingRequestsPage;
