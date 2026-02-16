import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import adminApi from '../../services/adminApi';
import { useAuth } from '../../context/AuthContext';
import './TicketsManagement.css';

const TicketsManagement = () => {
    const [tickets, setTickets] = useState([]);
    const [staffList, setStaffList] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedTicket, setSelectedTicket] = useState(null);
    const [showModal, setShowModal] = useState(false);
    const [pagination, setPagination] = useState({ page: 1, total: 0, page_size: 20 });
    
    // Filters
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [priorityFilter, setPriorityFilter] = useState('');
    
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    useEffect(() => {
        fetchTickets();
        fetchStaffList();
    }, [pagination.page, searchTerm, statusFilter, priorityFilter]);

    const fetchTickets = async () => {
        try {
            setLoading(true);
            const data = await adminApi.getTickets({
                page: pagination.page,
                page_size: pagination.page_size,
                search: searchTerm,
                status: statusFilter,
                priority: priorityFilter,
            });
            setTickets(data.tickets);
            setPagination(prev => ({ ...prev, total: data.total, total_pages: data.total_pages }));
            setError(null);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    const fetchStaffList = async () => {
        try {
            const data = await adminApi.getStaffList();
            setStaffList(data.staff);
        } catch (err) {
            console.error('Failed to fetch staff list:', err);
        }
    };

    const handleViewTicket = async (ticketId) => {
        try {
            const ticketData = await adminApi.getTicketDetail(ticketId);
            setSelectedTicket(ticketData);
            setShowModal(true);
        } catch (err) {
            alert('Failed to load ticket details: ' + err.message);
        }
    };

    const handleUpdateTicket = async (e) => {
        e.preventDefault();
        try {
            await adminApi.updateTicket(selectedTicket.id, {
                status: selectedTicket.status,
                priority: selectedTicket.priority,
                assigned_to: selectedTicket.assigned_to,
                admin_notes: selectedTicket.admin_notes,
            });
            alert('Ticket updated successfully!');
            setShowModal(false);
            fetchTickets();
        } catch (err) {
            alert('Failed to update ticket: ' + err.message);
        }
    };

    const handleDeleteTicket = async (ticketId) => {
        if (!window.confirm('Are you sure you want to delete this ticket?')) return;
        
        try {
            await adminApi.deleteTicket(ticketId);
            alert('Ticket deleted successfully!');
            fetchTickets();
        } catch (err) {
            alert('Failed to delete ticket: ' + err.message);
        }
    };

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    return (
        <div className="admin-dashboard">
            <header className="admin-header">
                <div className="header-content">
                    <h1>Admin Dashboard - Tickets</h1>
                    <div className="header-actions">
                        <span className="user-info">Welcome, {user?.first_name || user?.username}</span>
                        <button onClick={handleLogout} className="btn-logout">Logout</button>
                    </div>
                </div>
            </header>

            <nav className="admin-nav">
                <button className="nav-btn" onClick={() => navigate('/admin/dashboard')}>Dashboard</button>
                <button className="nav-btn active" onClick={() => navigate('/admin/tickets')}>Tickets</button>
                <button className="nav-btn" onClick={() => navigate('/admin/users')}>Users</button>
            </nav>

            <main className="dashboard-content">
                <div className="page-header">
                    <h2>Ticket Management</h2>
                </div>

                <div className="filters-section">
                    <input
                        type="text"
                        placeholder="Search by name, K-number, email, department..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="search-input"
                    />
                    
                    <select
                        value={statusFilter}
                        onChange={(e) => setStatusFilter(e.target.value)}
                        className="filter-select"
                    >
                        <option value="">All Statuses</option>
                        <option value="pending">Pending</option>
                        <option value="in_progress">In Progress</option>
                        <option value="resolved">Resolved</option>
                        <option value="closed">Closed</option>
                    </select>
                    
                    <select
                        value={priorityFilter}
                        onChange={(e) => setPriorityFilter(e.target.value)}
                        className="filter-select"
                    >
                        <option value="">All Priorities</option>
                        <option value="low">Low</option>
                        <option value="medium">Medium</option>
                        <option value="high">High</option>
                        <option value="urgent">Urgent</option>
                    </select>
                    
                    <button onClick={fetchTickets} className="btn-refresh">Refresh</button>
                </div>

                {loading ? (
                    <div className="loading">Loading tickets...</div>
                ) : error ? (
                    <div className="error">Error: {error}</div>
                ) : (
                    <>
                        <div className="tickets-table-container">
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
                                        <th>Assigned To</th>
                                        <th>Created</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {tickets.map((ticket) => (
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
                                            <td>{ticket.assigned_to_name || 'Unassigned'}</td>
                                            <td>{new Date(ticket.created_at).toLocaleDateString()}</td>
                                            <td className="actions-cell">
                                                <button
                                                    onClick={() => handleViewTicket(ticket.id)}
                                                    className="btn-action btn-view"
                                                >
                                                    View/Edit
                                                </button>
                                                <button
                                                    onClick={() => handleDeleteTicket(ticket.id)}
                                                    className="btn-action btn-delete"
                                                >
                                                    Delete
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>

                        <div className="pagination">
                            <button
                                onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                                disabled={pagination.page === 1}
                                className="btn-page"
                            >
                                Previous
                            </button>
                            <span className="page-info">
                                Page {pagination.page} of {pagination.total_pages || 1}
                            </span>
                            <button
                                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                                disabled={pagination.page >= pagination.total_pages}
                                className="btn-page"
                            >
                                Next
                            </button>
                        </div>
                    </>
                )}
            </main>

            {showModal && selectedTicket && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <h2>Edit Ticket #{selectedTicket.id}</h2>
                        
                        <form onSubmit={handleUpdateTicket}>
                            <div className="modal-section">
                                <h3>Ticket Information</h3>
                                <p><strong>Name:</strong> {selectedTicket.name} {selectedTicket.surname}</p>
                                <p><strong>K-Number:</strong> {selectedTicket.k_number}</p>
                                <p><strong>Email:</strong> {selectedTicket.k_email}</p>
                                <p><strong>Department:</strong> {selectedTicket.department}</p>
                                <p><strong>Issue Type:</strong> {selectedTicket.type_of_issue}</p>
                                <p><strong>Details:</strong> {selectedTicket.additional_details}</p>
                                <p><strong>Created:</strong> {new Date(selectedTicket.created_at).toLocaleString()}</p>
                            </div>

                            <div className="modal-section">
                                <h3>Admin Controls</h3>
                                
                                <div className="form-group">
                                    <label>Status</label>
                                    <select
                                        value={selectedTicket.status}
                                        onChange={(e) => setSelectedTicket({ ...selectedTicket, status: e.target.value })}
                                    >
                                        <option value="pending">Pending</option>
                                        <option value="in_progress">In Progress</option>
                                        <option value="resolved">Resolved</option>
                                        <option value="closed">Closed</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label>Priority</label>
                                    <select
                                        value={selectedTicket.priority}
                                        onChange={(e) => setSelectedTicket({ ...selectedTicket, priority: e.target.value })}
                                    >
                                        <option value="low">Low</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">High</option>
                                        <option value="urgent">Urgent</option>
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label>Assign To</label>
                                    <select
                                        value={selectedTicket.assigned_to || ''}
                                        onChange={(e) => setSelectedTicket({ 
                                            ...selectedTicket, 
                                            assigned_to: e.target.value ? parseInt(e.target.value) : null 
                                        })}
                                    >
                                        <option value="">Unassigned</option>
                                        {staffList.map((staff) => (
                                            <option key={staff.id} value={staff.id}>
                                                {staff.first_name} {staff.last_name} ({staff.role})
                                            </option>
                                        ))}
                                    </select>
                                </div>

                                <div className="form-group">
                                    <label>Admin Notes</label>
                                    <textarea
                                        value={selectedTicket.admin_notes}
                                        onChange={(e) => setSelectedTicket({ ...selectedTicket, admin_notes: e.target.value })}
                                        rows={4}
                                    />
                                </div>
                            </div>

                            <div className="modal-actions">
                                <button type="submit" className="btn-save">Save Changes</button>
                                <button type="button" onClick={() => setShowModal(false)} className="btn-cancel">
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default TicketsManagement;
