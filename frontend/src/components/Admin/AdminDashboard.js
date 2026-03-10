import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchDashboardStats, updateTicket } from '../../store/slices/adminSlice';
import { logout } from '../../store/slices/authSlice';
import './AdminDashboard.css';

const AdminDashboard = () => {
    const dispatch = useDispatch();
    const navigate = useNavigate();
    
    const { user } = useSelector((state) => state.auth);
    const { stats, statsLoading: loading, statsError: error } = useSelector((state) => state.admin);

    useEffect(() => {
        dispatch(fetchDashboardStats());
    }, [dispatch]);

    const handleLogout = async () => {
        await dispatch(logout());
        navigate('/login');
    };

    const confirmCloseTwice = (ticketId) => {
        if (!window.confirm('Are you sure you want to close this ticket?')) return false;
        if (!window.confirm('Please confirm again. This will close the ticket. Do you want to proceed?')) return false;
        return true;
    };

    const getStatusLabel = (ticket) => {
        if (ticket.status !== 'closed') return (ticket.status || 'pending').replace('_', ' ');
        if (!ticket.closed_by_role) return 'Closed';
        const label = ticket.closed_by_role.charAt(0).toUpperCase() + ticket.closed_by_role.slice(1);
        return `Closed by ${label}`;
    };

    const handleCloseTicket = async (ticketId) => {
        if (!confirmCloseTwice(ticketId)) return;
        try {
            await dispatch(updateTicket({
                ticketId,
                updates: { status: 'closed' },
            })).unwrap();
            dispatch(fetchDashboardStats());
        } catch (err) {
            alert('Failed to close ticket: ' + err);
        }
    };

    if (loading) {
        return <div className="admin-loading">Loading dashboard...</div>;
    }

    if (error) {
        return <div className="admin-error">Error: {error}</div>;
    }

    if (!stats) {
        return <div className="admin-loading">Loading dashboard...</div>;
    }

    return (
        <div className="admin-dashboard">
            {/* Top bar - matching user dashboard style */}
            <div className="dashboard-topbar">
                <h1>👋 Welcome, {user?.first_name || user?.username || 'Admin'}</h1>
                <div className="dashboard-topbar-actions">
                    <button 
                        className={`nav-tab ${window.location.pathname === '/admin/dashboard' ? 'active' : ''}`}
                        onClick={() => navigate('/admin/dashboard')}
                    >
                        Dashboard
                    </button>
                    <button 
                        className="nav-tab"
                        onClick={() => navigate('/admin/tickets')}
                    >
                        Tickets
                    </button>
                    <button 
                        className="nav-tab"
                        onClick={() => navigate('/admin/users')}
                    >
                        Users
                    </button>
                    <button 
                        className="nav-tab"
                        onClick={() => navigate('/admin/statistics')}
                    >
                        Statistics
                    </button>
                    <button className="logout-btn" onClick={handleLogout}>
                        Log Out
                    </button>
                </div>
            </div>

            {/* Summary cards for ticket statistics */}
            <div className="dashboard-summary">
                <div className="summary-card">
                    <div className="summary-count">{stats.total_tickets}</div>
                    <div className="summary-label">Total Tickets</div>
                </div>
                <div className="summary-card">
                    <div className="summary-count">{stats.pending_tickets}</div>
                    <div className="summary-label">Pending</div>
                </div>
                <div className="summary-card">
                    <div className="summary-count">{stats.in_progress_tickets}</div>
                    <div className="summary-label">In Progress</div>
                </div>
                <div className="summary-card">
                    <div className="summary-count">{stats.resolved_tickets}</div>
                    <div className="summary-label">Resolved</div>
                </div>
                <div className="summary-card">
                    <div className="summary-count">{stats.closed_tickets}</div>
                    <div className="summary-label">Closed</div>
                </div>
            </div>

            <main className="dashboard-content">
                <section className="stats-section">
                    <h2>User Statistics</h2>
                    <div className="stats-grid">
                        <div className="stat-card">
                            <div className="summary-count">{stats.total_users}</div>
                            <div className="summary-label">Total Users</div>
                        </div>
                        <div className="stat-card">
                            <div className="summary-count">{stats.total_students}</div>
                            <div className="summary-label">Students</div>
                        </div>
                        <div className="stat-card">
                            <div className="summary-count">{stats.total_staff}</div>
                            <div className="summary-label">Staff</div>
                        </div>
                    </div>
                </section>

                <section className="recent-tickets-section">
                    <h2>Recent Tickets (Last 7 Days)</h2>
                    <div className="tickets-table-container">
                        {stats.recent_tickets && stats.recent_tickets.length > 0 ? (
                            <table className="tickets-table">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Name</th>
                                        <th>K-Number</th>
                                        <th>Department</th>
                                        <th>Issue Type</th>
                                        <th>Status</th>
                                        <th>Priority</th>
                                        <th>Created</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {stats.recent_tickets.map((ticket) => (
                                        <tr key={ticket.id}>
                                            <td>{ticket.id}</td>
                                            <td>{ticket.user_name}</td>
                                            <td>{ticket.user_k_number}</td>
                                            <td>{ticket.department}</td>
                                            <td>{ticket.type_of_issue}</td>
                                            <td>
                                                <span className={`status-badge ${ticket.status}`}>
                                                    {getStatusLabel(ticket)}
                                                </span>
                                            </td>
                                            <td>
                                                <span className={`priority-badge ${ticket.priority}`}>
                                                    {ticket.priority}
                                                </span>
                                            </td>
                                            <td>{new Date(ticket.created_at).toLocaleDateString()}</td>
                                            <td>
                                                {ticket.status !== 'closed' && (
                                                    <button
                                                        type="button"
                                                        className="btn-action btn-close"
                                                        onClick={() => handleCloseTicket(ticket.id)}
                                                    >
                                                        Close
                                                    </button>
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <p className="no-data">No recent tickets</p>
                        )}
                    </div>
                </section>
            </main>
        </div>
    );
};

export default AdminDashboard;
