import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./UserNavbar.css";

// Handles logout and always redirects, even if the server-side call fails
export async function handleLogout(logout, navigate) {
  try {
    await logout();
  } catch {
    // ignore logout errors — always redirect
  }
  navigate("/login", { replace: true });
}

// The dropdown menu panel with Edit Profile link
function DropdownMenu({ onClose }) {
  return (
    <div className="navbar-dropdown" role="menu">
      <Link to="/profile" className="navbar-dropdown-item" role="menuitem" onClick={onClose}>
        Edit Profile
      </Link>
    </div>
  );
}

// The toggle button that opens/closes the profile dropdown
function ProfileToggle({ open, onToggle }) {
  return (
    <button
      className="navbar-link navbar-plain-btn navbar-profile-toggle"
      onClick={onToggle}
      aria-haspopup="true"
      aria-expanded={open}
    >
      Profile <span className="dropdown-caret">▾</span>
    </button>
  );
}

// Manages dropdown open/close state and renders the toggle + menu
function ProfileDropdown() {
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);
  const toggle = () => setOpen((prev) => !prev);
  return (
    <div
      className="navbar-dropdown-wrapper"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <ProfileToggle open={open} onToggle={toggle} />
      {open && <DropdownMenu onClose={close} />}
    </div>
  );
}

// All navigation links in the right-hand section of the navbar
function NavLinks({ onLogout }) {
  return (
    <div className="navbar-links">
      <Link to="/dashboard" className="navbar-link">Home</Link>
      <Link to="/my-meetings" className="navbar-link">My Meetings</Link>
      <Link to="/faqs" className="navbar-link">View FAQs</Link>
      <Link to="/staff" className="navbar-link">Staff Directory</Link>
      <Link to="/ai-chatbot" className="navbar-link">AI Chatbot</Link>
      <ProfileDropdown />
      <button className="navbar-logout-btn" onClick={onLogout}>Log Out</button>
    </div>
  );
}

// Main navbar component — orchestrates auth hooks and renders the nav bar
export default function UserNavbar() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const onLogout = () => handleLogout(logout, navigate);
  return (
    <nav className="user-navbar">
      <div className="user-navbar-inner">
        <Link to="/dashboard" className="navbar-brand">
          🎓 KCL Ticketing
        </Link>
        <NavLinks onLogout={onLogout} />
      </div>
    </nav>
  );
}
