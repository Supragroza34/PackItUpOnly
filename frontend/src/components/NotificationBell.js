import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import "./NotificationBell.css"; // import CSS

const API_BASE = "http://localhost:8000/api";

function NotificationBell() {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

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

  const unreadCount = notifications.filter((n) => !n.is_read).length;

  const toggleDropdown = () => setOpen((prev) => !prev);

  const handleNotificationClick = (n) => {
    setOpen(false);
    if (n.ticket_id) navigate(`/dashboard/ticket/${n.ticket_id}`);
  };

  return (
    <div className="notification-bell">
      <span onClick={toggleDropdown}>
        🔔 {unreadCount > 0 && <span className="notif-count">{unreadCount}</span>}
      </span>

      {open && (
        <div className="notification-dropdown">
          {notifications.length === 0 ? (
            <p style={{ padding: "10px" }}>You have no notifications.</p>
          ) : (
            notifications.map((n) => (
              <div
                key={n.id}
                className={`notification-item ${!n.is_read ? "unread" : ""}`}
                onClick={() => handleNotificationClick(n)}
              >
                <strong>{n.title}</strong>
                <p style={{ margin: "5px 0" }}>{n.message}</p>
                {n.ticket_id && <span>Click to view ticket</span>}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
}

export default NotificationBell; 


