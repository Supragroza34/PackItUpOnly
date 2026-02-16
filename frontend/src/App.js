import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import PrivateRoute from './utils/PrivateRoute';
import AdminLogin from './components/Admin/AdminLogin';
import AdminDashboard from './components/Admin/AdminDashboard';
import TicketsManagement from './components/Admin/TicketsManagement';
import UsersManagement from './components/Admin/UsersManagement';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Default Home Page */}
          <Route path="/" element={
            <div className="App">
              <header className="App-header">
                <h1>KCL Ticketing System</h1>
                <p>Frontend placeholder - build your components here</p>
                <div className="api-info">
                  <h2>Backend API Available:</h2>
                  <p>POST /api/submit-ticket/</p>
                  <Link to="/admin/login" style={{
                    display: 'inline-block',
                    marginTop: '20px',
                    padding: '10px 20px',
                    background: '#667eea',
                    color: 'white',
                    textDecoration: 'none',
                    borderRadius: '5px'
                  }}>
                    Admin Dashboard →
                  </Link>
                </div>
              </header>
            </div>
          } />
          
          {/* Admin Routes */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin/dashboard" element={
            <PrivateRoute>
              <AdminDashboard />
            </PrivateRoute>
          } />
          <Route path="/admin/tickets" element={
            <PrivateRoute>
              <TicketsManagement />
            </PrivateRoute>
          } />
          <Route path="/admin/users" element={
            <PrivateRoute>
              <UsersManagement />
            </PrivateRoute>
          } />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
