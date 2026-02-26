import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./UserNavbar.css";

export default function UserNavbar() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [profileOpen, setProfileOpen] = useState(false);

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <nav className="user-navbar">
      <div className="user-navbar-inner">
        {/* Brand / Logo */}
        <Link to="/dashboard" className="navbar-brand">
          🎓 KCL Ticketing
        </Link>

        {/* Nav Links */}
        <div className="navbar-links">
          {/* Home */}
          <Link to="/dashboard" className="navbar-link">
            Home
          </Link>

          {/* View FAQs */}
          <Link to="/faqs" className="navbar-link">
            View FAQs
          </Link>

          {/* Staff Office Hours — button only, no page yet */}
          <button
            className="navbar-link navbar-plain-btn navbar-office-btn"
            title="Staff office hours information coming soon"
            disabled
          >
            Staff Office Hours
          </button>

          {/* View Profile dropdown */}
          <div
            className="navbar-dropdown-wrapper"
            onMouseEnter={() => setProfileOpen(true)}
            onMouseLeave={() => setProfileOpen(false)}
          >
            <button
              className="navbar-link navbar-plain-btn navbar-profile-toggle"
              onClick={() => setProfileOpen((prev) => !prev)}
              aria-haspopup="true"
              aria-expanded={profileOpen}
            >
              View Profile <span className="dropdown-caret">▾</span>
            </button>

            {profileOpen && (
              <div className="navbar-dropdown" role="menu">
                <Link
                  to="/profile"
                  className="navbar-dropdown-item"
                  role="menuitem"
                  onClick={() => setProfileOpen(false)}
                >
                  View Profile
                </Link>
                <Link
                  to="/profile"
                  className="navbar-dropdown-item"
                  role="menuitem"
                  onClick={() => setProfileOpen(false)}
                >
                  Edit Profile
                </Link>
              </div>
            )}
          </div>

          {/* Log Out */}
          <button className="navbar-logout-btn" onClick={handleLogout}>
            Log Out
          </button>
        </div>
      </div>
    </nav>
  );
}
