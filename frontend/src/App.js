import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Provider } from "react-redux";
import store from "./store";

import PrivateRoute from "./utils/PrivateRoute";

import AdminDashboard from "./components/Admin/AdminDashboard";
import TicketsManagement from "./components/Admin/TicketsManagement";
import UsersManagement from "./components/Admin/UsersManagement";
import StaffDashboardPage from "./pages/StaffDashboardPage";
import TicketPage from "./pages/TicketPage";

import Login from "./Login";
import Signup from "./Signup";
import Profile from "./Profile";
import UserDashboardPage from './pages/UserDashboard';
import './App.css';

import FaqPage from "./pages/FaqPage";

import "./App.css";

function isAuthed() {
  return !!localStorage.getItem("access");
}

function Protected({ children }) {
  return isAuthed() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Provider store={store}>
      <BrowserRouter>
        <Routes>
          {/* User Authentication Routes */}
          <Route path="/" element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route
            path="/profile"
            element={
              <Protected>
                <Profile />
              </Protected>
            }
          />
          
          <Route
          path="/dashboard"
          element={
            <Protected>
            <UserDashboardPage />
            </Protected>
          }
          />
          
          {/* Staff Routes */}

          <Route path="/staff/dashboard/:ticket_id" element={
            <PrivateRoute>
              <TicketPage />
            </PrivateRoute>
          } />  

          <Route path="/staff/dashboard" element={
            <PrivateRoute>
              <StaffDashboardPage />
            </PrivateRoute>
          } />  

          {/* FAQs (added) */}
          <Route
            path="/faqs"
            element={
              <Protected>
                <FaqPage />
              </Protected>
            }
          />

          {/* Admin Routes */}
          <Route
            path="/admin/dashboard"
            element={
              <PrivateRoute>
                <AdminDashboard />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/tickets"
            element={
              <PrivateRoute>
                <TicketsManagement />
              </PrivateRoute>
            }
          />
          <Route
            path="/admin/users"
            element={
              <PrivateRoute>
                <UsersManagement />
              </PrivateRoute>
            }
          />

          {/* Fallback Route */}
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Routes>
      </BrowserRouter>
    </Provider>
  );
}
