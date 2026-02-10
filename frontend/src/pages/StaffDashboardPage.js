import React from 'react';
import {useState, useEffect} from 'react';
import {Link} from 'react-router-dom';

function StaffDashboardPage() {
    const [tickets, setTickets] = useState([]);
    const [filter, setFilter] = useState("open");
    useEffect(() => {
    fetch('/api/staff/dashboard/?filtering=' + filter)
        .then(res => {
            if (res.status === 401) {
                window.location.href = '/login'; //redirects if user is not specified
            }
            return res.json();
        })
        .then(data => setTickets(data))
}, [filter]);
    return (
        <div>
            <h1>Staff Dashboard</h1>
            <select value={filter} onChange={(e) => setFilter(e.target.value)}>
                <option value="open">Open</option>
                <option value="overdue">Overdue</option>
                <option value="closed">Closed</option>
                <option value="all">All</option>
            </select>
            {tickets.length === 0 ? (
            <p>No tickets available.</p>
            ) : (
            tickets.map(ticket => (
            <Link key={ticket.id} to={`/ticket/${ticket.id}`}>
            <p>Type of issue:{ticket.type_of_issue}</p>
            <p>K-Number: {ticket.k_number}</p>
            <p>Created: {ticket.created_at}</p>
            <p>Status: {ticket.is_overdue ? "Overdue" : ticket.status}</p>
            </Link>
            ))
            )}
        </div>
    );
}

export default StaffDashboardPage;