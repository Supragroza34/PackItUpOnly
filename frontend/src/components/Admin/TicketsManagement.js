import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { 
    fetchTickets, 
    fetchStaffList, 
    fetchTicketDetail, 
    updateTicket,
    deleteTicket as deleteTicketAction 
} from '../../store/slices/adminSlice';
import { logout } from '../../store/slices/authSlice';
import './TicketsManagement.css';

const TicketsManagement = () => {
    const dispatch = useDispatch();
    const navigate = useNavigate();
    
    const { user } = useSelector((state) => state.auth);
    const { 
        tickets, 
        ticketsTotalPages, 
        ticketsLoading: loading, 
        ticketsError: error,
        selectedTicket,
        staffList 
    } = useSelector((state) => state.admin);
    
    const [showModal, setShowModal] = useState(false);
    const [pagination, setPagination] = useState({ page: 1, page_size: 20 });
    const [editedTicket, setEditedTicket] = useState(null);
    
    // Filters
    const [searchTerm, setSearchTerm] = useState('');
    const [statusFilter, setStatusFilter] = useState('');
    const [priorityFilter, setPriorityFilter] = useState('');

    useEffect(() => {
        dispatch(fetchTickets({
            page: pagination.page,
            page_size: pagination.page_size,
            search: searchTerm,
            status: statusFilter,
            priority: priorityFilter,
        }));
    }, [dispatch, pagination.page, pagination.page_size, searchTerm, statusFilter, priorityFilter]);

    useEffect(() => {
        dispatch(fetchStaffList());
    }, [dispatch]);

    const handleViewTicket = async (ticketId) => {
        try {
            await dispatch(fetchTicketDetail(ticketId)).unwrap();
            setEditedTicket(selectedTicket);
            setShowModal(true);
        } catch (err) {
            alert('Failed to load ticket details: ' + err);
        }
    };

    useEffect(() => {
        if (selectedTicket) {
            setEditedTicket(selectedTicket);
        }
    }, [selectedTicket]);

    const handleUpdateTicket = async (e) => {
        e.preventDefault();
        try {
            await dispatch(updateTicket({
                ticketId: editedTicket.id,
                updates: {
                    status: editedTicket.status,
                    priority: editedTicket.priority,
                    assigned_to: editedTicket.assigned_to,
                    admin_notes: editedTicket.admin_notes,
                }
            })).unwrap();
            alert('Ticket updated successfully!');
            setShowModal(false);
        } catch (err) {
            alert('Failed to update ticket: ' + err);
        }
    };

    const handleDeleteTicket = async (ticketId) => {
        if (!window.confirm('Are you sure you want to delete this ticket?')) return;
        
        try {
            await dispatch(deleteTicketAction(ticketId)).unwrap();
            alert('Ticket deleted successfully!');
        } catch (err) {
            alert('Failed to delete ticket: ' + err);
        }
    };

    const handleLogout = async () => {
        await dispatch(logout());
        navigate('/login');
    };

    const refreshTickets = () => {
        dispatch(fetchTickets({
            page: pagination.page,
            page_size: pagination.page_size,
            search: searchTerm,
            status: statusFilter,
            priority: priorityFilter,
        }));
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
                    
                    <button onClick={refreshTickets} className="btn-refresh">Refresh</button>
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
                                            <td>{ticket.user_name}</td>
                                            <td>{ticket.user_k_number}</td>
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
                                Page {pagination.page} of {ticketsTotalPages || 1}
                            </span>
                            <button
                                onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                                disabled={pagination.page >= ticketsTotalPages}
                                className="btn-page"
                            >
                                Next
                            </button>
                        </div>
                    </>
                )}
            </main>

            {showModal && editedTicket && (
                <div className="modal-overlay" onClick={() => setShowModal(false)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <h2>Edit Ticket #{editedTicket.id}</h2>
                        
                        <form onSubmit={handleUpdateTicket}>
                            <div className="modal-section">
                                <h3>Ticket Information</h3>
                                <p><strong>Name:</strong> {editedTicket.user?.first_name} {editedTicket.user?.last_name}</p>
                                <p><strong>K-Number:</strong> {editedTicket.user?.k_number}</p>
                                <p><strong>Email:</strong> {editedTicket.user?.email}</p>
                                <p><strong>Department:</strong> {editedTicket.department}</p>
                                <p><strong>Issue Type:</strong> {editedTicket.type_of_issue}</p>
                                <p><strong>Details:</strong> {editedTicket.additional_details}</p>
                                <p><strong>Created:</strong> {new Date(editedTicket.created_at).toLocaleString()}</p>
                            </div>

                            <div className="modal-section">
                                <h3>Admin Controls</h3>
                                
                                <div className="form-group">
                                    <label>Status</label>
                                    <select
                                        value={editedTicket.status}
                                        onChange={(e) => setEditedTicket({ ...editedTicket, status: e.target.value })}
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
                                        value={editedTicket.priority}
                                        onChange={(e) => setEditedTicket({ ...editedTicket, priority: e.target.value })}
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
                                        value={editedTicket.assigned_to || ''}
                                        onChange={(e) => setEditedTicket({ 
                                            ...editedTicket, 
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
                                        value={editedTicket.admin_notes || ''}
                                        onChange={(e) => setEditedTicket({ ...editedTicket, admin_notes: e.target.value })}
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
