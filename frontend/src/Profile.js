import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { apiFetch, authHeaders } from "./api";
import { logout as logoutAction, checkAuth } from "./store/slices/authSlice";
import { useNavigate } from "react-router-dom";

export default function Profile() {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { user: reduxUser, loading } = useSelector((state) => state.auth);
  const [editedUser, setEditedUser] = useState(null);
  const [err, setErr] = useState("");

  // Load user from Redux on mount
  useEffect(() => {
    dispatch(checkAuth());
  }, [dispatch]);

  // Sync Redux user to local editing state
  useEffect(() => {
    if (reduxUser) {
      setEditedUser(reduxUser);
    }
  }, [reduxUser]);

  async function save() {
    setErr("");
    try {
      const updated = await apiFetch("/users/me/", {
        method: "PATCH",
        headers: authHeaders(),
        body: JSON.stringify({
          first_name: editedUser.first_name,
          last_name: editedUser.last_name,
          department: editedUser.department,
        }),
      });
      setEditedUser(updated);
      // Refresh auth to update Redux state
      dispatch(checkAuth());
    } catch (e) {
      setErr("Save failed");
    }
  }

  const handleLogout = async () => {
    await dispatch(logoutAction());
    navigate("/login");
  };

  if (loading || !editedUser) {
    return <div style={{ maxWidth: 520, margin: "40px auto" }}>{err || "Loading..."}</div>;
  }

  return (
    <div style={{ maxWidth: 520, margin: "40px auto" }}>
      <h2>Profile</h2>
      {err && <p style={{ color: "crimson" }}>{err}</p>}

      <div style={{ display: "grid", gap: 10 }}>
        <div><b>Role:</b> {editedUser.role}</div>
        <div><b>Email:</b> {editedUser.email}</div>
        <div><b>K Number:</b> {editedUser.k_number}</div>

        <input
          value={editedUser.first_name ?? ""}
          onChange={(e) => setEditedUser({ ...editedUser, first_name: e.target.value })}
          placeholder="first name"
        />
        <input
          value={editedUser.last_name ?? ""}
          onChange={(e) => setEditedUser({ ...editedUser, last_name: e.target.value })}
          placeholder="last name"
        />
        <input
          value={editedUser.department ?? ""}
          onChange={(e) => setEditedUser({ ...editedUser, department: e.target.value })}
          placeholder="department"
        />

        <button onClick={save}>Save</button>
        <button onClick={handleLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}
