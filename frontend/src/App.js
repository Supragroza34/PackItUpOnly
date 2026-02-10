import React from 'react';
import './App.css';
import {BrowserRouter, Routes, Route} from 'react-router-dom';
import StaffDashboardPage from './pages/StaffDashboardPage';
import TicketPage from './pages/TicketPage';

function App() {
  return (
    <BrowserRouter>
    <Routes>
      <Route path="/staff/dashboard" element={<StaffDashboardPage />} />
      <Route path="/ticket/:id" element={<TicketPage />} />
    </Routes>
    </BrowserRouter>
  );
}

export default App;
