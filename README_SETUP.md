# KCL Ticketing System - Setup Instructions

This project consists of a Django backend and a React.js frontend for a ticket submission system.

## Prerequisites

- Python 3.8 or higher
- Node.js 14 or higher
- npm or yarn

## Backend Setup (Django)

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Create and run database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

3. **Create a superuser (optional, for admin access):**
   ```bash
   python manage.py createsuperuser
   ```

4. **Run the Django development server:**
   ```bash
   python manage.py runserver
   ```
   The backend will be available at `http://localhost:8000`

## Frontend Setup (React)

1. **Navigate to the frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

3. **Start the React development server:**
   ```bash
   npm start
   ```
   The frontend will be available at `http://localhost:3000`

## Features

- **Form Fields:**
  - Name (validated: no numbers allowed)
  - Surname (validated: no numbers allowed)
  - K-Number (validated: numbers only, auto-generates email)
  - Email (auto-generated from K-Number in format: KNumber@kcl.ac.uk)
  - Department dropdown (Informatics, Engineering, Medicine)
  - Type of Issue dropdown (appears after department selection, department-specific)
  - Additional Details text area

- **Validation:**
  - Email must match K-Number format (KNumber@kcl.ac.uk)
  - K-Number cannot contain letters
  - Name and Surname cannot contain numbers
  - All fields are required

- **Database Integration:**
  - All submitted tickets are saved to the database
  - Tickets can be viewed in Django admin panel

## API Endpoint

- **Submit Ticket:** `POST /api/submit-ticket/`
  - Request body: JSON with form fields
  - Returns: Success message or validation errors

## Accessing Admin Panel

Visit `http://localhost:8000/admin/` to view and manage tickets in the Django admin interface.

