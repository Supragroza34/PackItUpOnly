import React from 'react';
import './App.css';

import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Login } from "./Login.jsx";
import { Signup } from "./Signup.jsx";
import { Profile } from "./Profile.jsx";

/*
<header className="App-header">
        <h1>KCL Ticketing System</h1>
        <p>Frontend placeholder - build your components here</p>
        <div className="api-info">
          <h2>Backend API Available:</h2>
          <p>POST /api/submit-ticket/</p>
        </div>
      </header>
*/

function isAuthed() {
  return !!localStorage.getItem("access");
}
function Protected({ children }) {
  return isAuthed() ? children : <Navigate to="/login" replace />;
}

/*
function App() {
  return (
    
    <div className="App">
      <BrowserRouter>
        <div style={{ padding: 32 }}>
          <h1>KCL Ticketing System</h1>

          <Routes>
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
              <Route path="*" element={<Navigate to="/login" replace />} />
          </Routes>
        </div>
      </BrowserRouter>

      
    </div>
  );
}
*/

export default function App() {
  return (
    <BrowserRouter>
      <div style={{ padding: 40 }}>
        <h1>ROUTER IS RENDERING</h1>
        <Routes>
          <Route path="*" element={<div>ROUTE MATCHED ✅</div>} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}

export default App;


