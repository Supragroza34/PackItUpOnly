import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useDispatch, useSelector } from "react-redux";
import { apiFetch, authHeaders } from "../api";
import { checkAuth } from "../store/slices/authSlice";

function UserDashboardPage() {
  const dispatch = useDispatch();
  const { user, loading } = useSelector((state) => state.auth);
  const [tickets, setTickets] = useState([]);
  const nav = useNavigate();

  // Check auth on mount
  useEffect(() => {
    dispatch(checkAuth());
  }, [dispatch]);

  // Fetch tickets when user is loaded
  useEffect(() => {
    if (!user) return;

    const fetchDashboard = async () => {
      try {
        // Call the dashboard API and include JWT token
        const data = await apiFetch("/dashboard/", {
          headers: authHeaders(), // pass token here
        });

        setTickets(data.tickets);
      } catch (err) {
        console.error("Error loading dashboard:", err);

        // If 401 or 403, redirect to login
        if (err.message.includes("401") || err.message.includes("403")) {
          nav("/login", { replace: true });
        }
      }
    };

    fetchDashboard();
  }, [user, nav]);

  if (!user) {
    return (
      <div className="container py-5 text-center">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
        <p className="mt-2 text-muted">Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="container py-4">
      <div className="row justify-content-center">
        <div className="col-12 col-lg-10 col-xl-8">
          <div className="d-flex align-items-center justify-content-between flex-wrap gap-2 mb-4">
            <h1 className="h3 mb-0">Welcome, {user.k_number}</h1>
            <Link to="/create-ticket" className="btn btn-primary">Create ticket</Link>
          </div>

          <div className="card shadow-sm border-0 mb-4">
            <div className="card-header bg-white py-3">
              <h2 className="h5 mb-0">Your Tickets</h2>
            </div>
            <div className="card-body p-0">
              {tickets.length === 0 ? (
                <div className="text-center py-5 text-muted">
                  <p className="mb-0">No tickets yet.</p>
                  <p className="small mt-1">Create a ticket when you need support.</p>
                </div>
              ) : (
                <ul className="list-group list-group-flush">
                  {tickets.map((ticket) => (
                    <li key={ticket.id} className="list-group-item">
                      <div className="d-flex flex-wrap justify-content-between align-items-start gap-2 mb-2">
                        <span className="badge bg-primary rounded-pill">{ticket.type_of_issue}</span>
                        <small className="text-muted">
                          {new Date(ticket.created_at).toLocaleString()}
                        </small>
                      </div>
                      <p className="mb-1 small text-muted">Department: {ticket.department}</p>
                      <p className="mb-0">{ticket.additional_details}</p>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default UserDashboardPage;