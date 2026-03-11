import { useState } from "react";
import { apiFetch } from "./api";
import { useNavigate } from "react-router-dom";
import "./Login.css";

export default function Signup() {
  const nav = useNavigate();
  const [form, setForm] = useState({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
    k_number: "",
    department: "",
  });
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  const onChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  async function onSubmit(e) {
    e.preventDefault();
    if (loading) return;
    setErr("");
    setLoading(true);
    try {
      await apiFetch("/auth/register/", {
        method: "POST",
        body: JSON.stringify(form),
      });
      nav("/login");
    } catch (e2) {
      setErr(String(e2.message));
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">Create your KCL account</h1>
        <p className="login-subtitle">Sign up to get started</p>

        {err && (
          <p className="login-error" role="alert">
            {err}
          </p>
        )}

        <form className="login-form" onSubmit={onSubmit} autoComplete="on">
          <div className="login-field">
            <label htmlFor="signup-username">Username</label>
            <input
              id="signup-username"
              name="username"
              type="text"
              placeholder="Choose a username"
              value={form.username}
              onChange={onChange}
              required
              className="login-input"
              disabled={loading}
              autoComplete="username"
            />
          </div>

          <div className="login-field">
            <label htmlFor="signup-email">Email</label>
            <input
              id="signup-email"
              name="email"
              type="email"
              placeholder="Your email address"
              value={form.email}
              onChange={onChange}
              required
              className="login-input"
              disabled={loading}
              autoComplete="email"
            />
          </div>

          <div className="login-field">
            <label htmlFor="signup-password">Password</label>
            <input
              id="signup-password"
              name="password"
              type="password"
              placeholder="Create a password"
              value={form.password}
              onChange={onChange}
              required
              className="login-input"
              disabled={loading}
              autoComplete="new-password"
            />
          </div>

          <div className="login-field">
            <label htmlFor="signup-first-name">First name</label>
            <input
              id="signup-first-name"
              name="first_name"
              type="text"
              placeholder="First name"
              value={form.first_name}
              onChange={onChange}
              className="login-input"
              disabled={loading}
            />
          </div>

          <div className="login-field">
            <label htmlFor="signup-last-name">Last name</label>
            <input
              id="signup-last-name"
              name="last_name"
              type="text"
              placeholder="Last name"
              value={form.last_name}
              onChange={onChange}
              className="login-input"
              disabled={loading}
            />
          </div>

          <div className="login-field">
            <label htmlFor="signup-k-number">K Number</label>
            <input
              id="signup-k-number"
              name="k_number"
              type="text"
              placeholder="K number"
              value={form.k_number}
              onChange={onChange}
              required
              className="login-input"
              disabled={loading}
            />
          </div>

          <div className="login-field">
            <label htmlFor="signup-department">Department</label>
            <input
              id="signup-department"
              name="department"
              type="text"
              placeholder="Department"
              value={form.department}
              onChange={onChange}
              className="login-input"
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="login-submit"
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="login-footer">
          Already have an account? <a href="/login">Sign in</a>
        </p>
      </div>
    </div>
  );
}
