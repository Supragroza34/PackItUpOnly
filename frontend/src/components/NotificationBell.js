import { useEffect, useState, useRef } from "react";
import "./NotificationBell.css";

const API_BASE = "http://localhost:8000/api";

function NotificationBell({ onNotificationClick }) {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const bellRef = useRef(null);

  // Fetch notifications
  useEffect(() => {
    const token = localStorage.getItem("access");
    if (!token) return;

    fetch(`${API_BASE}/notifications/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then(setNotifications)
      .catch((err) => console.error("Failed to fetch notifications:", err));
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (bellRef.current && !bellRef.current.contains(event.target)) {
        setOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const toggleDropdown = () => setOpen((prev) => !prev);

  const handleClick = async (notif) => {
    setOpen(false);

    // Optimistically mark as read
    setNotifications((prev) =>
      prev.map((n) => (n.id === notif.id ? { ...n, is_read: true } : n))
    );

    // Persist in backend
    const token = localStorage.getItem("access");
    try {
      await fetch(`${API_BASE}/notifications/${notif.id}/read/`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch (err) {
      console.error("Failed to mark notification as read:", err);
      // Revert if backend fails
      setNotifications((prev) =>
        prev.map((n) => (n.id === notif.id ? { ...n, is_read: false } : n))
      );
    }

    if (onNotificationClick) onNotificationClick(notif);
  };

  return (
    <div className="notification-bell" ref={bellRef}>
      <span onClick={toggleDropdown} className="bell-label">
        🔔 {unreadCount > 0 && <span className="notif-count">{unreadCount}</span>} Notifications
      </span>

      {open && (
        <div className="notification-dropdown">
          {notifications.length === 0 ? (
            <p className="no-notifications">You have no notifications.</p>
          ) : (
            notifications.map((n, idx) => (
              <div
                key={n.id}
                className={`notification-item ${!n.is_read ? "unread" : ""}`}
                onClick={() => handleClick(n)}
              >
                {!n.is_read && <span className="unread-dot"></span>}
                <div>
                  <strong className="notification-title">{n.title}</strong>
                  <p className="notification-message">{n.message}</p>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default NotificationBell;