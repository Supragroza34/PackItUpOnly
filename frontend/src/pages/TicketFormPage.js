import React, { useState, useRef } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { authHeaders } from "../api";
import "./TicketFormPage.css";
import UserNavbar from "../components/UserNavbar";

const ISSUE_TYPES = {
  Informatics: [
    "Software Installation Issues",
    "Network Connectivity Problems",
    "Database Access Request",
    "Programming Assignment Help",
    "System Access Request",
    "Lab Equipment Issues",
    "Course Material Access",
  ],
  Engineering: [
    "Lab Equipment Malfunction",
    "CAD Software Issues",
    "Project Submission Problems",
    "Workshop Access Request",
    "Technical Support Request",
    "Hardware Troubleshooting",
    "Simulation Software Problems",
  ],
  Medicine: [
    "Clinical System Access",
    "Medical Database Query",
    "Patient Record System Issues",
    "Research Data Access",
    "Lab Results System Problems",
    "Medical Software Support",
    "Clinical Training Resources",
  ],
};

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10 MB

function formatFileSize(bytes) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + " " + sizes[i];
}

export default function TicketFormPage() {
  const { user } = useAuth();
  const nav = useNavigate();
  const fileInputRef = useRef(null);

  const [department, setDepartment] = useState("");
  const [typeOfIssue, setTypeOfIssue] = useState("");
  const [additionalDetails, setAdditionalDetails] = useState("");
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [errors, setErrors] = useState({});
  const [submitting, setSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState("");
  const [generalError, setGeneralError] = useState("");

  /* ---------- Handlers ---------- */

  function handleDepartmentChange(e) {
    setDepartment(e.target.value);
    setTypeOfIssue("");
    clearError("department");
  }

  function handleIssueChange(e) {
    setTypeOfIssue(e.target.value);
    clearError("type_of_issue");
  }

  function handleDetailsChange(e) {
    setAdditionalDetails(e.target.value);
    clearError("additional_details");
  }

  function handleFileChange(e) {
    const incoming = Array.from(e.target.files);
    const newFiles = [];
    const fileErrors = [];

    incoming.forEach((file) => {
      if (file.size > MAX_FILE_SIZE) {
        fileErrors.push(`"${file.name}" exceeds the 10 MB limit.`);
        return;
      }
      const isDuplicate = selectedFiles.some(
        (f) => f.name === file.name && f.size === file.size
      );
      if (!isDuplicate) newFiles.push(file);
    });

    if (fileErrors.length) {
      setErrors((prev) => ({ ...prev, attachments: fileErrors.join(" ") }));
    } else {
      clearError("attachments");
    }

    setSelectedFiles((prev) => [...prev, ...newFiles]);
    // Reset file input so the same file can be re-added after removal
    e.target.value = "";
  }

  function removeFile(index) {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== index));
    clearError("attachments");
  }

  function clearError(field) {
    setErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      return next;
    });
  }

  /* ---------- Validation ---------- */

  function validate() {
    const errs = {};
    if (!department) errs.department = "Department is required.";
    if (!typeOfIssue) errs.type_of_issue = "Type of issue is required.";
    if (!additionalDetails.trim())
      errs.additional_details = "Additional details are required.";
    return errs;
  }

  /* ---------- Submit ---------- */

  async function handleSubmit(e) {
    e.preventDefault();
    setGeneralError("");
    setSuccessMessage("");

    const clientErrors = validate();
    if (Object.keys(clientErrors).length) {
      setErrors(clientErrors);
      return;
    }

    setSubmitting(true);

    try {
      const formData = new FormData();
      formData.append("department", department);
      formData.append("type_of_issue", typeOfIssue);
      formData.append("additional_details", additionalDetails);
      selectedFiles.forEach((file) => formData.append("attachments", file));

      const API_BASE = `${window.location.protocol}//${window.location.hostname}:8000/api`;
      const res = await fetch(`${API_BASE}/tickets/`, {
        method: "POST",
        headers: authHeaders(), // JWT token; no Content-Type so browser sets multipart boundary
        body: formData,
      });

      const data = await res.json();

      if (res.ok) {
        const ticketId = data.id ?? data.ticket_id;
        setSuccessMessage(
          ticketId
            ? `Ticket #${ticketId} submitted successfully! Redirecting…`
            : `Ticket submitted successfully! Redirecting…`
        );
        setDepartment("");
        setTypeOfIssue("");
        setAdditionalDetails("");
        setSelectedFiles([]);
        setErrors({});
        setTimeout(() => nav("/dashboard"), 2000);
      } else {
        if (data.errors) {
          setErrors(data.errors);
        } else {
          setGeneralError("Something went wrong. Please try again.");
        }
      }
    } catch {
      setGeneralError(
        "Could not reach the server. Please check your connection and try again."
      );
    } finally {
      setSubmitting(false);
    }
  }

  /* ---------- Render ---------- */

  const issueOptions = ISSUE_TYPES[department] || [];

  return (
    <>
      <UserNavbar />
      <div className="ticket-form-page">
      <div className="ticket-form-card">
        {/* Header */}
        <div className="ticket-form-header">
          <h1>🎫 Submit a Support Ticket</h1>
          <p>
            Describe your issue and our team will get back to you as soon as
            possible.
          </p>
        </div>

        <div className="ticket-form-body">
          {/* Back link */}
          <Link to="/dashboard" className="back-link">
            ← Back to Dashboard
          </Link>

          {/* Logged-in user banner */}
          {user && (
            <div className="user-info-banner">
              Submitting as&nbsp;
              <span>
                {user.first_name
                  ? `${user.first_name} ${user.last_name}`
                  : user.username}
              </span>
              {user.k_number && (
                <>
                  &nbsp;·&nbsp;K-Number:&nbsp;<span>{user.k_number}</span>
                </>
              )}
            </div>
          )}

          {/* Success */}
          {successMessage && (
            <div className="alert alert-success">✅ {successMessage}</div>
          )}

          {/* General error */}
          {generalError && (
            <div className="alert alert-error">⚠️ {generalError}</div>
          )}

          <form onSubmit={handleSubmit} noValidate>
            {/* Department */}
            <div className="form-group">
              <label htmlFor="department">Department</label>
              <select
                id="department"
                value={department}
                onChange={handleDepartmentChange}
                className={errors.department ? "error" : ""}
                disabled={submitting}
              >
                <option value="">— Select a department —</option>
                <option value="Informatics">Informatics</option>
                <option value="Engineering">Engineering</option>
                <option value="Medicine">Medicine</option>
              </select>
              {errors.department && (
                <p className="field-error">{errors.department}</p>
              )}
            </div>

            {/* Type of issue (shown only when department is selected) */}
            {department && (
              <div className="form-group">
                <label htmlFor="type_of_issue">Type of Issue</label>
                <select
                  id="type_of_issue"
                  value={typeOfIssue}
                  onChange={handleIssueChange}
                  className={errors.type_of_issue ? "error" : ""}
                  disabled={submitting}
                >
                  <option value="">— Select type of issue —</option>
                  {issueOptions.map((opt) => (
                    <option key={opt} value={opt}>
                      {opt}
                    </option>
                  ))}
                </select>
                {errors.type_of_issue && (
                  <p className="field-error">{errors.type_of_issue}</p>
                )}
              </div>
            )}

            {/* Additional details */}
            <div className="form-group">
              <label htmlFor="additional_details">Additional Details</label>
              <textarea
                id="additional_details"
                value={additionalDetails}
                onChange={handleDetailsChange}
                placeholder="Please describe your issue in detail…"
                rows={6}
                className={errors.additional_details ? "error" : ""}
                disabled={submitting}
              />
              {errors.additional_details && (
                <p className="field-error">{errors.additional_details}</p>
              )}
            </div>

            {/* File attachments */}
            <div className="form-group">
              <label>Attachments (optional)</label>
              <div
                className="file-upload-area"
                onClick={() => fileInputRef.current?.click()}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept="image/*,.pdf,.doc,.docx,.txt"
                  onChange={handleFileChange}
                  disabled={submitting}
                />
                <label className="file-upload-label">
                  <span className="upload-icon">📎</span>
                  <span>
                    <strong>Click to upload</strong> or drag & drop
                  </span>
                  <span style={{ fontSize: "0.8rem", color: "#90a4ae" }}>
                    Images, PDF, DOC, DOCX, TXT — max 10 MB each
                  </span>
                </label>
              </div>

              {errors.attachments && (
                <p className="field-error">{errors.attachments}</p>
              )}

              {selectedFiles.length > 0 && (
                <div className="file-list">
                  {selectedFiles.map((file, idx) => (
                    <div key={idx} className="file-item">
                      <span className="file-item-name">{file.name}</span>
                      <span className="file-item-size">
                        {formatFileSize(file.size)}
                      </span>
                      <button
                        type="button"
                        className="file-item-remove"
                        onClick={() => removeFile(idx)}
                        aria-label={`Remove ${file.name}`}
                      >
                        ×
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Submit */}
            <button type="submit" className="submit-btn" disabled={submitting}>
              {submitting ? "Submitting…" : "Submit Ticket"}
            </button>
          </form>
        </div>
      </div>
    </div>
    </>
  );
}
