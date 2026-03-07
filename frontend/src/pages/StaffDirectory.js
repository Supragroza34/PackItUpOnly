import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../api";
import "./StaffDirectory.css";



export default function StaffDirectory() {
  const [department, setDepartment] = useState("");
  const [departments, setDepartments] = useState([]);
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);

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


  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const query = department ? `?department=${encodeURIComponent(department)}` : "";
        const data = await apiFetch(`/staff/${query}`, {}, { auth: true });
        setStaff(data);

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
        <>

          <div className="staff-grid">
            {staff.map((s) => (
              <div key={s.id} className="staff-card">
                <div>
                  <div className="staff-name">{s.first_name} {s.last_name}</div>
                  <div style={{ opacity: 0.85 }}>{s.department || "—"}</div>
                </div>

                <div style={{ marginTop: 10 }}>
                  <Link to={`/staff/${s.id}`}>Book Meeting</Link>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}