import { useEffect, useState } from "react";
import "./NotificationBell.css"; 

function NotificationBell({ onNotificationClick }) {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("access");
    if (!token) return;

    fetch("http://localhost:8000/api/notifications/", {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((res) => res.json())
      .then(setNotifications)
      .catch((err) => console.error("Failed to fetch notifications:", err));
  }, []);

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const toggleDropdown = () => setOpen((prev) => !prev);

  const handleClick = (notif) => {
    setOpen(false);
    if (onNotificationClick) onNotificationClick(notif); 
  };

  return (
    <div className="notification-bell">
      <span onClick={toggleDropdown}>
        🔔 {unreadCount > 0 && <span className="notif-count">{unreadCount}</span>} Notifications
      </span>

      {open && (
        <div className="notification-dropdown">
          {notifications.length === 0 ? (
            <p className="no-notifications">You have no notifications.</p>
          ) : (
            notifications.map((n) => (
              <div
                key={n.id}
                className={`notification-item ${!n.is_read ? "unread" : ""}`}
                onClick={() => handleClick(n)}
              >
                <strong>{n.title}</strong>
                <p>{n.message}</p>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default NotificationBell;