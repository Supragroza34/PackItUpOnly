import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function TicketPage() {
    const { ticket_id } = useParams();
    const [ticket, setTicket] = useState([]);
    const [body, setBody] = useState("");
    const navigate = useNavigate();
    
    function fetchPost() {
        fetch(`/api/staff/dashboard/${ticket_id}/`)
        .then(res => res.json())
        .then(setTicket);
    }
    
    useEffect(() => {
        fetch(`/api/staff/dashboard/${ticket_id}/`, {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('access')}`
            }
        })
            .then(res => {
                if (res.status === 401) {
                    localStorage.removeItem('access');
                    navigate('/login');
                    return;
                }
                return res.json();
            })
            .then(data => {
                if (data) setTicket(data);
            })
            .catch(err => console.error('Error:', err));
    }, [ticket_id, navigate]);

    function submitReply(e) {
        e.preventDefault();

        fetch("/api/replies/create/", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${localStorage.getItem('access')}`
        },
        body: JSON.stringify({
            ticket: ticket_id,
            body: body
        })
        })
        .then(res => res.json())
        .then(() => {
            setBody("");
            fetchPost(); // refresh replies
        });
    }

    if (!ticket) return <p>Loading...</p>;

    return (
        <div>
            <h1>Ticket Details</h1>
            <p>Type of Issue: {ticket.type_of_issue}</p>
            <p>Status: {ticket.is_overdue ? "Overdue" : ticket.status}</p>
            <p>Created: {ticket.created_at}</p>
            <p>Last Updated: {ticket.updated_at}</p>
            <h2>Submitted By</h2>
            <p>Name: {ticket.user?.first_name} {ticket.user?.last_name}</p>
            <p>Email: {ticket.user?.email}</p>
            <h2>Replies</h2>
            {ticket.replies?.map(reply => (
                <div key={reply?.id}>
                <b>{reply?.user_username}</b>: {reply?.body} - posted at {reply?.created_at}
                </div>
            ))}
            {/* Reply form */}
            <form onSubmit={submitReply}>
                <textarea
                value={body}
                onChange={e => setBody(e.target.value)}
                placeholder="Write a reply..."
                />
                <button type="submit">Reply</button>
            </form>
            <button onClick={() => navigate('/staff/dashboard/')}>Back to dashboard</button>
        </div>
    );
}

export default TicketPage;