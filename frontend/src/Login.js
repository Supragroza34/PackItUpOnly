import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { login as loginAction, checkAuth } from "./store/slices/authSlice";

export default function Login() {
  const dispatch = useDispatch();
  const nav = useNavigate();
  const { user } = useSelector((state) => state.auth);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState("");
  const [loading, setLoading] = useState(false);
  
  // Refs to handle autofill properly
  const usernameRef = useRef(null);
  const passwordRef = useRef(null);

  // Check auth on mount
  useEffect(() => {
    dispatch(checkAuth());
  }, [dispatch]);

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
  }, [username, password]);

  // Redirect when user is set in Redux
  useEffect(() => {
    if (user && loading) {
      console.log("User loaded in Redux, redirecting...");
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
      
      // Dispatch Redux login action
      await dispatch(loginAction({ username: usernameValue, password: passwordValue })).unwrap();
      
      console.log("Login successful");
      // Navigation will happen in the useEffect when user state is updated
      
    } catch (e2) {
      console.error("Login error:", e2);
      setErr("Login failed: " + (e2 || "Please check your credentials."));
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
