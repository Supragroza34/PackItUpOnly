import React from 'react';
import {useState, useEffect} from 'react';
import {Link, useNavigate} from 'react-router-dom';

function StaffDashboardPage() {
    const [tickets, setTickets] = useState([]);
    const [filter, setFilter] = useState("open");
    const navigate = useNavigate();
    useEffect(() => {
    fetch('/api/staff/dashboard/?filtering=' + filter, {
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('access')}`
        }
    })
        .then(res => {
            if (res.status === 401) {
                alert('You do not have permission to access this page.');
                localStorage.removeItem('access');
                navigate('/login');
                return;
            }
            return res.json();
        })
        .then(data => {
            if (data) setTickets(data);
        })
        .catch(err => console.error('Error:', err))
    }, [filter, navigate]);
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