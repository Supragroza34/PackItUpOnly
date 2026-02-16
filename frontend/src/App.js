import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";

import Login from "./Login";
import Signup from "./Signup";
import Profile from "./Profile";

// add your pages/components
import FaqPage from "./pages/FaqPage";
import TicketForm from "./components/TicketForm";

function isAuthed() {
  return !!localStorage.getItem("access");
}

function Protected({ children }) {
  return isAuthed() ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* keep existing auth flow */}
        <Route path="/" element={<Navigate to="/login" replace />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />

        {/* existing protected route */}
        <Route
          path="/profile"
          element={
            <Protected>
              <Profile />
            </Protected>
          }
        />

        {/* add your FAQ + ticket pages (make them protected if you want) */}
        <Route
          path="/ticket"
          element={
            <Protected>
              <TicketForm />
            </Protected>
          }
        />
        <Route
          path="/faqs"
          element={
            <Protected>
              <FaqPage />
            </Protected>
          }
        />

        {/* fallback */}
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
