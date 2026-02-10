import { useState } from "react";
import { apiFetch } from "./api";
import { useNavigate } from "react-router-dom";

export function Login() {
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    try {
      const data = await apiFetch("/auth/token/", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);
      nav("/profile");
    } catch (e2) {
      setErr("Login failed");
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "40px auto" }}>
      <h2>Login</h2>
      {err && <p style={{ color: "crimson" }}>{err}</p>}
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 10 }}>
        <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="username" />
        <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" type="password" />
        <button type="submit">Login</button>
      </form>
    </div>
  );
}
