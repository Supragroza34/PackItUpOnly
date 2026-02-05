import React, { useEffect, useState } from 'react';
import FaqPage from './pages/FaqPage';
import TicketForm from './components/TicketForm';
import './App.css';

const getCurrentPath = () => {
  const path = window.location.pathname || '/';
  return path.endsWith('/') && path !== '/' ? path.slice(0, -1) : path;
};

const NavItem = ({ label, path, isActive, onNavigate }) => (
  <a
    href={path}
    className={`nav-link ${isActive ? 'active' : ''}`}
    onClick={(event) => onNavigate(event, path)}
  >
    {label}
  </a>
);

function App() {
  const [currentPath, setCurrentPath] = useState(getCurrentPath);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(getCurrentPath());
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const handleNavigate = (event, path) => {
    event.preventDefault();
    if (path === currentPath) {
      return;
    }

    window.history.pushState({}, '', path);
    setCurrentPath(getCurrentPath());
  };

  const pageContent = currentPath === '/faqs' ? (
    <FaqPage onNavigate={handleNavigate} />
  ) : (
    <TicketForm />
  );

  return (
    <div className="App">
      <header className="app-nav">
        <div className="app-nav-inner">
          <NavItem
            label="Create Ticket"
            path="/"
            isActive={currentPath === '/'}
            onNavigate={handleNavigate}
          />
          <NavItem
            label="FAQs"
            path="/faqs"
            isActive={currentPath === '/faqs'}
            onNavigate={handleNavigate}
          />
        </div>
      </header>

      <main className="app-main">{pageContent}</main>
    </div>
  );
}

export default App;
