import { useState } from "react";
import { apiFetch, authHeaders } from "./api";
import { useNavigate } from "react-router-dom";

export default function Login() {
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e) {
    e.preventDefault();
    
    if (loading) return; // Prevent double submission
    
    setErr("");
    setLoading(true);
    
    try {
      console.log("Attempting login with:", username);
      const data = await apiFetch("/auth/token/", {
        method: "POST",
        body: JSON.stringify({ username, password }),
      });
      
      console.log("Login successful, tokens received:", data);
      localStorage.setItem("access", data.access);
      localStorage.setItem("refresh", data.refresh);
      
      // Fetch user profile to check role
      console.log("Fetching user profile...");
      const userProfile = await apiFetch("/users/me/", {
        headers: authHeaders(),
      });
      
      console.log("User profile:", userProfile);
      
      // Redirect based on user role - don't setLoading(false) here!
      if (userProfile.role === "admin" || userProfile.is_superuser || userProfile.is_staff) {
        console.log("Redirecting to admin dashboard");
        nav("/admin/dashboard", { replace: true });
      } else {
        console.log("Redirecting to profile");
        nav("/profile", { replace: true });
      }
    } catch (e2) {
      console.error("Login error:", e2);
      setErr("Login failed: " + (e2.message || "Please check your credentials."));
      setLoading(false); // Only reset loading on error
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "40px auto", padding: "20px" }}>
      <h2>KCL Ticketing System - Login</h2>
      {err && <p style={{ color: "crimson", background: "#ffe6e6", padding: "10px", borderRadius: "5px" }}>{err}</p>}
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 10 }}>
        <input 
          value={username} 
          onChange={(e) => setUsername(e.target.value)} 
          placeholder="Username" 
          disabled={loading}
          required
        />
        <input 
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          placeholder="Password" 
          type="password"
          disabled={loading}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "Logging in..." : "Login"}
        </button>
      </form>
      <p style={{ marginTop: "15px", textAlign: "center" }}>
        Don't have an account? <a href="/signup">Sign up</a>
      </p>
    </div>
  );
}
