import { useEffect, useState } from "react";
import { apiFetch, authHeaders } from "./api";

export function Profile() {
  const [user, setUser] = useState(null);
  const [err, setErr] = useState("");

  async function load() {
    setErr("");
    try {
      const me = await apiFetch("/users/me/", { headers: authHeaders() });
      setUser(me);
    } catch {
      setErr("Not logged in (or token expired).");
    }
  }

  useEffect(() => { load(); }, []);

  async function save() {
    setErr("");
    try {
      const updated = await apiFetch("/users/me/", {
        method: "PATCH",
        headers: authHeaders(),
        body: JSON.stringify({
          first_name: user.first_name,
          last_name: user.last_name,
          department: user.department,
        }),
      });
      setUser(updated);
    } catch (e) {
      setErr("Save failed");
    }
  }

  if (!user) return <div style={{ maxWidth: 520, margin: "40px auto" }}>{err || "Loading..."}</div>;

  return (
    <div style={{ maxWidth: 520, margin: "40px auto" }}>
      <h2>Profile</h2>
      {err && <p style={{ color: "crimson" }}>{err}</p>}

      <div style={{ display: "grid", gap: 10 }}>
        <div><b>Role:</b> {user.role}</div>
        <div><b>Email:</b> {user.email}</div>
        <div><b>K Number:</b> {user.k_number}</div>

        <input
          value={user.first_name ?? ""}
          onChange={(e) => setUser({ ...user, first_name: e.target.value })}
          placeholder="first name"
        />
        <input
          value={user.last_name ?? ""}
          onChange={(e) => setUser({ ...user, last_name: e.target.value })}
          placeholder="last name"
        />
        <input
          value={user.department ?? ""}
          onChange={(e) => setUser({ ...user, department: e.target.value })}
          placeholder="department"
        />

        <button onClick={save}>Save</button>
        <button
          onClick={() => {
            localStorage.removeItem("access");
            localStorage.removeItem("refresh");
            setUser(null);
          }}
        >
          Logout
        </button>
      </div>
    </div>
  );
}
