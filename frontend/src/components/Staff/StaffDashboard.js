import React from 'react';
import {useState, useEffect} from 'react';
import {Link, useNavigate} from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';

const StaffDashboard = () => {
    const [tickets, setTickets] = useState([]);
    const { user, logout } = useAuth();
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

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div>
            <h1>Staff Dashboard</h1>
            <div>
                <p>
                    Welcome, {user?.first_name || user?.last_name}
                </p>
                <button onClick={handleLogout}>
                    Logout
                </button>
            </div>
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
            <Link key={ticket.id} to={`/staff/dashboard/${ticket.id}`}>
                <p> Ticket {ticket.id} posted by {ticket.user?.first_name} {ticket.user?.last_name}</p>
            </Link>
            ))
            )}
        </div>
    );
}

export default StaffDashboard;