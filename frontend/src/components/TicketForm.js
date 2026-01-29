import React, { useState } from 'react';
import './TicketForm.css';

const TicketForm = () => {
  const [formData, setFormData] = useState({
    name: '',
    surname: '',
    k_number: '',
    k_email: '',
    department: '',
    type_of_issue: '',
    additional_details: ''
  });

  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Department-specific issue types
  const issueTypes = {
    Informatics: [
      'Software Installation Issues',
      'Network Connectivity Problems',
      'Database Access Request',
      'Programming Assignment Help',
      'System Access Request',
      'Lab Equipment Issues',
      'Course Material Access'
    ],
    Engineering: [
      'Lab Equipment Malfunction',
      'CAD Software Issues',
      'Project Submission Problems',
      'Workshop Access Request',
      'Technical Support Request',
      'Hardware Troubleshooting',
      'Simulation Software Problems'
    ],
    Medicine: [
      'Clinical System Access',
      'Medical Database Query',
      'Patient Record System Issues',
      'Research Data Access',
      'Lab Results System Problems',
      'Medical Software Support',
      'Clinical Training Resources'
    ]
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    
    // Auto-format email when K-Number changes
    if (name === 'k_number') {
      const kNumber = value.replace(/[^0-9]/g, '').slice(0, 8); // Remove non-numeric and limit to 8 digits
      setFormData(prev => ({
        ...prev,
        [name]: kNumber,
        k_email: kNumber ? `K${kNumber}@kcl.ac.uk` : ''
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }

    // Clear errors when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }

    // Reset type_of_issue when department changes
    if (name === 'department') {
      setFormData(prev => ({
        ...prev,
        type_of_issue: ''
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    // Validate name (no numbers)
    if (!formData.name.trim()) {
      newErrors.name = 'Name is required';
    } else if (/\d/.test(formData.name)) {
      newErrors.name = 'Name cannot contain numbers';
    }

    // Validate surname (no numbers)
    if (!formData.surname.trim()) {
      newErrors.surname = 'Surname is required';
    } else if (/\d/.test(formData.surname)) {
      newErrors.surname = 'Surname cannot contain numbers';
    }

    // Validate K-Number (no letters, only numbers, max 8 digits)
    if (!formData.k_number.trim()) {
      newErrors.k_number = 'K-Number is required';
    } else if (/[a-zA-Z]/.test(formData.k_number)) {
      newErrors.k_number = 'K-Number cannot contain letters';
    } else if (formData.k_number.length > 8) {
      newErrors.k_number = 'K-Number cannot be more than 8 digits';
    }

    // Validate email format
    if (!formData.k_email.trim()) {
      newErrors.k_email = 'Email is required';
    } else {
      const emailPattern = new RegExp(`^K${formData.k_number}@kcl\\.ac\\.uk$`);
      if (!emailPattern.test(formData.k_email)) {
        newErrors.k_email = 'Email must be in the format: KNumber@kcl.ac.uk';
      }
    }

    // Validate department
    if (!formData.department) {
      newErrors.department = 'Department is required';
    }

    // Validate type of issue
    if (!formData.type_of_issue) {
      newErrors.type_of_issue = 'Type of issue is required';
    }

    // Validate additional details
    if (!formData.additional_details.trim()) {
      newErrors.additional_details = 'Additional details are required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitSuccess(false);

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await fetch('/api/submit-ticket/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (response.ok) {
        setSubmitSuccess(true);
        // Reset form
        setFormData({
          name: '',
          surname: '',
          k_number: '',
          k_email: '',
          department: '',
          type_of_issue: '',
          additional_details: ''
        });
        setErrors({});
        
        // Hide success message after 5 seconds
        setTimeout(() => {
          setSubmitSuccess(false);
        }, 5000);
      } else {
        // Handle validation errors from server
        if (data.errors) {
          setErrors(data.errors);
        }
      }
    } catch (error) {
      setErrors({ general: 'An error occurred while submitting the ticket. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="ticket-form-container">
      <h1 className="form-heading">Ticket Form</h1>
      
      {submitSuccess && (
        <div className="success-message">
          Ticket submitted successfully!
        </div>
      )}

      {errors.general && (
        <div className="error-message">
          {errors.general}
        </div>
      )}

      <form onSubmit={handleSubmit} className="ticket-form">
        <div className="form-group">
          <label htmlFor="name">Name</label>
          <input
            type="text"
            id="name"
            name="name"
            value={formData.name}
            onChange={handleChange}
            className={errors.name ? 'error' : ''}
            placeholder="Enter your name"
          />
          {errors.name && <span className="error-text">{errors.name}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="surname">Surname</label>
          <input
            type="text"
            id="surname"
            name="surname"
            value={formData.surname}
            onChange={handleChange}
            className={errors.surname ? 'error' : ''}
            placeholder="Enter your surname"
          />
          {errors.surname && <span className="error-text">{errors.surname}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="k_number">K-Number</label>
          <input
            type="text"
            id="k_number"
            name="k_number"
            value={formData.k_number}
            onChange={handleChange}
            className={errors.k_number ? 'error' : ''}
            placeholder="Enter your K-Number (e.g., 12345678)"
          />
          {errors.k_number && <span className="error-text">{errors.k_number}</span>}
        </div>

        <div className="form-group">
          <label htmlFor="k_email">Email (K Number Email)</label>
          <input
            type="email"
            id="k_email"
            name="k_email"
            value={formData.k_email}
            onChange={handleChange}
            className={errors.k_email ? 'error' : ''}
            placeholder="KNumber@kcl.ac.uk"
            readOnly
          />
          {errors.k_email && <span className="error-text">{errors.k_email}</span>}
        </div>

        <div className="form-group">
          <h2 className="section-heading">Department</h2>
          <select
            id="department"
            name="department"
            value={formData.department}
            onChange={handleChange}
            className={errors.department ? 'error' : ''}
          >
            <option value="">Select a department</option>
            <option value="Informatics">Informatics</option>
            <option value="Engineering">Engineering</option>
            <option value="Medicine">Medicine</option>
          </select>
          {errors.department && <span className="error-text">{errors.department}</span>}
        </div>

        {formData.department && (
          <div className="form-group">
            <h2 className="section-heading">Type Of Issue</h2>
            <select
              id="type_of_issue"
              name="type_of_issue"
              value={formData.type_of_issue}
              onChange={handleChange}
              className={errors.type_of_issue ? 'error' : ''}
            >
              <option value="">Select type of issue</option>
              {issueTypes[formData.department]?.map((issue, index) => (
                <option key={index} value={issue}>
                  {issue}
                </option>
              ))}
            </select>
            {errors.type_of_issue && <span className="error-text">{errors.type_of_issue}</span>}
          </div>
        )}

        <div className="form-group">
          <label htmlFor="additional_details">Further Additional Details</label>
          <textarea
            id="additional_details"
            name="additional_details"
            value={formData.additional_details}
            onChange={handleChange}
            className={errors.additional_details ? 'error' : ''}
            placeholder="Please provide additional details about your issue..."
            rows="5"
          />
          {errors.additional_details && <span className="error-text">{errors.additional_details}</span>}
        </div>

        <button 
          type="submit" 
          className="submit-button"
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Submitting...' : 'Submit Ticket'}
        </button>
      </form>
    </div>
  );
};

export default TicketForm;

