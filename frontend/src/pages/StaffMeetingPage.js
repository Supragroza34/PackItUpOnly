import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

export default function StaffMeetingPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [staff, setStaff] = useState(null);
  const [loading, setLoading] = useState(true);

  // Meeting request form
  const [meetingDatetime, setMeetingDatetime] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const data = await apiFetch(`/staff/${id}/`, {}, { auth: true });
        setStaff(data);
      } catch (e) {
        const errorMsg = String(e.message || e);
        setErr(errorMsg.replace(/^HTTP \\d+:\\s*/, ''));
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  async function submitRequest(e) {
    e.preventDefault();
    setSubmitting(true);
    setErr("");
    setSuccess("");

    // Prevent selecting past date/time on the client
    if (meetingDatetime) {
      const selected = new Date(meetingDatetime);
      const now = new Date();
      if (isNaN(selected.getTime()) || selected < now) {
        setErr("Please choose a current or future date and time.");
        setSubmitting(false);
        return;
      }
    }

    try {
      const payload = {
        staff: Number(id),
        meeting_datetime: meetingDatetime,
        description: description,
      };

      await apiFetch("/meeting-requests/", {
        method: "POST",
        body: JSON.stringify(payload),
      }, { auth: true });

      setSuccess("Meeting request submitted successfully!");
      setMeetingDatetime("");
      setDescription("");
      
    } catch (e2) {
      const errorMsg = String(e2.message || e2);
      // Remove "HTTP XXX: " prefix if present for cleaner display
      setErr(errorMsg.replace(/^HTTP \d+:\s*/, ''));
    } finally {
      setSubmitting(false);
    }
  }

  // Helper function to format office hours
  const formatOfficeHours = (officeHours) => {
    if (!officeHours || officeHours.length === 0) {
      return "No office hours set";
    }

    const dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    const sorted = [...officeHours].sort((a, b) => 
      dayOrder.indexOf(a.day_of_week) - dayOrder.indexOf(b.day_of_week)
    );

    return sorted.map(oh => 
      `${oh.day_of_week}: ${oh.start_time.substring(0, 5)} - ${oh.end_time.substring(0, 5)}`
    ).join(", ");
  };

  // Minimum selectable datetime for the picker (current moment, local)
  const minNow = (() => {
    const d = new Date();
    // adjust for local timezone so toISOString yields local-equivalent
    d.setMinutes(d.getMinutes() - d.getTimezoneOffset());
    return d.toISOString().slice(0, 16);
  })();

  if (loading) return <div style={{ padding: 24 }}>Loading...</div>;
  if (err && !staff) return (
    <div style={{ padding: 24 }}>
      <div style={{ 
        padding: 12, 
        backgroundColor: "#f8d7da", 
        color: "#721c24",
        borderRadius: 6,
        border: "1px solid #f5c6cb"
      }}>
        {err}
      </div>
    </div>
  );
  if (!staff) return <div style={{ padding: 24 }}>Not found</div>;

  return (
    <div style={{ padding: 24, maxWidth: 700 }}>
      <h2>
        {staff.first_name} {staff.last_name}
      </h2>

      <div style={{ marginBottom: 18, opacity: 0.85 }}>
        <div><b>Department:</b> {staff.department || "—"}</div>
        <div><b>Email:</b> {staff.email || "—"}</div>
        <div><b>K-number:</b> {staff.k_number || "—"}</div>
      </div>

      <div style={{ 
        padding: 12, 
        backgroundColor: "#f0f8ff", 
        borderRadius: 6,
        marginBottom: 18
      }}>
        <b>Office Hours:</b>
        <div style={{ marginTop: 6 }}>
          {formatOfficeHours(staff.office_hours)}
        </div>
      </div>

      <hr style={{ margin: "18px 0" }} />

      <h3>Request a meeting</h3>
      <p style={{ fontSize: 14, color: "#666", marginBottom: 12 }}>
        Please select a date and time within the staff member's office hours.
      </p>

      {success && (
        <div style={{ 
          padding: 12, 
          backgroundColor: "#d4edda", 
          color: "#155724",
          borderRadius: 6,
          marginBottom: 12
        }}>
          {success}
        </div>
      )}

      <form onSubmit={submitRequest} style={{ display: "grid", gap: 10 }}>
        <div>
          <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>
            Meeting Date & Time
          </label>
          <input
            type="datetime-local"
            value={meetingDatetime}
            onChange={(e) => setMeetingDatetime(e.target.value)}
            min={minNow}
            required
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        
        <div>
          <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Describe what you want to meet about…"
            required
            rows={5}
            style={{ width: "100%", padding: 8 }}
          />
        </div>
        
        <button 
          disabled={submitting}
          style={{ padding: 10, fontSize: 16 }}
        >
          {submitting ? "Submitting..." : "Send meeting request"}
        </button>
      </form>

      {err && (
        <div style={{ 
          padding: 12, 
          backgroundColor: "#f8d7da", 
          color: "#721c24",
          borderRadius: 6,
          marginTop: 12,
          border: "1px solid #f5c6cb"
        }}>
          {err}
        </div>
      )}
    </div>
  );
}