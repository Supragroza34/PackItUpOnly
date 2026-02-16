# Admin Dashboard Documentation

## 🎯 Overview
The Admin Dashboard provides complete control over the KCL Ticketing System, allowing administrators to:
- View system statistics and metrics
- Manage ALL tickets (from both submitters and responders)
- Update ticket status, priority, and assignments
- Manage users and their roles
- Oversee the entire ticketing ecosystem

---

## 🚀 Getting Started

### 1. Create an Admin User
Before accessing the admin dashboard, you need to create an admin user:

```bash
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Create a superuser
python manage.py createsuperuser

# Follow the prompts:
# - Username: (e.g., admin)
# - Email: (your email)
# - Password: (create a strong password)
# - K-number: (e.g., K1234567)
```

Then, manually set the role to admin in Django shell:
```bash
python manage.py shell

# In the Python shell:
from KCLTicketingSystems.models.user import User
user = User.objects.get(username='admin')
user.role = 'admin'
user.save()
exit()
```

### 2. Start the Backend Server
```bash
python manage.py runserver
```
Backend will run on: `http://localhost:8000`

### 3. Start the Frontend Server
```bash
cd frontend
npm start
```
Frontend will run on: `http://localhost:3000`

---

## 🔐 Access the Admin Dashboard

1. Open browser: `http://localhost:3000`
2. Click "Admin Dashboard →" button
3. Login with your admin credentials
4. Navigate between Dashboard, Tickets, and Users sections

---

## 📊 Features

### Dashboard (`/admin/dashboard`)
**Statistics Overview:**
- Total tickets count
- Tickets by status (Pending, In Progress, Resolved, Closed)
- User statistics (Students, Staff, Admins)
- Recent tickets from last 7 days

**Quick Navigation:**
- Jump to Tickets or Users management

### Tickets Management (`/admin/tickets`)
**View & Manage All Tickets:**
- Search by name, K-number, email, department
- Filter by status, priority, department
- Pagination for large datasets

**For Each Ticket:**
- View complete details
- Update status (Pending → In Progress → Resolved → Closed)
- Set priority (Low, Medium, High, Urgent)
- Assign to staff members
- Add internal admin notes
- Delete tickets (with confirmation)

### Users Management (`/admin/users`)
**Manage All Users:**
- Search by name, username, email, K-number
- Filter by role (Student, Staff, Admin)
- View user details

**For Each User:**
- Edit user information (name, email, department)
- Change user roles (promote to staff/admin or demote)
- Delete users (cannot delete yourself)

---

## 🔧 Technical Details

### Backend APIs (Django)
All APIs require admin authentication via Django sessions:

**Authentication:**
- `POST /api/admin/login/` - Admin login
- `POST /api/admin/logout/` - Admin logout
- `GET /api/admin/current-user/` - Get current admin info

**Dashboard:**
- `GET /api/admin/dashboard/stats/` - Get dashboard statistics

**Tickets:**
- `GET /api/admin/tickets/` - List tickets (with filters)
- `GET /api/admin/tickets/{id}/` - Get ticket details
- `PATCH /api/admin/tickets/{id}/update/` - Update ticket
- `DELETE /api/admin/tickets/{id}/delete/` - Delete ticket

**Users:**
- `GET /api/admin/users/` - List users (with filters)
- `GET /api/admin/users/{id}/` - Get user details
- `PATCH /api/admin/users/{id}/update/` - Update user
- `DELETE /api/admin/users/{id}/delete/` - Delete user

**Staff:**
- `GET /api/admin/staff/` - Get staff list for assignments

### Database Schema Changes
New fields added to Ticket model:
- `status` - pending, in_progress, resolved, closed (default: pending)
- `priority` - low, medium, high, urgent (default: medium)
- `assigned_to` - ForeignKey to User (nullable)
- `admin_notes` - TextField for internal notes

### Security
- Session-based authentication
- Admin role verification on every request
- CORS configured for localhost development
- Protected routes in React (redirect to login if not authenticated)

---

## 🤝 Team Integration

### Your teammates can:
1. **Pull your changes:**
   ```bash
   git pull origin main
   ```

2. **Install dependencies:**
   ```bash
   # Backend
   pip install -r requirements.txt
   python manage.py migrate
   
   # Frontend (react-router-dom is in package.json)
   cd frontend
   npm install
   ```

3. **Work on their features:**
   - General ticket submission form
   - User dashboard for ticket submitters
   - Responder/Staff dashboard for handling tickets
   
4. **Use your Ticket model enhancements:**
   - Your tickets now have status, priority, assigned_to fields
   - They can read/update these fields in their features
   - The admin dashboard will automatically manage all tickets

---

## 🎨 Customization Notes

### Styling
- All components use plain CSS (no external libraries)
- Color scheme: Purple gradient (#667eea to #764ba2)
- CSS files are modular per component
- Easy to customize colors, fonts, layouts

### Adding New Features
To add new admin features:

1. **Backend:** Add new view in `admin_views.py`
2. **API:** Add route in `urls.py`
3. **Frontend:** Add method in `adminApi.js`
4. **Component:** Create new component or extend existing ones

---

## 🐛 Troubleshooting

**"Authentication required" error:**
- Make sure you're logged in
- Check that user role is 'admin'
- Clear browser cookies and re-login

**"CORS error":**
- Ensure backend is running on port 8000
- Check CORS settings in `settings.py`

**Can't see admin dashboard:**
- Verify react-router-dom is installed: `npm list react-router-dom`
- Check browser console for errors

**Migrations error:**
- Run: `python manage.py makemigrations`
- Then: `python manage.py migrate`

---

## 📝 Notes for Team

- The admin dashboard is **read-only for other users' work**
- It doesn't interfere with ticket submission forms or user dashboards
- Admin can modify any ticket created by any feature
- All components are in `/frontend/src/components/Admin/`
- All APIs are under `/api/admin/` prefix
- Database changes (new Ticket fields) are backward compatible

---

## ✅ What's Included

**Backend Files:**
- `KCLTicketingSystems/models/ticket.py` - Enhanced Ticket model
- `KCLTicketingSystems/serializers.py` - DRF serializers
- `KCLTicketingSystems/permissions.py` - Admin permission checks
- `KCLTicketingSystems/views/admin_views.py` - All admin API views
- `KCLTicketingSystem/urls.py` - Admin routes added
- Migration file for new Ticket fields

**Frontend Files:**
- `frontend/src/context/AuthContext.js` - Authentication state
- `frontend/src/services/adminApi.js` - API client
- `frontend/src/utils/PrivateRoute.js` - Protected route wrapper
- `frontend/src/components/Admin/AdminLogin.js` - Login page
- `frontend/src/components/Admin/AdminDashboard.js` - Main dashboard
- `frontend/src/components/Admin/TicketsManagement.js` - Ticket management
- `frontend/src/components/Admin/UsersManagement.js` - User management
- All corresponding CSS files
- `frontend/src/App.js` - Routing setup
- `frontend/package.json` - react-router-dom dependency added

---

## 🚀 Ready to Use!

Your admin dashboard is fully functional and ready for your team to integrate with their work!
