import { useEffect, useState } from "react";
import { useDispatch, useSelector } from "react-redux";
import { apiFetch, authHeaders } from "./api";
import { checkAuth } from "./store/slices/authSlice";
import UserNavbar from "./components/UserNavbar";
import "./Profile.css";

export default function Profile() {
  const dispatch = useDispatch();
  const { user: reduxUser, loading } = useSelector((state) => state.auth);
  const [editedUser, setEditedUser] = useState(null);
  const [err, setErr] = useState("");
  const [success, setSuccess] = useState("");
  const [saving, setSaving] = useState(false);

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
    if (!editedUser) return;

    setErr("");
    setSuccess("");
    setSaving(true);

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
      setSuccess("Profile updated successfully.");
    } catch (e) {
      setErr(e.message || "Save failed");
    } finally {
      setSaving(false);
    }
  }

  function resetChanges() {
    if (!reduxUser) return;
    setEditedUser(reduxUser);
    setErr("");
    setSuccess("");
  }

  if (loading || !editedUser) {
    return (
      <>
        <UserNavbar />
        <div className="profile-page">
          <div className="profile-card">{err || "Loading..."}</div>
        </div>
      </>
    );
  }

  return (
    <>
      <UserNavbar />
      <div className="profile-page">
        <section className="profile-card">
          <h2 className="profile-title">My Profile</h2>

          {err && <p className="profile-alert profile-alert-error">{err}</p>}
          {success && <p className="profile-alert profile-alert-success">{success}</p>}

          <div className="profile-static-grid">
            <div className="profile-static-item">
              <span className="profile-label">Role</span>
              <span className="profile-value">{editedUser.role}</span>
            </div>
            <div className="profile-static-item">
              <span className="profile-label">Email</span>
              <span className="profile-value">{editedUser.email}</span>
            </div>
            <div className="profile-static-item">
              <span className="profile-label">K Number</span>
              <span className="profile-value">{editedUser.k_number}</span>
            </div>
          </div>

          <div className="profile-form-grid">
            <label className="profile-field">
              <span className="profile-label">First name</span>
              <input
                value={editedUser.first_name ?? ""}
                onChange={(e) =>
                  setEditedUser({ ...editedUser, first_name: e.target.value })
                }
                placeholder="First name"
              />
            </label>

            <label className="profile-field">
              <span className="profile-label">Last name</span>
              <input
                value={editedUser.last_name ?? ""}
                onChange={(e) =>
                  setEditedUser({ ...editedUser, last_name: e.target.value })
                }
                placeholder="Last name"
              />
            </label>

            <label className="profile-field profile-field-full">
              <span className="profile-label">Department</span>
              <input
                value={editedUser.department ?? ""}
                onChange={(e) =>
                  setEditedUser({ ...editedUser, department: e.target.value })
                }
                placeholder="Department"
              />
            </label>
          </div>

          <div className="profile-actions">
            <button
              className="profile-btn profile-btn-secondary"
              onClick={resetChanges}
              type="button"
              disabled={saving}
            >
              Cancel
            </button>
            <button
              className="profile-btn profile-btn-primary"
              onClick={save}
              type="button"
              disabled={saving}
            >
              {saving ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </section>
      </div>
    </>
  );
}
