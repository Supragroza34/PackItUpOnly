import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom';
import '@testing-library/jest-dom';
import AdminTopbar from './AdminTopbar';

jest.mock('../NotificationBell', () => ({ onNotificationClick }) => (
  <button
    data-testid="notification-bell"
    onClick={() => onNotificationClick({ ticket: 123 })}
  >
    Bell
  </button>
));

const mockNavigate = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

function renderAdminTopbar(user = {}, initialPath = '/admin/dashboard') {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <AdminTopbar
        user={user}
        handleLogout={jest.fn()}
      />
    </MemoryRouter>
  );
}

describe('AdminTopbar', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders welcome with user first name', () => {
    renderAdminTopbar({ first_name: 'Jane', username: 'jane' });
    expect(screen.getByText(/Welcome, Jane/)).toBeInTheDocument();
  });

  test('renders username when first_name is missing', () => {
    renderAdminTopbar({ username: 'admin' });
    expect(screen.getByText(/Welcome, admin/)).toBeInTheDocument();
  });

  test('renders Admin when user is empty', () => {
    renderAdminTopbar({});
    expect(screen.getByText(/Welcome, Admin/)).toBeInTheDocument();
  });

  test('renders notification bell and logout button', () => {
    renderAdminTopbar({});
    expect(screen.getByTestId('notification-bell')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
  });

  test('calls handleLogout when Log Out clicked', () => {
    const handleLogout = jest.fn();
    render(
      <MemoryRouter>
        <AdminTopbar user={{}} handleLogout={handleLogout} />
      </MemoryRouter>
    );
    fireEvent.click(screen.getByRole('button', { name: /log out/i }));
    expect(handleLogout).toHaveBeenCalledTimes(1);
  });

  test('navigates to /admin/dashboard when Dashboard tab clicked', () => {
    renderAdminTopbar({}, '/admin/tickets');
    fireEvent.click(screen.getByRole('button', { name: /^dashboard$/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/admin/dashboard');
  });

  test('navigates to /admin/tickets when Tickets tab clicked', () => {
    renderAdminTopbar({}, '/admin/dashboard');
    fireEvent.click(screen.getByRole('button', { name: /^tickets$/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/admin/tickets');
  });

  test('navigates to /admin/users when Users tab clicked', () => {
    renderAdminTopbar({}, '/admin/dashboard');
    fireEvent.click(screen.getByRole('button', { name: /^users$/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/admin/users');
  });

  test('navigates to /admin/statistics when Statistics tab clicked', () => {
    renderAdminTopbar({}, '/admin/dashboard');
    fireEvent.click(screen.getByRole('button', { name: /^statistics$/i }));
    expect(mockNavigate).toHaveBeenCalledWith('/admin/statistics');
  });

  test('notification click navigates to ticket when notif has ticket', () => {
    renderAdminTopbar({});
    fireEvent.click(screen.getByTestId('notification-bell'));
    expect(mockNavigate).toHaveBeenCalledWith('/admin/tickets/123');
  });

  test('Dashboard tab has active class on /admin/dashboard', () => {
    renderAdminTopbar({}, '/admin/dashboard');
    const dashboardTab = screen.getByRole('button', { name: /^dashboard$/i });
    expect(dashboardTab).toHaveClass('active');
  });

  test('Tickets tab has active class on /admin/tickets', () => {
    renderAdminTopbar({}, '/admin/tickets');
    const ticketsTab = screen.getByRole('button', { name: /^tickets$/i });
    expect(ticketsTab).toHaveClass('active');
  });
});
