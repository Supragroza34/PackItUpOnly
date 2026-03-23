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
import AdminTopbar from "./AdminTopbar";

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
    const [replyBody, setReplyBody] = useState('');
    
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
            closeModal();
        } catch (err) {
            alert('Failed to update ticket: ' + err);
        }
    };

    const closeModal = () => {
        setShowModal(false);
        setReplyBody('');
    };

    const handleSubmitReply = async (e) => {
        e.preventDefault();
        if (!replyBody.trim()) return;
        
        try {
            const token = localStorage.getItem('access');
            const response = await fetch('/api/replies/create/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`,
                },
                body: JSON.stringify({
                    ticket: editedTicket.id,
                    body: replyBody.trim(),
                }),
            });
            
            if (!response.ok) {
                throw new Error('Failed to send reply');
            }
            
            setReplyBody('');
            // Refresh ticket details to show the new reply
            await dispatch(fetchTicketDetail(editedTicket.id)).unwrap();
            alert('Reply sent successfully!');
        } catch (err) {
            alert('Failed to send reply: ' + err.message);
        }
    };

    const handleAssignTicket = async (ticketId, assignedToId) => {
        const value = assignedToId === '' ? null : parseInt(assignedToId, 10);
        try {
            await dispatch(updateTicket({
                ticketId,
                updates: { assigned_to: value },
            })).unwrap();
            refreshTickets();
        } catch (err) {
            alert('Failed to assign ticket: ' + err);
        }
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
            refreshTickets();
        } catch (err) {
            alert('Failed to close ticket: ' + err);
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
            <AdminTopbar user={user} handleLogout={handleLogout} />

            <main className="dashboard-content">
                <div className="page-header">
                    <h2>Ticket Management</h2>
                </div>

                <div className="filters-section">
                    <div className="search-by-name-wrap">
                        <label htmlFor="admin-ticket-search" className="search-label">Search by name</label>
                        <input
                            id="admin-ticket-search"
                            type="text"
                            placeholder="Name, K-number, email, department..."
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                            className="search-input"
                        />
                    </div>
                    
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
                        <option value="reported">Reported</option>
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
                                                    {getStatusLabel(ticket)}
                                                </span>
                                            </td>
                                            <td>
                                                <span className={`priority-badge ${ticket.priority}`}>
                                                    {ticket.priority}
                                                </span>
                                            </td>
                                            <td className="assign-cell">
                                                <select
                                                    className="assign-select"
                                                    value={ticket.assigned_to ?? ''}
                                                    onChange={(e) => handleAssignTicket(ticket.id, e.target.value)}
                                                    onClick={(e) => e.stopPropagation()}
                                                    title="Assign to staff"
                                                >
                                                    <option value="">Unassigned</option>
                                                    {staffList.map((staff) => (
                                                        <option key={staff.id} value={staff.id}>
                                                            {staff.first_name} {staff.last_name}
                                                        </option>
                                                    ))}
                                                </select>
                                                {staffList.length === 0 && (
                                                    <span className="assign-hint">No staff in list</span>
                                                )}
                                            </td>
                                            <td>{new Date(ticket.created_at).toLocaleDateString()}</td>
                                            <td className="actions-cell">
                                                <button
                                                    onClick={() => handleViewTicket(ticket.id)}
                                                    className="btn-action btn-view"
                                                >
                                                    View/Edit
                                                </button>
                                                {ticket.status !== 'closed' && (
                                                    <button
                                                        onClick={() => handleCloseTicket(ticket.id)}
                                                        className="btn-action btn-close"
                                                    >
                                                        Close
                                                    </button>
                                                )}
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
                <div className="modal-overlay" onClick={closeModal}>
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
                                <h3>Replies</h3>
                                {editedTicket.replies && editedTicket.replies.length > 0 ? (
                                    <div className="replies-list">
                                        {editedTicket.replies.map((reply) => (
                                            <div key={reply.id} className="reply-item">
                                                <p className="reply-meta">
                                                    <strong>{reply.user_username}</strong>
                                                    {' · '}
                                                    {reply.created_at ? new Date(reply.created_at).toLocaleString() : ''}
                                                </p>
                                                <p className="reply-body">{reply.body}</p>
                                            </div>
                                        ))}
                                    </div>
                                ) : (
                                    <p className="no-replies">No replies yet.</p>
                                )}
                                
                                <div className="reply-form">
                                    <textarea
                                        value={replyBody}
                                        onChange={(e) => setReplyBody(e.target.value)}
                                        placeholder="Write a reply..."
                                        rows={3}
                                    />
                                    <button type="button" onClick={handleSubmitReply} className="btn-send-reply">Send Reply</button>
                                </div>
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
                                        value={editedTicket.assigned_to ?? ''}
                                        onChange={(e) => setEditedTicket({ 
                                            ...editedTicket, 
                                            assigned_to: e.target.value ? parseInt(e.target.value, 10) : null 
                                        })}
                                    >
                                        <option value="">Unassigned</option>
                                        {staffList.map((staff) => (
                                            <option key={staff.id} value={staff.id}>
                                                {staff.first_name} {staff.last_name} ({staff.role})
                                            </option>
                                        ))}
                                    </select>
                                    <small className="form-hint">Assigned staff will see this ticket in their dashboard.</small>
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
                                <button type="button" onClick={closeModal} className="btn-cancel">
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
