import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { reassignTicket, fetchStaffList } from '../store/slices/staffSlice';
import { checkAuth } from '../store/slices/authSlice';
import { useAuth } from '../context/AuthContext';
import './TicketPage.css';

const STATUS_OPTIONS = [
    { value: 'new', label: 'New' },
    { value: 'seen', label: 'Seen' },
    { value: 'pending', label: 'Pending' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'awaiting_response', label: 'Awaiting Student Response' },
    { value: 'resolved', label: 'Resolved' },
    { value: 'closed', label: 'Closed' },
    { value: 'reported', label: 'Reported' },
];



function TicketPage() {
    const { ticket_id } = useParams();
    const dispatch = useDispatch();
    const reduxUser = useSelector((state) => state.auth.user);
    const { staffList } = useSelector((state) => state.staff);
    const { user: contextUser } = useAuth();
    const user = reduxUser ?? contextUser;
    const [ticket, setTicket] = useState(null);
    const [body, setBody] = useState("");
    const navigate = useNavigate();

    const authHeaders = () => ({
        'Authorization': `Bearer ${localStorage.getItem('access')}`,
    });

    function changeStatus(newStatus) {
    fetch(`/api/staff/dashboard/${ticket_id}/update/`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', ...authHeaders() },
        body: JSON.stringify({ status: newStatus }),
    })
        .then(res => res.ok ? res.json() : Promise.reject(res))
        .then((data) => {
            setTicket(data);
            if (data['status']==='reported'){
                navigate('/staff/dashboard');
            }
        })
        .catch(err => console.error('Failed to update status:', err));
}

    useEffect(() => {
        dispatch(fetchStaffList());
    }, [dispatch]);

    useEffect(() => {
        if (!user && localStorage.getItem('access')) {
            dispatch(checkAuth());
        }
    }, [dispatch, user]);

    function fetchTicket() {
        fetch(`/api/staff/dashboard/${ticket_id}/`, { headers: authHeaders() })
            .then(res => {
                if (res.status === 401) {
                    localStorage.removeItem('access');
                    navigate('/login');
                    return null;
                }
                return res.json();
            })
            .then(data => data && setTicket(data))
            .catch(err => console.error('Error:', err));
    }

    useEffect(() => {
        fetch(`/api/staff/dashboard/${ticket_id}/`, { headers: authHeaders() })
            .then(res => {
                if (res.status === 401) {
                    localStorage.removeItem('access');
                    navigate('/login');
                    return null;
                }
                return res.json();
            })
            .then(data => data && setTicket(data))
            .catch(err => console.error('Error:', err));
    }, [ticket_id, navigate]);
    
    const redirectQuery = async (ticketId, assignedToId) => {
        const value = assignedToId === '' ? null : parseInt(assignedToId, 10);
        try {
            await dispatch(reassignTicket({
                ticketId,
                updates: { assigned_to: value },
            })).unwrap().then(navigate('/staff/dashboard'));
        } catch (err) {
            alert('Failed to redirect ticket: ' + err);
        }
    };

    function confirmCloseTwice() {
        if (!window.confirm('Are you sure you want to close this ticket?')) return false;
        if (!window.confirm('Please confirm again. This will close the ticket. Do you want to proceed?')) return false;
        return true;
    }

    function handleCloseTicket() {
        if (!confirmCloseTwice()) return;
        fetch(`/api/staff/dashboard/${ticket_id}/update/`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json', ...authHeaders() },
            body: JSON.stringify({ status: 'closed' }),
        })
            .then(res => res.ok ? res.json() : Promise.reject(res))
            .then((data) => {
                setTicket(data);
            })
            .catch(err => console.error('Failed to close ticket:', err));
    }

    function submitReply(e) {
        e.preventDefault();
        if (!body.trim()) return;
        fetch("/api/replies/create/", {
            method: "POST",
            headers: { "Content-Type": "application/json", ...authHeaders() },
            body: JSON.stringify({ ticket: ticket_id, body: body.trim() }),
        })
            .then(res => res.ok ? res.json() : Promise.reject(res))
            .then(() => {
                setBody("");
                fetchTicket();
            })
            .catch(err => console.error('Reply failed:', err));
    }

    if (ticket === null) {
        return <div className="ticket-page"><p className="ticket-page-loading">Loading ticket…</p></div>;
    }

    if (!ticket || !ticket.id) {
        return (
            <div className="ticket-page">
                <p className="ticket-page-loading">Ticket not found or you don’t have access.</p>
                <button className="ticket-page-back" onClick={() => navigate('/staff/dashboard')}>Back to dashboard</button>
            </div>
        );
    }

    const statusClass = (ticket.status || 'pending').replace('_', '-');
    const getStatusLabel = () => {
        if (ticket.status !== 'closed') return (ticket.status || 'pending').replace('_', ' ');
        if (!ticket.closed_by_role) return 'Closed';
        const label = ticket.closed_by_role.charAt(0).toUpperCase() + ticket.closed_by_role.slice(1);
        return `Closed by ${label}`;
    };

    return (
        <div className="ticket-page">
            <div className="ticket-page-header">
                <h1 className="ticket-page-title">Ticket #{ticket.id}</h1>
                <button type="button" className="ticket-page-back" onClick={() => navigate('/staff/dashboard')}>
                    ← Back to dashboard
                </button>
            </div>

            <div className="ticket-meta">
                <span><strong>Type:</strong> {ticket.type_of_issue}</span>
                <span>
                    <strong>Status:</strong>{' '}
                    <select 
                        value={ticket.status || 'pending'} 
                        onChange={(e) => changeStatus(e.target.value)}
                        className="status-dropdown"
                        disabled={ticket.status === 'closed'}
                    >
                        {STATUS_OPTIONS.map(option => (
                            <option key={option.value} value={option.value}>
                                {option.label}
                            </option>
                        ))}
                    </select>
                    {ticket.is_overdue && <span className="overdue-badge">⚠️ Overdue</span>}
                </span>
                <span><strong>Priority:</strong> {(ticket.priority || 'medium')}</span>
                <span><strong>Created:</strong> {ticket.created_at ? new Date(ticket.created_at).toLocaleString() : '—'}</span>
                <span><strong>Updated:</strong> {ticket.updated_at ? new Date(ticket.updated_at).toLocaleString() : '—'}</span>
            </div>

            <div className="ticket-card">
                <h2 className="ticket-card-title">Issue description</h2>
                <p className="ticket-description">{ticket.additional_details || 'No description provided.'}</p>
                {ticket.department && <span className="ticket-department">📁 {ticket.department}</span>}
            </div>

            <div className="ticket-card">
                <h2 className="ticket-card-title">Submitted by</h2>
                <p className="ticket-submitter">
                    <strong>{ticket.user?.first_name} {ticket.user?.last_name}</strong>
                </p>
                {ticket.user?.email && (
                    <p className="ticket-submitter">Email: {ticket.user.email}</p>
                )}
            </div>

            {ticket.status !== 'closed' && (
                <div className="ticket-card">
                    <button type="button" className="ticket-page-close-btn" onClick={handleCloseTicket}>
                        Close ticket
                    </button>
                    <button
                        onClick={() => changeStatus('reported')}
                        disabled={ticket.status === 'closed' || ticket.status === 'reported'}
                        className="ticket-page-report-btn"
                    >
                        Report ticket
                    </button>
                </div>
            )}

            <div className="ticket-card">
                <h2 className="ticket-card-title">Replies</h2>
                {ticket.replies?.length ? (
                    <div className="ticket-replies-list">
                        {ticket.replies.map(reply => (
                            <div key={reply.id} className="ticket-reply">
                                <p className="ticket-reply-meta">
                                    <strong>{reply.user_username}</strong> · {reply.created_at ? new Date(reply.created_at).toLocaleString() : ''}
                                </p>
                                <p className="ticket-reply-body">{reply.body}</p>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="ticket-replies-empty">No replies yet.</p>
                )}
                <form className="ticket-reply-form" onSubmit={submitReply}>
                    <textarea
                        value={body}
                        onChange={e => setBody(e.target.value)}
                        placeholder="Write a reply..."
                        required
                    />
                    <button type="submit">Send reply</button>
                </form>
            </div>

            <div className="ticket-card">
                <h2 className="ticket-card-title">Escalate ticket?</h2>
                <td className="assign-cell">
                    <select
                        className="assign-select"
                        value={ticket.assigned_to ?? ''}
                        onChange={(e) => redirectQuery(ticket.id, e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <option value="">Unassigned</option>
                        {staffList.map((staff) => (
                            <option key={staff.id} value={staff.id}>
                                {staff.first_name} {staff.last_name} : {staff.ticket_count} tickets
                            </option>
                        ))}
                    </select>
                    {staffList.length === 0 && (
                        <span className="assign-hint">No staff in list</span>
                    )}
                </td>
            </div>
        </div>
    );
}

export default TicketPage;