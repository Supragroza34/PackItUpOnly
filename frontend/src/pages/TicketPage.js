import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';

function TicketPage() {
    const { id } = useParams();
    const [ticket, setTicket] = useState(null);
    const navigate = useNavigate();
    
    useEffect(() => {
        fetch(`/api/ticket/${id}/`, {
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
    }, [id, navigate]);

    if (!ticket) return <p>Loading...</p>;

    return (
        <div>
            <h1>Ticket Details</h1>
            <p>Type of Issue: {ticket.type_of_issue}</p>
            <p>Status: {ticket.is_overdue ? "Overdue" : ticket.status}</p>
            <p>Created: {ticket.created_at}</p>
            <p>Last Updated: {ticket.updated_at}</p>
            <h2>Submitted By</h2>
            <p>Name: {ticket.k_number.first_name} {ticket.k_number.last_name}</p>
            <p>Email: {ticket.k_number.email}</p>
            <button onClick={() => navigate('/dashboard/staff')}>Reply</button>
        </div>
    );
}

export default TicketPage;