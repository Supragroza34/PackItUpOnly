import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { checkAuth } from '../store/slices/authSlice';
import { useAuth } from '../context/AuthContext';
import './TicketPage.css';

function TicketPage() {
    const { ticket_id } = useParams();
    const dispatch = useDispatch();
    const reduxUser = useSelector((state) => state.auth.user);
    const { user: contextUser } = useAuth();
    const user = reduxUser ?? contextUser;
    const [ticket, setTicket] = useState(null);
    const [body, setBody] = useState("");
    const navigate = useNavigate();

    const authHeaders = () => ({
        'Authorization': `Bearer ${localStorage.getItem('access')}`,
    });

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
                    <span className={`status-badge status-${statusClass}`}>
                        {ticket.is_overdue ? 'Overdue' : (ticket.status || 'pending').replace('_', ' ')}
                    </span>
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
        </div>
    );
}

export default TicketPage;