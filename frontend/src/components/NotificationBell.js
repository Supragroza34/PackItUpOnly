import { useEffect, useState, useRef, useCallback } from "react";
import "./NotificationBell.css";
import { apiFetch } from "../api";

function toNotifications(data) {
  return Array.isArray(data) ? data : [];
}

function getUnreadCount(notifications) {
  return notifications.filter((notif) => !notif.is_read).length;
}

function updateReadState(notifications, targetId, isRead) {
  return notifications.map((notif) =>
    notif.id === targetId ? { ...notif, is_read: isRead } : notif
  );
}

function BellLabel({ unreadCount, onToggle }) {
  return (
    <span onClick={onToggle} className="bell-label">
      🔔 {unreadCount > 0 && <span className="notif-count">{unreadCount}</span>} Notifications
    </span>
  );
}

function NotificationDropdown({ notifications, onClickNotification }) {
  if (notifications.length === 0) {
    return <p className="no-notifications">You have no notifications.</p>;
  }

  return notifications.map((notif) => (
    <div
      key={notif.id}
      className={`notification-item ${!notif.is_read ? "unread" : ""}`}
      onClick={() => onClickNotification(notif)}
    >
      {!notif.is_read && <span className="unread-dot"></span>}
      <div>
        <strong className="notification-title">{notif.title}</strong>
        <p className="notification-message">{notif.message}</p>
      </div>
    </div>
  ));
}

function useOutsideClose(ref, onClose) {
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (!ref.current || ref.current.contains(event.target)) return;
      onClose();
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [ref, onClose]);
}

function NotificationBell({ onNotificationClick }) {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);
  const bellRef = useRef(null);
  const hasFetchedRef = useRef(false);

  useEffect(() => {
    if (!open) return;
    if (hasFetchedRef.current) return;

    const token = sessionStorage.getItem("access");
    if (!token) return;

    hasFetchedRef.current = true;
    apiFetch("/notifications/", {}, { auth: true })
      .then((data) => {
        setNotifications(Array.isArray(data) ? data : []);
      })
      .catch((err) => {
        console.error("Failed to fetch notifications:", err);
      });
  }, [open]);

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

  const fetchNotifications = useCallback(() => {
    return apiFetch("/notifications/", {}, { auth: true })
      .then((data) => setNotifications(toNotifications(data)))
      .catch((err) => console.error("Failed to fetch notifications:", err));
  }, []);

  useEffect(() => {
    const token = localStorage.getItem("access");
    if (!token || hasFetchedRef.current) return;
    hasFetchedRef.current = true;
    fetchNotifications();
  }, [fetchNotifications]);

  useEffect(() => {
    const token = localStorage.getItem("access");
    if (!open || !token || hasFetchedRef.current) return;
    hasFetchedRef.current = true;
    fetchNotifications();
  }, [open, fetchNotifications]);

  useOutsideClose(bellRef, () => setOpen(false));

  const toggleDropdown = () => setOpen((prev) => !prev);
  const unreadCount = getUnreadCount(notifications);

  const handleNotificationClick = async (notif) => {
    setOpen(false);
    setNotifications((prev) =>
      updateReadState(prev, notif.id, true)
    );

    try {
      await apiFetch(`/notifications/${notif.id}/read/`, { method: "POST" }, { auth: true });
    } catch (err) {
      console.error("Failed to mark notification as read:", err);
      setNotifications((prev) =>
        updateReadState(prev, notif.id, false)
      );
    }

    if (onNotificationClick) onNotificationClick(notif);
  };

  return (
    <div className="notification-bell" ref={bellRef}>
      <BellLabel unreadCount={unreadCount} onToggle={toggleDropdown} />

      {open && (
        <div className="notification-dropdown">
          <NotificationDropdown
            notifications={notifications}
            onClickNotification={handleNotificationClick}
          />
        </div>
      )}
    </div>
  );
}

export default NotificationBell;