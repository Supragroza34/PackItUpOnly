import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../api";
import UserNavbar from "../components/UserNavbar";
import "./StaffDirectory.css";

const PER_PAGE = 12;

export default function StaffDirectory() {
  const [department, setDepartment] = useState("");
  const [departments, setDepartments] = useState([]);
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");

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
        setPage(1);

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

  const filtered = useMemo(() => {
    if (!search.trim()) return staff;
    const q = search.toLowerCase();
    return staff.filter((s) => {
      const full = `${s.first_name} ${s.last_name}`.toLowerCase();
      return full.includes(q);
    });
  }, [staff, search]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const paged = useMemo(
    () => filtered.slice((page - 1) * PER_PAGE, page * PER_PAGE),
    [filtered, page]
  );

  return (
    <div className="staff-page-wrapper">
      <UserNavbar />

      <div className="staff-page-bg">
        <div className="staff-page">
          <header className="staff-header">
            <h1>Staff Directory</h1>
            <p>Browse staff members and book a meeting.</p>
          </header>

          <div className="staff-controls">
            <input
              type="text"
              className="staff-search"
              placeholder="Search by name…"
              value={search}
              onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            />

            <label htmlFor="dept-filter">Department:</label>
            <select
              id="dept-filter"
              className="staff-select"
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
            >
              <option value="">All</option>
              {departments.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>

          {loading ? (
            <p className="staff-status">Loading...</p>
          ) : filtered.length === 0 ? (
            <p className="staff-status">No staff found.</p>
          ) : (
            <>
              <div className="staff-grid">
                {paged.map((s) => (
                  <div key={s.id} className="staff-card">
                    <div className="staff-card-avatar">
                      {(s.first_name?.[0] || "").toUpperCase()}
                      {(s.last_name?.[0] || "").toUpperCase()}
                    </div>
                    <div className="staff-card-body">
                      <div className="staff-name">{s.first_name} {s.last_name}</div>
                      <div className="staff-dept">{s.department || "—"}</div>
                    </div>
                    <Link className="staff-book-btn" to={`/staff/${s.id}`}>
                      Book Meeting
                    </Link>
                  </div>
                ))}
              </div>

              {totalPages > 1 && (
                <div className="staff-pagination">
                  <button
                    className="page-btn"
                    disabled={page <= 1}
                    onClick={() => setPage((p) => p - 1)}
                  >
                    &laquo; Prev
                  </button>

                  {Array.from({ length: totalPages }, (_, i) => i + 1).map((n) => (
                    <button
                      key={n}
                      className={`page-btn ${n === page ? "page-btn-active" : ""}`}
                      onClick={() => setPage(n)}
                    >
                      {n}
                    </button>
                  ))}

                  <button
                    className="page-btn"
                    disabled={page >= totalPages}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    Next &raquo;
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}