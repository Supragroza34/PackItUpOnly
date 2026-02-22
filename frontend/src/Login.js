import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";

export default function Login() {
  const nav = useNavigate();
  const { login: authLogin, user } = useAuth();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  
  // Refs to handle autofill properly
  const usernameRef = useRef(null);
  const passwordRef = useRef(null);

  // Sync autofilled values with state
  useEffect(() => {
    const syncAutofill = () => {
      if (usernameRef.current && usernameRef.current.value !== username) {
        setUsername(usernameRef.current.value);
      }
      if (passwordRef.current && passwordRef.current.value !== password) {
        setPassword(passwordRef.current.value);
      }
    };
    
    // Check for autofill after a short delay
    const timer = setTimeout(syncAutofill, 100);
    return () => clearTimeout(timer);
  }, []);

  // Redirect when user is set in AuthContext
  useEffect(() => {
    if (user && loading) {
      console.log("User loaded in context, redirecting...");
      // Redirect based on user role
      if (user.role === "admin" || user.is_superuser || user.is_staff) {
        console.log("Redirecting to admin dashboard");
        nav("/admin/dashboard", { replace: true });
      } else {
        console.log("Redirecting to profile");
        nav("/profile", { replace: true });
      }
    }
  }, [user, loading, nav]);

  async function onSubmit(e) {
    e.preventDefault();
    
    if (loading) return; // Prevent double submission
    
    setErr("");
    setLoading(true);
    
    // Get values directly from inputs to handle autofill properly
    const usernameValue = usernameRef.current.value.trim();
    const passwordValue = passwordRef.current.value;
    
    // Validate inputs
    if (!usernameValue || !passwordValue) {
      setErr("Please enter both username and password");
      setLoading(false);
      return;
    }
    
    try {
      console.log("Attempting login with:", usernameValue);
      
      // Use AuthContext's login method which properly updates user state
      const result = await authLogin(usernameValue, passwordValue);
      
      if (!result.success) {
        throw new Error(result.error || "Login failed");
      }
      
      console.log("Login successful");
      // Navigation will happen in the useEffect when user state is updated
      
      // Redirect based on user role - don't setLoading(false) here!
      if (userProfile.role === "admin" || userProfile.is_superuser || userProfile.is_staff) {
        console.log("Redirecting to admin dashboard");
        nav("/admin/dashboard", { replace: true });
      } else {
        //console.log("Redirecting to profile");
        //nav("/profile", { replace: true });

        console.log("Redirecting to user dashboard");
        nav("/dashboard", { replace: true });
      }
    } catch (e2) {
      console.error("Login error:", e2);
      setErr("Login failed: " + (e2.message || "Please check your credentials."));
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 420, margin: "40px auto", padding: "20px" }}>
      <h2>KCL Ticketing System - Login</h2>
      {err && <p style={{ color: "crimson", background: "#ffe6e6", padding: "10px", borderRadius: "5px" }}>{err}</p>}
      <form onSubmit={onSubmit} style={{ display: "grid", gap: 10 }} autoComplete="on">
        <input 
          ref={usernameRef}
          name="username"
          value={username} 
          onChange={(e) => setUsername(e.target.value)} 
          placeholder="Username" 
          disabled={loading}
          autoComplete="username"
          required
        />
        <input 
          ref={passwordRef}
          name="password"
          value={password} 
          onChange={(e) => setPassword(e.target.value)} 
          placeholder="Password" 
          type="password"
          disabled={loading}
          autoComplete="current-password"
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
