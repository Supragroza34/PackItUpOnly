import React, { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { apiFetch } from "../api";

export default function StaffMeetingPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [staff, setStaff] = useState(null);
  const [loading, setLoading] = useState(true);

  // booking form (simple ticket-based request)
  const [subject, setSubject] = useState("Meeting request");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [err, setErr] = useState("");

  useEffect(() => {
    (async () => {
      setLoading(true);
      setErr("");
      try {
        const data = await apiFetch(`/staff/${id}/`, {}, { auth: true });
        setStaff(data);
      } catch (e) {
        setErr(String(e.message || e));
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  async function submitRequest(e) {
    e.preventDefault();
    setSubmitting(true);
    setErr("");

    try {
      const payload = {
        subject,
        description,
        staff_id: Number(id),
      };

      await apiFetch("/tickets/", {
        method: "POST",
        body: JSON.stringify(payload),
      }, { auth: true });

      // Go somewhere after success
      navigate("/dashboard");
    } catch (e2) {
      setErr(String(e2.message || e2));
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div style={{ padding: 24 }}>Loading...</div>;
  if (err) return <div style={{ padding: 24, color: "crimson" }}>{err}</div>;
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

      <hr style={{ margin: "18px 0" }} />

      <h3>Book a meeting</h3>

      <form onSubmit={submitRequest} style={{ display: "grid", gap: 10 }}>
        <input
          value={subject}
          onChange={(e) => setSubject(e.target.value)}
          placeholder="Subject"
        />
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          placeholder="Describe what you want to meet about…"
          rows={5}
        />
        <button disabled={submitting}>
          {submitting ? "Submitting..." : "Send request"}
        </button>
      </form>

      {err && <p style={{ color: "crimson" }}>{err}</p>}
    </div>
  );
}