import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { logout as logoutAction } from '../store/slices/authSlice';
import './StaffDashboardPage.css';

function StaffDashboardPage() {
    const dispatch = useDispatch();
    const { user } = useSelector((state) => state.auth);
    const [tickets, setTickets] = useState([]);
    const [filter, setFilter] = useState("open");
    const navigate = useNavigate();
    
    // Hard guard: only staff should ever see this page
    useEffect(() => {
        if (!user) return;
        if (user.role !== 'staff' && user.role !== 'Staff') {
            navigate('/dashboard', { replace: true });
        }
    }, [user, navigate]);

    useEffect(() => {
        fetch('/api/staff-dashboard/?filtering=' + filter, {
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
                if (!data) return;

                console.log('Staff dashboard response:', data);

                const ticketsArray = Array.isArray(data)
                    ? data
                    : Array.isArray(data.tickets)
                        ? data.tickets
                        : Array.isArray(data.results)
                            ? data.results
                            : [];

                setTickets(ticketsArray);
            })
            .catch(err => console.error('Error:', err))
    }, [filter, navigate]);

    const handleLogout = async () => {
        await dispatch(logoutAction());
        navigate('/login');
    };

    return (
        <div className="staff-dashboard">
            <h1>Staff Dashboard</h1>

            <div className="staff-dashboard-header">
                <p className="staff-dashboard-user">
                    Welcome, {user?.first_name || user?.last_name}
                </p>
                <button className="staff-dashboard-logout" onClick={handleLogout}>
                    Logout
                </button>
            </div>

            <div className="staff-dashboard-filter">
                <label>
                    Filter tickets:&nbsp;
                    <select value={filter} onChange={(e) => setFilter(e.target.value)}>
                        <option value="open">Open</option>
                        <option value="overdue">Overdue</option>
                        <option value="closed">Closed</option>
                        <option value="all">All</option>
                    </select>
                </label>
            </div>

            {tickets.length === 0 ? (
                <p className="staff-dashboard-empty">No tickets available.</p>
            ) : (
                <div className="staff-dashboard-tickets">
                    {tickets.map((ticket) => (
                        <Link
                            key={ticket.id}
                            to={`/staff/dashboard/${ticket.id}`}
                            className="staff-dashboard-ticket"
                        >
                            <p>
                                Created by: {ticket.user?.first_name} {ticket.user?.last_name}
                            </p>
                        </Link>
                    ))}
                </div>
            )}
        </div>
    );
}

export default StaffDashboardPage;