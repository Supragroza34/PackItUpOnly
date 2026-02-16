import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import adminApi from '../../services/adminApi';
import { useAuth } from '../../context/AuthContext';
import './AdminDashboard.css';

const AdminDashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            setLoading(true);
            const data = await adminApi.getDashboardStats();
            setStats(data);
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = async () => {
        await logout();
        navigate('/admin/login');
    };

    if (loading) {
        return <div className="admin-loading">Loading dashboard...</div>;
    }

    if (error) {
        return <div className="admin-error">Error: {error}</div>;
    }

    return (
        <div className="admin-dashboard">
            <header className="admin-header">
                <div className="header-content">
                    <h1>Admin Dashboard</h1>
                    <div className="header-actions">
                        <span className="user-info">
                            Welcome, {user?.first_name || user?.username}
                        </span>
                        <button onClick={handleLogout} className="btn-logout">
                            Logout
                        </button>
                    </div>
                </div>
            </header>

            <nav className="admin-nav">
                <button 
                    className="nav-btn active"
                    onClick={() => navigate('/admin/dashboard')}
                >
                    Dashboard
                </button>
                <button 
                    className="nav-btn"
                    onClick={() => navigate('/admin/tickets')}
                >
                    Tickets
                </button>
                <button 
                    className="nav-btn"
                    onClick={() => navigate('/admin/users')}
                >
                    Users
                </button>
            </nav>

            <main className="dashboard-content">
                <section className="stats-section">
                    <h2>Ticket Statistics</h2>
                    <div className="stats-grid">
                        <div className="stat-card total">
                            <h3>Total Tickets</h3>
                            <p className="stat-number">{stats.total_tickets}</p>
                        </div>
                        <div className="stat-card pending">
                            <h3>Pending</h3>
                            <p className="stat-number">{stats.pending_tickets}</p>
                        </div>
                        <div className="stat-card progress">
                            <h3>In Progress</h3>
                            <p className="stat-number">{stats.in_progress_tickets}</p>
                        </div>
                        <div className="stat-card resolved">
                            <h3>Resolved</h3>
                            <p className="stat-number">{stats.resolved_tickets}</p>
                        </div>
                        <div className="stat-card closed">
                            <h3>Closed</h3>
                            <p className="stat-number">{stats.closed_tickets}</p>
                        </div>
                    </div>
                </section>

                <section className="stats-section">
                    <h2>User Statistics</h2>
                    <div className="stats-grid">
                        <div className="stat-card users">
                            <h3>Total Users</h3>
                            <p className="stat-number">{stats.total_users}</p>
                        </div>
                        <div className="stat-card students">
                            <h3>Students</h3>
                            <p className="stat-number">{stats.total_students}</p>
                        </div>
                        <div className="stat-card staff">
                            <h3>Staff</h3>
                            <p className="stat-number">{stats.total_staff}</p>
                        </div>
                        <div className="stat-card admins">
                            <h3>Admins</h3>
                            <p className="stat-number">{stats.total_admins}</p>
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
                                    </tr>
                                </thead>
                                <tbody>
                                    {stats.recent_tickets.map((ticket) => (
                                        <tr key={ticket.id}>
                                            <td>{ticket.id}</td>
                                            <td>{ticket.name} {ticket.surname}</td>
                                            <td>{ticket.k_number}</td>
                                            <td>{ticket.department}</td>
                                            <td>{ticket.type_of_issue}</td>
                                            <td>
                                                <span className={`status-badge ${ticket.status}`}>
                                                    {ticket.status.replace('_', ' ')}
                                                </span>
                                            </td>
                                            <td>
                                                <span className={`priority-badge ${ticket.priority}`}>
                                                    {ticket.priority}
                                                </span>
                                            </td>
                                            <td>{new Date(ticket.created_at).toLocaleDateString()}</td>
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
