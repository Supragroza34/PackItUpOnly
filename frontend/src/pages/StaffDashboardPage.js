import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { useAuth } from '../context/AuthContext';
import { logout as logoutAction } from '../store/slices/authSlice';
import './StaffDashboardPage.css';

function StaffDashboardPage() {
    const dispatch = useDispatch();
    const reduxUser = useSelector((state) => state.auth.user);
    const { user: contextUser } = useAuth();
    const user = reduxUser ?? contextUser;
    const [tickets, setTickets] = useState([]);
    const [filter, setFilter] = useState("open");
    const [nameSearch, setNameSearch] = useState('');
    const navigate = useNavigate();
    
    // Hard guard: only staff (and admin) should see this page
    useEffect(() => {
        if (!user) return;
        const role = (user.role || '').toLowerCase();
        if (role !== 'staff' && role !== 'admin') {
            navigate('/dashboard', { replace: true });
        }
    }, [user, navigate]);

    useEffect(() => {
        const params = new URLSearchParams({ filtering: filter });
        if (nameSearch.trim()) params.set('search', nameSearch.trim());
        fetch('/api/staff-dashboard/?' + params.toString(), {
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
    }, [filter, nameSearch, navigate]);

    const handleLogout = async () => {
        await dispatch(logoutAction());
        navigate('/login');
    };

    function confirmCloseTwice() {
        if (!window.confirm('Are you sure you want to close this ticket?')) return false;
        if (!window.confirm('Please confirm again. This will close the ticket. Do you want to proceed?')) return false;
        return true;
    }

    async function handleCloseTicket(e, ticketId) {
        e.preventDefault();
        e.stopPropagation();
        if (!confirmCloseTwice()) return;
        try {
            const res = await fetch(`/api/staff/dashboard/${ticketId}/update/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access')}`,
                },
                body: JSON.stringify({ status: 'closed' }),
            });
            if (res.ok) {
                const data = await res.json();
                setTickets(prev => prev.map(t => t.id === ticketId ? { ...t, status: 'closed', closed_by_role: data.closed_by_role || 'staff' } : t));
            }
        } catch (err) {
            console.error('Failed to close ticket:', err);
        }
    }

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
                        <option value="open" >Open</option>
                        <option value="overdue">Overdue</option>
                        <option value="closed">Closed</option>
                        <option value="all">All</option>
                    </select>
                </label>
                <label className="staff-search-by-name">
                    Search by name:&nbsp;
                    <input
                        type="text"
                        placeholder="Submitter name..."
                        value={nameSearch}
                        onChange={(e) => setNameSearch(e.target.value)}
                        className="staff-name-search-input"
                    />
                </label>
            </div>

            {tickets.length === 0 ? (
                <p className="staff-dashboard-empty">
                    {filter === 'all'
                        ? 'No tickets assigned to you.'
                        : 'No tickets assigned to you for this filter. Try "All" or ask an admin to assign you a ticket.'}
                </p>
            ) : (
                <div className="staff-dashboard-tickets">
                    {tickets.map((ticket) => (
                        <div key={ticket.id} className="staff-dashboard-ticket-wrap">
                            <Link
                                to={`/staff/dashboard/${ticket.id}`}
                                className="staff-dashboard-ticket"
                            >
                                <p>
                                    Created by: {ticket.user?.first_name} {ticket.user?.last_name}
                                </p>
                            </Link>
                            {ticket.status !== 'closed' && (
                                <button
                                    type="button"
                                    className="staff-close-ticket-btn"
                                    onClick={(e) => handleCloseTicket(e, ticket.id)}
                                    title="Close ticket"
                                >
                                    Close
                                </button>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}

export default StaffDashboardPage;