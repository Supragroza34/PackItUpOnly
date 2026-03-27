import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { apiFetch } from "../api";
import UserNavbar from '../components/UserNavbar';
import './StaffDirectory.css';

export default function StaffMeetingPage() {
  const { id } = useParams();

  const [staff, setStaff] = useState(null);
  const [loading, setLoading] = useState(true);

  // Slot selection
  const [selectedDate, setSelectedDate] = useState("");
  const [availableSlots, setAvailableSlots] = useState([]);
  const [slotsLoading, setSlotsLoading] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState("");

  // Form
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
        setErr(String(e.message || e).replace(/^HTTP \d+:\s*/, ''));
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  // Fetch available slots whenever the selected date changes
  useEffect(() => {
    if (!selectedDate) {
      setAvailableSlots([]);
      setSelectedSlot("");
      return;
    }
    let cancelled = false;
    (async () => {
      setSlotsLoading(true);
      setSelectedSlot("");
      setErr("");
      try {
        const data = await apiFetch(
          `/staff/${id}/available-slots/?date=${selectedDate}`,
          {},
          { auth: true }
        );
        if (!cancelled) setAvailableSlots(data.slots || []);
      } catch (e) {
        if (!cancelled) {
          setErr(String(e.message || e).replace(/^HTTP \d+:\s*/, ''));
          setAvailableSlots([]);
        }
      } finally {
        if (!cancelled) setSlotsLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [selectedDate, id]);

  async function submitRequest(e) {
    e.preventDefault();
    if (!selectedSlot) {
      setErr("Please select a time slot.");
      return;
    }
    setSubmitting(true);
    setErr("");
    setSuccess("");
    try {
      await apiFetch("/meeting-requests/", {
        method: "POST",
        body: JSON.stringify({
          staff: Number(id),
          meeting_datetime: selectedSlot,
          description,
        }),
      }, { auth: true });

      setSuccess("Meeting request submitted successfully!");
      // Remove slot from the list immediately so it can't be double-booked
      setAvailableSlots(prev => prev.filter(s => s !== selectedSlot));
      setSelectedSlot("");
      setDescription("");
    } catch (e2) {
      setErr(String(e2.message || e2).replace(/^HTTP \d+:\s*/, ''));
    } finally {
      setSubmitting(false);
    }
  }

  // Format ISO datetime to a readable time string (e.g. "09:15")
  // Use UTC so displayed times match the office hours (stored/shown in UTC).
  function formatTime(isoStr) {
    const d = new Date(isoStr);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'UTC' });
  }

  const formatOfficeHours = (officeHours) => {
    if (!officeHours || officeHours.length === 0) return [];
    const dayOrder = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
    return [...officeHours]
      .sort((a, b) => dayOrder.indexOf(a.day_of_week) - dayOrder.indexOf(b.day_of_week))
      .map(oh => `${oh.day_of_week}: ${oh.start_time.substring(0, 5)} – ${oh.end_time.substring(0, 5)}`);
  };

  // Earliest selectable date is today
  const todayStr = new Date().toISOString().split('T')[0];

  if (loading) return (
    <div className="staff-page-wrapper">
      <UserNavbar />
      <div className="staff-page-bg"><div className="staff-page"><p className="staff-status">Loading...</p></div></div>
    </div>
  );

  if (err && !staff) return (
    <div className="staff-page-wrapper">
      <UserNavbar />
      <div className="staff-page-bg">
        <div className="staff-page">
          <div style={{ padding: 12, backgroundColor: "#f8d7da", color: "#721c24", borderRadius: 6, border: "1px solid #f5c6cb" }}>
            {err}
          </div>
        </div>
      </div>
    </div>
  );

  if (!staff) return (
    <div className="staff-page-wrapper">
      <UserNavbar />
      <div className="staff-page-bg"><div className="staff-page"><p className="staff-status">Not found</p></div></div>
    </div>
  );

  return (
    <div className="staff-page-wrapper">
      <UserNavbar />
      <div className="staff-page-bg">
        <div className="staff-page">
          <header className="staff-header">
            <h1>{staff.first_name} {staff.last_name}</h1>
            <p>Request a meeting with this staff member.</p>
          </header>

          <div style={{ marginTop: 18 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 400px', gap: 20 }}>

              {/* Left column: staff info */}
              <div>
                <div style={{ marginBottom: 18, opacity: 0.85 }}>
                  <div><b>Department:</b> {staff.department || "—"}</div>
                  <div><b>Email:</b> {staff.email || "—"}</div>
                  <div><b>K-number:</b> {staff.k_number || "—"}</div>
                </div>

                <div style={{ padding: 12, backgroundColor: "#f0f8ff", borderRadius: 6, marginBottom: 18 }}>
                  <b>Office Hours:</b>
                  <div style={{ marginTop: 6 }}>
                    {(() => {
                      const lines = formatOfficeHours(staff.office_hours);
                      if (!lines.length) return <div>No office hours set</div>;
                      return lines.map((ln, i) => <div key={i}>{ln}</div>);
                    })()}
                  </div>
                </div>

                {err && (
                  <div style={{ padding: 12, backgroundColor: "#f8d7da", color: "#721c24", borderRadius: 6, marginTop: 12, border: "1px solid #f5c6cb" }}>
                    {err}
                  </div>
                )}
              </div>

              {/* Right column: booking form */}
              <div>
                <div style={{ background: '#fff', padding: 16, borderRadius: 8, boxShadow: '0 4px 12px rgba(0,0,0,0.06)' }}>
                  <h3 style={{ marginTop: 0 }}>Request a meeting</h3>
                  <p style={{ fontSize: 14, color: "#666", marginBottom: 12 }}>
                    Pick a date to see available 15-minute slots.
                  </p>

                  {success && (
                    <div style={{ padding: 12, backgroundColor: "#d4edda", color: "#155724", borderRadius: 6, marginBottom: 12 }}>
                      {success}
                    </div>
                  )}

                  <form onSubmit={submitRequest} style={{ display: "grid", gap: 12 }}>

                    {/* Date picker */}
                    <div>
                      <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>
                        Date
                      </label>
                      <input
                        type="date"
                        value={selectedDate}
                        min={todayStr}
                        onChange={e => { setSelectedDate(e.target.value); setSuccess(""); }}
                        required
                        style={{ width: "100%", padding: 8 }}
                      />
                    </div>

                    {/* Slot grid */}
                    {selectedDate && (
                      <div>
                        <label style={{ display: "block", marginBottom: 6, fontWeight: 500 }}>
                          Available slots
                        </label>

                        {slotsLoading && (
                          <p style={{ color: "#666", fontSize: 14 }}>Loading slots…</p>
                        )}

                        {!slotsLoading && availableSlots.length === 0 && (
                          <p style={{ color: "#999", fontSize: 14 }}>
                            No available slots on this date.
                          </p>
                        )}

                        {!slotsLoading && availableSlots.length > 0 && (
                          <div style={{
                            display: 'flex',
                            flexWrap: 'wrap',
                            gap: 8,
                          }}>
                            {availableSlots.map(slot => (
                              <button
                                key={slot}
                                type="button"
                                onClick={() => { setSelectedSlot(slot); setErr(""); }}
                                style={{
                                  padding: '6px 12px',
                                  borderRadius: 6,
                                  border: selectedSlot === slot
                                    ? '2px solid #003f7f'
                                    : '1px solid #ccc',
                                  backgroundColor: selectedSlot === slot
                                    ? '#003f7f'
                                    : '#f5f5f5',
                                  color: selectedSlot === slot ? '#fff' : '#333',
                                  cursor: 'pointer',
                                  fontSize: 14,
                                  fontWeight: selectedSlot === slot ? 600 : 400,
                                }}
                              >
                                {formatTime(slot)}
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Description */}
                    <div>
                      <label style={{ display: "block", marginBottom: 4, fontWeight: 500 }}>
                        Description
                      </label>
                      <textarea
                        value={description}
                        onChange={e => setDescription(e.target.value)}
                        placeholder="Describe what you want to meet about…"
                        required
                        rows={4}
                        style={{ width: "100%", padding: 8 }}
                      />
                    </div>

                    <button
                      disabled={submitting || !selectedSlot}
                      style={{
                        padding: 10,
                        fontSize: 16,
                        opacity: (!selectedSlot || submitting) ? 0.6 : 1,
                        cursor: (!selectedSlot || submitting) ? 'not-allowed' : 'pointer',
                      }}
                    >
                      {submitting ? "Submitting…" : "Send meeting request"}
                    </button>
                  </form>
                </div>
              </div>

            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
