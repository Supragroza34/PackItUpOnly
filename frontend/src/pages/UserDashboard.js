import React, { useEffect, useState } from "react";

function UserDashboardPage() {
  const [user, setUser] = useState(null);
  const [tickets, setTickets] = useState([]);

  useEffect(() => {
    fetch("/api/dashboard/")
      .then(res => res.json())
      .then(data => {
        setUser(data.user);
        setTickets(data.tickets);
      })
      .catch(err => console.error("Error loading dashboard:", err));
  }, []);

  if (!user) return <p>Loading dashboard...</p>;

  return (
    <div>
      <h1>Welcome {user.k_number}</h1>

      <h2>Your Tickets</h2>

      {tickets.length === 0 ? (
        <p>No tickets yet.</p>
      ) : (
        tickets.map(ticket => (
          <div key={ticket.id} style={{border:"1px solid #ccc", padding:"10px", margin:"10px 0"}}>
            <p><strong>Issue:</strong> {ticket.type_of_issue}</p>
            <p><strong>Department:</strong> {ticket.department}</p>
            <p><strong>Details:</strong> {ticket.additional_details}</p>
            <p><strong>Created:</strong> {ticket.created_at}</p>
          </div>
        ))
      )}
    </div>
  );
}

export default UserDashboardPage;
