import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';

function TicketPage() {
    const { id } = useParams();
    const [ticket, setTicket] = useState(null);

    useEffect(() => {
        fetch(`/api/ticket/${id}/`)
            .then(res => {
                if (res.status === 401) {
                    window.location.href = '/login';
                }
                return res.json();
            })
            .then(data => setTicket(data))
    }, [id]);

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
        </div>
    );
}

export default TicketPage;