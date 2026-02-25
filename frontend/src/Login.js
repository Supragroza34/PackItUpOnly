import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { login as loginAction, checkAuth } from "./store/slices/authSlice";
import "./Login.css";

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
      console.log("User loaded in context, redirecting...", user);
      // Redirect based strictly on custom role (plus admin flag)
      if (user.role === "admin" || user.is_superuser) {
        console.log("Redirecting to admin dashboard");
        nav("/admin/dashboard", { replace: true });
      } else if (user.role === "staff" || user.role === "Staff") {
        console.log("Redirecting to staff dashboard");
        nav("/staff/dashboard", { replace: true });
      } else {
        console.log("Redirecting to user dashboard");
        nav("/dashboard", { replace: true });
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
      
      // Dispatch Redux login action and get the user data
      const userData = await dispatch(loginAction({ username: usernameValue, password: passwordValue })).unwrap();
      
      console.log("Login successful, user data:", userData);
      
      // Redirect based on user role using the fresh userData
      if (userData.role === "admin" || userData.is_superuser) {
        console.log("Redirecting to admin dashboard");
        nav("/admin/dashboard", { replace: true });
      }
      else if(userData.role === "staff" || userData.role === "Staff"){
        console.log("Redirecting to staff dashboard");
        nav("/staff/dashboard", { replace: true });
      } 
      else {
        console.log("Redirecting to user dashboard");
        nav("/dashboard", { replace: true });
      }
    } catch (e2) {
      console.error("Login error:", e2);
      // Display the error message (already user-friendly from Redux)
      setErr(e2 || "Invalid username or password");
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">KCL Ticketing System</h1>
        <p className="login-subtitle">Sign in to your account</p>

        {err && <p className="login-error" role="alert">{err}</p>}

        <form className="login-form" onSubmit={onSubmit} autoComplete="on">
          <div className="login-field">
            <label htmlFor="login-username">Username</label>
            <input
              id="login-username"
              ref={usernameRef}
              name="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter your username"
              disabled={loading}
              autoComplete="username"
              className="login-input"
              required
            />
          </div>
          <div className="login-field">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              ref={passwordRef}
              name="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              type="password"
              disabled={loading}
              autoComplete="current-password"
              className="login-input"
              required
            />
          </div>
          <button type="submit" disabled={loading} className="login-submit">
            {loading ? "Logging in..." : "Login"}
          </button>
        </form>

        <p className="login-footer">
          Don&apos;t have an account? <a href="/signup">Sign up</a>
        </p>
      </div>
    </div>
  );
}
