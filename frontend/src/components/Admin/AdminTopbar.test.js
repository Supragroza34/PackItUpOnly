import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import AdminTopbar from './AdminTopbar';

const mockNavigate = jest.fn();
const mockUseLocation = jest.fn();

jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
  useLocation: () => mockUseLocation(),
}));

let notificationClickHandler;

jest.mock('../NotificationBell', () => {
  return function MockNotificationBell(props) {
    notificationClickHandler = props.onNotificationClick;
    return (
      <button data-testid="notification-bell" onClick={() => props.onNotificationClick({ ticket: 42 })}>
        Bell
      </button>
    );
  };
});

describe('AdminTopbar', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseLocation.mockReturnValue({ pathname: '/admin/dashboard' });
    notificationClickHandler = undefined;
  });

  test('renders fallback welcome name and logout button', () => {
    render(<AdminTopbar user={null} handleLogout={jest.fn()} />);

    expect(screen.getByText('👋 Welcome, Admin')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
    expect(screen.getByTestId('notification-bell')).toBeInTheDocument();
  });

  test('renders user first_name when available', () => {
    render(
      <AdminTopbar user={{ first_name: 'Teja', username: 'teja1' }} handleLogout={jest.fn()} />
    );

    expect(screen.getByText('👋 Welcome, Teja')).toBeInTheDocument();
  });

  test('marks active nav tab using current route', () => {
    mockUseLocation.mockReturnValue({ pathname: '/admin/statistics' });
    render(<AdminTopbar user={{ username: 'admin' }} handleLogout={jest.fn()} />);

    const statsButton = screen.getByRole('button', { name: 'Statistics' });
    expect(statsButton).toHaveClass('active');
  });

  test('navigates when tab buttons are clicked', () => {
    render(<AdminTopbar user={{ username: 'admin' }} handleLogout={jest.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: 'Dashboard' }));
    fireEvent.click(screen.getByRole('button', { name: 'Tickets' }));
    fireEvent.click(screen.getByRole('button', { name: 'Users' }));
    fireEvent.click(screen.getByRole('button', { name: 'Statistics' }));

    expect(mockNavigate).toHaveBeenCalledWith('/admin/dashboard');
    expect(mockNavigate).toHaveBeenCalledWith('/admin/tickets');
    expect(mockNavigate).toHaveBeenCalledWith('/admin/users');
    expect(mockNavigate).toHaveBeenCalledWith('/admin/statistics');
  });

  test('calls logout handler when Log Out is clicked', () => {
    const handleLogout = jest.fn();
    render(<AdminTopbar user={{ username: 'admin' }} handleLogout={handleLogout} />);

    fireEvent.click(screen.getByRole('button', { name: /log out/i }));
    expect(handleLogout).toHaveBeenCalledTimes(1);
  });

  test('navigates to ticket when notification includes ticket id', () => {
    render(<AdminTopbar user={{ username: 'admin' }} handleLogout={jest.fn()} />);

    expect(notificationClickHandler).toBeDefined();
    notificationClickHandler({ ticket: 91 });

    expect(mockNavigate).toHaveBeenCalledWith('/admin/tickets/91');
  });

  test('does not navigate when notification has no ticket id', () => {
    render(<AdminTopbar user={{ username: 'admin' }} handleLogout={jest.fn()} />);

    expect(notificationClickHandler).toBeDefined();
    notificationClickHandler({});

    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
