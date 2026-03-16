import React, { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { useAuth } from '../context/AuthContext';
import { logout as logoutAction } from '../store/slices/authSlice';
import './StaffDashboardPage.css';

function statusClass(status, isOverdue) {
    if (isOverdue) return 'sd-status-badge sd-status-overdue';
    return `sd-status-badge sd-status-${(status || 'pending').replace('_', '-')}`;
}

function getStatusLabel(ticket) {
    if (ticket.is_overdue) return 'Overdue';
    if (ticket.status !== 'closed') return (ticket.status || 'pending').replace('_', ' ');
    if (!ticket.closed_by_role) return 'Closed';
    const label = ticket.closed_by_role.charAt(0).toUpperCase() + ticket.closed_by_role.slice(1);
    return `Closed by ${label}`;
}

function extractArray(data) {
    if (Array.isArray(data)) return data;
    if (Array.isArray(data?.tickets)) return data.tickets;
    if (Array.isArray(data?.results)) return data.results;
    return [];
}

function StaffDashboardPage() {
    const dispatch = useDispatch();
    const reduxUser = useSelector((state) => state.auth.user);
    const { user: contextUser } = useAuth();
    const user = reduxUser ?? contextUser;
    const [tickets, setTickets] = useState([]);
    const [allTickets, setAllTickets] = useState([]);
    const [filter, setFilter] = useState('open');
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

    // Fetch all tickets once for summary card counts
    useEffect(() => {
        fetch('/api/staff-dashboard/?filtering=all', {
            headers: { 'Authorization': `Bearer ${sessionStorage.getItem('access')}` },
        })
            .then((res) => res.json())
            .then((data) => setAllTickets(extractArray(data)))
            .catch(() => {});
    }, []);

    // Fetch filtered tickets
    useEffect(() => {
        const params = new URLSearchParams({ filtering: filter });
        if (nameSearch.trim()) params.set('search', nameSearch.trim());
        fetch('/api/staff-dashboard/?' + params.toString(), {
            headers: { 'Authorization': `Bearer ${sessionStorage.getItem('access')}` },
        })
            .then((res) => {
                if (res.status === 401) {
                    alert('You do not have permission to access this page.');
                    sessionStorage.removeItem('access');
                    navigate('/login');
                    return null;
                }
                return res.json();
            })
            .then((data) => {
                if (!data) return;
                console.log('Staff dashboard response:', data);
                setTickets(extractArray(data));
            })
            .catch((err) => console.error('Error:', err));
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
                    'Authorization': `Bearer ${sessionStorage.getItem('access')}`,
                },
                body: JSON.stringify({ status: 'closed' }),
            });
            if (res.ok) {
                const data = await res.json();
                const update = (t) =>
                    t.id === ticketId
                        ? { ...t, status: 'closed', is_overdue: false, closed_by_role: data.closed_by_role || 'staff' }
                        : t;
                setTickets((prev) => prev.map(update));
                setAllTickets((prev) => prev.map(update));
            }
        } catch (err) {
            console.error('Failed to close ticket:', err);
        }
    }

    const countOpen = allTickets.filter((t) => ['pending', 'in_progress'].includes(t.status)).length;
    const countOverdue = allTickets.filter((t) => t.is_overdue).length;
    const countClosed = allTickets.filter((t) => ['closed', 'resolved'].includes(t.status)).length;

    return (
        <div className="sd-page">
            {/* Top bar */}
            <div className="sd-topbar">
                <h1>👋 Welcome, {user?.first_name} {user?.last_name}</h1>
                <div className="sd-topbar-actions">
                    <button
                        className="sd-meeting-btn"
                        onClick={() => navigate('/staff/dashboard/meeting-requests')}
                    >
                        📅 Meeting Requests
                    </button>
                    <button className="sd-logout-btn" onClick={handleLogout}>Log Out</button>
                </div>
            </div>

            {/* Summary cards */}
            <div className="sd-summary">
                <div className="sd-summary-card">
                    <div className="sd-summary-count">{allTickets.length}</div>
                    <div className="sd-summary-label">Total Assigned</div>
                </div>
                <div className="sd-summary-card">
                    <div className="sd-summary-count">{countOpen}</div>
                    <div className="sd-summary-label">Open</div>
                </div>
                <div className="sd-summary-card sd-summary-card--overdue">
                    <div className="sd-summary-count">{countOverdue}</div>
                    <div className="sd-summary-label">Overdue</div>
                </div>
                <div className="sd-summary-card">
                    <div className="sd-summary-count">{countClosed}</div>
                    <div className="sd-summary-label">Closed</div>
                </div>
            </div>

            {/* Ticket list */}
            <div className="sd-content">
                <div className="sd-content-header">
                    <h2>Assigned Tickets</h2>
                    <div className="sd-controls">
                        <select
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            className="sd-select"
                            aria-label="Filter tickets"
                        >
                            <option value="open">Open</option>
                            <option value="overdue">Overdue</option>
                            <option value="closed">Closed</option>
                            <option value="all">All</option>
                        </select>
                        <input
                            type="text"
                            placeholder="Search by name…"
                            value={nameSearch}
                            onChange={(e) => setNameSearch(e.target.value)}
                            className="sd-search-input"
                        />
                    </div>
                </div>

                {tickets.length === 0 ? (
                    <div className="sd-empty-state">
                        <div className="sd-empty-icon">🎫</div>
                        <p>
                            {filter === 'all'
                                ? 'No tickets assigned to you.'
                                : 'No tickets for this filter. Try "All" or ask an admin to assign you a ticket.'}
                        </p>
                    </div>
                ) : (
                    <div className="sd-ticket-list">
                        {tickets.map((ticket) => (
                            <div key={ticket.id} className="sd-ticket-item">
                                <Link to={`/staff/dashboard/${ticket.id}`} className="sd-ticket-link">
                                    <div className="sd-ticket-info">
                                        <h3>{ticket.type_of_issue}</h3>
                                        <div className="sd-ticket-dept">📁 {ticket.department}</div>
                                        {ticket.additional_details && (
                                            <div className="sd-ticket-details">{ticket.additional_details}</div>
                                        )}
                                        <div className="sd-ticket-submitter">
                                            👤 {ticket.user?.first_name} {ticket.user?.last_name}
                                        </div>
                                    </div>
                                </Link>
                                <div className="sd-ticket-meta">
                                    <span className={statusClass(ticket.status, ticket.is_overdue)}>
                                        {getStatusLabel(ticket)}
                                    </span>
                                    {ticket.priority && (
                                        <span className={`sd-priority-badge sd-priority-${ticket.priority}`}>
                                            {ticket.priority}
                                        </span>
                                    )}
                                    <span className="sd-ticket-date">
                                        {new Date(ticket.created_at).toLocaleDateString('en-GB', {
                                            day: '2-digit',
                                            month: 'short',
                                            year: 'numeric',
                                        })}
                                    </span>
                                    {ticket.status !== 'closed' && (
                                        <button
                                            type="button"
                                            className="sd-close-btn"
                                            onClick={(e) => handleCloseTicket(e, ticket.id)}
                                        >
                                            Close ticket
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
//Staff dashboard updated
export default StaffDashboardPage;