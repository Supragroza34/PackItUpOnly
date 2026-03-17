import React, { useEffect, useState } from 'react';
import { apiFetch } from '../api';
import UserNavbar from '../components/UserNavbar';
import './StaffDirectory.css';

export default function MyMeetingsPage() {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState('');

  useEffect(() => {
    (async () => {
      setLoading(true);
      setErr('');
      try {
        const data = await apiFetch('/meeting-requests/', {}, { auth: true });
        setMeetings(data);
      } catch (e) {
        setErr(String(e.message || e));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const formatDate = (d) => {
    try {
      return new Date(d).toLocaleString();
    } catch {
      return d;
    }
  };

  return (
    <div className="staff-page-wrapper">
      <UserNavbar />

      <div className="staff-page-bg">
        <div className="staff-page">
          <header className="staff-header">
            <h1>My Meetings</h1>
            <p>View and manage meeting requests you have sent to staff.</p>
          </header>

          <div style={{ marginTop: 18 }}>
            {loading ? (
              <p className="staff-status">Loading...</p>
            ) : err ? (
              <p className="staff-status" style={{ color: 'crimson' }}>{err}</p>
            ) : meetings.length === 0 ? (
              <p className="staff-status">You have no meetings scheduled.</p>
            ) : (
              <div className="staff-grid" style={{ gridTemplateColumns: 'repeat(2, 1fr)' }}>
                {meetings.map((m) => {
                  const full = (m.staff_name || '').trim();
                  const parts = full.split(/\s+/);
                  const initials = (parts[0]?.[0] || '') + (parts[1]?.[0] || '');
                  return (
                    <div key={m.id} className="staff-card">
                      <div className="staff-card-avatar">{initials.toUpperCase()}</div>
                      <div className="staff-card-body" style={{ textAlign: 'left' }}>
                        <div className="staff-name">{full || 'Staff'}</div>
                        {m.staff_department ? <div className="staff-dept">{m.staff_department}</div> : null}
                      <div style={{ marginTop: 8 }}><strong>When:</strong> {formatDate(m.meeting_datetime)}</div>
                      <div style={{ marginTop: 6 }}><strong>Status:</strong> {m.status}</div>
                      <div style={{ marginTop: 8 }}><strong>Description</strong>
                        <div style={{ marginTop: 6 }}>{m.description}</div>
                      </div>
                    </div>
                  </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
