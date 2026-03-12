import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { apiFetch, authHeaders } from "../api";

const DEPARTMENTS = ["Informatics", "Engineering", "Medicine"];
const ISSUE_TYPES = ["Technical", "Access", "Billing", "Account", "Other"];
const PRIORITIES = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "urgent", label: "Urgent" },
];

export default function CreateTicketPage() {
  const navigate = useNavigate();
  const [department, setDepartment] = useState("");
  const [typeOfIssue, setTypeOfIssue] = useState("");
  const [additionalDetails, setAdditionalDetails] = useState("");
  const [priority, setPriority] = useState("medium");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!department || !typeOfIssue.trim() || !additionalDetails.trim()) {
      setError("Please fill in department, type of issue, and additional details.");
      return;
    }
    setSubmitting(true);
    try {
      await apiFetch("/tickets/", {
        method: "POST",
        headers: authHeaders(),
        body: JSON.stringify({
          department,
          type_of_issue: typeOfIssue.trim(),
          additional_details: additionalDetails.trim(),
          priority: priority || "medium",
        }),
      });
      navigate("/dashboard", { replace: true });
    } catch (err) {
      const message = err?.message || "Failed to create ticket. Please try again.";
      setError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="container py-4">
      <div className="row justify-content-center">
        <div className="col-12 col-md-10 col-lg-8">
          <div className="card shadow-sm border-0">
            <div className="card-header bg-white py-3">
              <h1 className="h5 mb-0">Create a ticket</h1>
              <p className="text-muted small mb-0 mt-1">Submit a support request and we’ll get back to you.</p>
            </div>
            <div className="card-body p-4">
              {error && (
                <div className="alert alert-danger" role="alert">
                  {error}
                </div>
              )}
              <form onSubmit={handleSubmit}>
                <div className="mb-3">
                  <label htmlFor="department" className="form-label">Department</label>
                  <select
                    id="department"
                    className="form-select"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    required
                  >
                    <option value="">Select department</option>
                    {DEPARTMENTS.map((d) => (
                      <option key={d} value={d}>{d}</option>
                    ))}
                  </select>
                </div>
                <div className="mb-3">
                  <label htmlFor="typeOfIssue" className="form-label">Type of issue</label>
                  <select
                    id="typeOfIssue"
                    className="form-select"
                    value={typeOfIssue}
                    onChange={(e) => setTypeOfIssue(e.target.value)}
                    required
                  >
                    <option value="">Select type</option>
                    {ISSUE_TYPES.map((t) => (
                      <option key={t} value={t}>{t}</option>
                    ))}
                  </select>
                </div>
                <div className="mb-3">
                  <label htmlFor="additionalDetails" className="form-label">Additional details</label>
                  <textarea
                    id="additionalDetails"
                    className="form-control"
                    rows={4}
                    value={additionalDetails}
                    onChange={(e) => setAdditionalDetails(e.target.value)}
                    placeholder="Describe your issue in detail..."
                    required
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="priority" className="form-label">Priority</label>
                  <select
                    id="priority"
                    className="form-select"
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                  >
                    {PRIORITIES.map((p) => (
                      <option key={p.value} value={p.value}>{p.label}</option>
                    ))}
                  </select>
                </div>
                <div className="d-flex gap-2">
                  <button type="submit" className="btn btn-primary" disabled={submitting}>
                    {submitting ? "Submitting…" : "Submit ticket"}
                  </button>
                  <button
                    type="button"
                    className="btn btn-outline-secondary"
                    onClick={() => navigate("/dashboard")}
                    disabled={submitting}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
