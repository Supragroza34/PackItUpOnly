import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, authHeaders } from "../api";

function UserDashboardPage() {
  const [user, setUser] = useState(null);
  const [tickets, setTickets] = useState([]);
  const nav = useNavigate();

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        // Call the dashboard API and include JWT token
        const data = await apiFetch("/dashboard/", {
          headers: authHeaders(), // pass token here
        });

        setUser(data.user);
        setTickets(data.tickets);
      } catch (err) {
        console.error("Error loading dashboard:", err);

        // If 401 or 403, redirect to login
        if (err.message.includes("401") || err.message.includes("403")) {
          nav("/login", { replace: true });
        }
      }
    };

    fetchDashboard();
  }, [nav]);

  if (!user) return <p>Loading dashboard...</p>;

  return (
    <div style={{ maxWidth: 800, margin: "20px auto", padding: 20 }}>
      <h1>Welcome {user.k_number}</h1>

      <h2>Your Tickets</h2>

      {tickets.length === 0 ? (
        <p>No tickets yet.</p>
      ) : (
        tickets.map((ticket) => (
          <div
            key={ticket.id}
            style={{
              border: "1px solid #ccc",
              padding: "10px",
              margin: "10px 0",
              borderRadius: 5,
            }}
          >
            <p><strong>Issue:</strong> {ticket.type_of_issue}</p>
            <p><strong>Department:</strong> {ticket.department}</p>
            <p><strong>Details:</strong> {ticket.additional_details}</p>
            <p><strong>Created:</strong> {new Date(ticket.created_at).toLocaleString()}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default UserDashboardPage;