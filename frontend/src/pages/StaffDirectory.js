import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../api";



export default function StaffDirectory() {
  const [department, setDepartment] = useState("");
  const [departments, setDepartments] = useState([]);
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);

  // Load departments (optional endpoint)
  useEffect(() => {
    (async () => {
      try {
        const deps = await apiFetch("/staff/departments/");
        setDepartments(deps);
      } catch (e) {
        setDepartments([]);
      }
    })();
  }, []);

  // Load staff list (with optional department filter)
  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const query = department ? `?department=${encodeURIComponent(department)}` : "";
        const data = await apiFetch(`/staff/${query}`, {}, { auth: true });
        setStaff(data);

        // If departments endpoint doesn't exist, derive departments from staff data
        if (departments.length === 0) {
          const derived = Array.from(
            new Set((data || []).map((s) => (s.department || "").trim()).filter(Boolean))
          ).sort();
          setDepartments(derived);
        }
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [department]);

  return (
    <div style={{ padding: 24 }}>
      <h2>Staff Directory</h2>

      <div style={{ margin: "12px 0" }}>
        <label style={{ marginRight: 8 }}>Department:</label>
        <select value={department} onChange={(e) => setDepartment(e.target.value)}>
          <option value="">All</option>
          {departments.map((d) => (
            <option key={d} value={d}>
              {d}
            </option>
          ))}
        </select>
      </div>

      {loading ? (
        <p>Loading...</p>
      ) : staff.length === 0 ? (
        <p>No staff found.</p>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(260px, 1fr))",
            gap: 12,
          }}
        >
          {staff.map((s) => (
            <div
              key={s.id}
              style={{ border: "1px solid #2b2b2b", borderRadius: 10, padding: 12 }}
            >
              <div style={{ fontWeight: 600 }}>
                {s.first_name} {s.last_name}
              </div>
              <div style={{ opacity: 0.85 }}>{s.department || "—"}</div>

              <div style={{ marginTop: 10, display: "flex", gap: 8 }}>
                <Link to={`/staff/${s.id}`}>Book Meeting</Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}