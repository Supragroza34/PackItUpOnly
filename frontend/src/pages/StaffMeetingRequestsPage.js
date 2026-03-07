import { useEffect, useState } from "react";
import { apiFetch } from "../api";

function StaffMeetingRequestsPage() {
  const [meetingRequests, setMeetingRequests] = useState([]);
  const [officeHours, setOfficeHours] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  const [success, setSuccess] = useState("");

  // Office hours form
  const [dayOfWeek, setDayOfWeek] = useState("Monday");
  const [startTime, setStartTime] = useState("09:00");
  const [endTime, setEndTime] = useState("17:00");
  const [addingHours, setAddingHours] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  async function loadData() {
    setLoading(true);
    setErr("");
    setSuccess("");
    try {
      const [requestsData, hoursData] = await Promise.all([
        apiFetch("/staff/dashboard/meeting-requests/", {}, { auth: true }),
        apiFetch("/staff/office-hours/", {}, { auth: true }),
      ]);
      setMeetingRequests(requestsData);
      setOfficeHours(hoursData);
    } catch (e) {
      const errorMsg = String(e.message || e);
      setErr(errorMsg.replace(/^HTTP \\d+:\\s*/, ''));
    } finally {
      setLoading(false);
    }
  }

  async function handleAccept(requestId) {
    try {
      await apiFetch(`/staff/dashboard/meeting-requests/${requestId}/accept/`, {
        method: "POST",
      }, { auth: true });
      setErr("");
      setSuccess("Meeting request accepted successfully!");
      setTimeout(() => setSuccess(""), 3000);
      loadData(); // Reload data
    } catch (e) {
      const errorMsg = String(e.message || e).replace(/^HTTP \d+:\s*/, '');
      setErr(`Error accepting request: ${errorMsg}`);
    }
  }

  async function handleDeny(requestId) {
    try {
      await apiFetch(`/staff/dashboard/meeting-requests/${requestId}/deny/`, {
        method: "POST",
      }, { auth: true });
      setErr("");
      setSuccess("Meeting request denied.");
      setTimeout(() => setSuccess(""), 3000);
      loadData(); // Reload data
    } catch (e) {
      const errorMsg = String(e.message || e).replace(/^HTTP \d+:\s*/, '');
      setErr(`Error denying request: ${errorMsg}`);
    }
  }

  async function handleAddOfficeHours(e) {
    e.preventDefault();
    setAddingHours(true);
    setErr("");

    try {
      await apiFetch("/staff/office-hours/", {
        method: "POST",
        body: JSON.stringify({
          day_of_week: dayOfWeek,
          start_time: startTime,
          end_time: endTime,
        }),
      }, { auth: true });
      
      // Reset form
      setDayOfWeek("Monday");
      setStartTime("09:00");
      setEndTime("17:00");
      
      setSuccess("Office hours added successfully!");
      setTimeout(() => setSuccess(""), 3000);
      loadData(); // Reload data
    } catch (e) {
      const errorMsg = String(e.message || e).replace(/^HTTP \d+:\s*/, '');
      setErr(errorMsg);
    } finally {
      setAddingHours(false);
    }
  }

  async function handleDeleteOfficeHours(hoursId) {
    if (!window.confirm("Are you sure you want to delete this office hours block?")) {
      return;
    }

    try {
      await apiFetch(`/staff/office-hours/${hoursId}/`, {
        method: "DELETE",
      }, { auth: true });
      setErr("");
      setSuccess("Office hours deleted successfully!");
      setTimeout(() => setSuccess(""), 3000);
      loadData(); // Reload data
    } catch (e) {
      const errorMsg = String(e.message || e).replace(/^HTTP \d+:\s*/, '');
      setErr(`Error deleting office hours: ${errorMsg}`);
    }
  }

  const formatDateTime = (datetime) => {
    const date = new Date(datetime);
    return date.toLocaleString('en-GB', {
      weekday: 'short',
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending: { bg: "#fff3cd", text: "#856404" },
      accepted: { bg: "#d4edda", text: "#155724" },
      denied: { bg: "#f8d7da", text: "#721c24" }
    };
    const color = colors[status] || colors.pending;
    
    return (
      <span style={{
        padding: "4px 8px",
        borderRadius: 4,
        fontSize: 12,
        fontWeight: 500,
        backgroundColor: color.bg,
        color: color.text
      }}>
        {status.toUpperCase()}
      </span>
    );
  };

  if (loading) return <div style={{ padding: 24 }}>Loading...</div>;

  return (
    <div style={{ padding: 24, maxWidth: 1000 }}>
      <h1>Meeting Requests & Office Hours</h1>

      {err && <div style={{ padding: 12, backgroundColor: "#f8d7da", color: "#721c24", borderRadius: 6, marginBottom: 18 }}>{err}</div>}
      {success && <div style={{ padding: 12, backgroundColor: "#d4edda", color: "#155724", borderRadius: 6, marginBottom: 18 }}>{success}</div>}

      {/* Meeting Requests Section */}
      <section style={{ marginBottom: 40 }}>
        <h2>Incoming Meeting Requests</h2>
        {meetingRequests.length === 0 ? (
          <p style={{ color: "#666", fontStyle: "italic" }}>No meeting requests yet.</p>
        ) : (
          <div style={{ display: "grid", gap: 16 }}>
            {meetingRequests.map(request => (
              <div key={request.id} style={{
                border: "1px solid #ddd",
                borderRadius: 8,
                padding: 16,
                backgroundColor: "#fff"
              }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: 12 }}>
                  <div>
                    <h3 style={{ margin: 0, marginBottom: 4 }}>
                      {request.student_name} ({request.student_k_number})
                    </h3>
                    <div style={{ fontSize: 14, color: "#666" }}>
                      {request.student_email}
                    </div>
                  </div>
                  {getStatusBadge(request.status)}
                </div>

                <div style={{ marginBottom: 8 }}>
                  <strong>Requested Time:</strong> {formatDateTime(request.meeting_datetime)}
                </div>

                <div style={{ marginBottom: 12 }}>
                  <strong>Description:</strong>
                  <div style={{ marginTop: 4, padding: 8, backgroundColor: "#f9f9f9", borderRadius: 4 }}>
                    {request.description}
                  </div>
                </div>

                {request.status === "pending" && (
                  <div style={{ display: "flex", gap: 8 }}>
                    <button
                      onClick={() => handleAccept(request.id)}
                      style={{
                        padding: "8px 16px",
                        backgroundColor: "#28a745",
                        color: "white",
                        border: "none",
                        borderRadius: 4,
                        cursor: "pointer"
                      }}
                    >
                      Accept
                    </button>
                    <button
                      onClick={() => handleDeny(request.id)}
                      style={{
                        padding: "8px 16px",
                        backgroundColor: "#dc3545",
                        color: "white",
                        border: "none",
                        borderRadius: 4,
                        cursor: "pointer"
                      }}
                    >
                      Deny
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Office Hours Section */}
      <section>
        <h2>My Office Hours</h2>
        
        {/* Current Office Hours */}
        <div style={{ marginBottom: 20 }}>
          <h3 style={{ fontSize: 18 }}>Current Schedule</h3>
          {officeHours.length === 0 ? (
            <p style={{ color: "#666", fontStyle: "italic" }}>No office hours set. Add some below.</p>
          ) : (
            <div style={{ display: "grid", gap: 8 }}>
              {officeHours.map(oh => (
                <div key={oh.id} style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: 12,
                  border: "1px solid #ddd",
                  borderRadius: 6,
                  backgroundColor: "#f8f9fa"
                }}>
                  <span>
                    <strong>{oh.day_of_week}:</strong> {oh.start_time.substring(0, 5)} - {oh.end_time.substring(0, 5)}
                  </span>
                  <button
                    onClick={() => handleDeleteOfficeHours(oh.id)}
                    style={{
                      padding: "4px 12px",
                      backgroundColor: "#dc3545",
                      color: "white",
                      border: "none",
                      borderRadius: 4,
                      cursor: "pointer",
                      fontSize: 12
                    }}
                  >
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Add Office Hours Form */}
        <div style={{ padding: 16, border: "1px solid #ddd", borderRadius: 8, backgroundColor: "#f9f9f9" }}>
          <h3 style={{ fontSize: 18, marginTop: 0 }}>Add Office Hours Block</h3>
          <form onSubmit={handleAddOfficeHours} style={{ display: "grid", gap: 12 }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
              <div>
                <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>Day</label>
                <select
                  value={dayOfWeek}
                  onChange={(e) => setDayOfWeek(e.target.value)}
                  style={{ width: "100%", padding: 8 }}
                >
                  <option>Monday</option>
                  <option>Tuesday</option>
                  <option>Wednesday</option>
                  <option>Thursday</option>
                  <option>Friday</option>
                  <option>Saturday</option>
                  <option>Sunday</option>
                </select>
              </div>
              
              <div>
                <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>Start Time</label>
                <input
                  type="time"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  style={{ width: "100%", padding: 8 }}
                  required
                />
              </div>
              
              <div>
                <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>End Time</label>
                <input
                  type="time"
                  value={endTime}
                  onChange={(e) => setEndTime(e.target.value)}
                  style={{ width: "100%", padding: 8 }}
                  required
                />
              </div>
            </div>
            
            <button
              type="submit"
              disabled={addingHours}
              style={{
                padding: "10px 16px",
                backgroundColor: "#007bff",
                color: "white",
                border: "none",
                borderRadius: 4,
                cursor: "pointer",
                fontSize: 14,
                fontWeight: 500
              }}
            >
              {addingHours ? "Adding..." : "Add Office Hours"}
            </button>
          </form>
        </div>
      </section>
    </div>
  );
}

export default StaffMeetingRequestsPage;