import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import TicketsManagement from './TicketsManagement';
import { renderWithProviders } from '../../utils/testUtils';
import adminApi from '../../services/adminApi';

// Mock the adminApi module
jest.mock('../../services/adminApi', () => ({
  __esModule: true,
  default: {
    getTickets: jest.fn(),
    getStaffList: jest.fn(),
    updateTicket: jest.fn(),
    deleteTicket: jest.fn(),
    getTicketDetail: jest.fn(),
  },
}));

// Mock console.error to keep tests clean
const originalError = console.error;
beforeAll(() => {
  console.error = jest.fn();
});

afterAll(() => {
  console.error = originalError;
});

describe('TicketsManagement', () => {
  const mockTickets = [
    {
      id: 1,
      user_name: 'John Doe',
      user_k_number: 'K1234567',
      department: 'Computer Science',
      type_of_issue: 'Technical',
      status: 'pending',
      priority: 'high',
      assigned_to_name: null,
      created_at: '2026-02-15T10:00:00Z',
    },
    {
      id: 2,
      user_name: 'Jane Smith',
      user_k_number: 'K7654321',
      department: 'IT',
      type_of_issue: 'Account',
      status: 'in_progress',
      priority: 'medium',
      assigned_to_name: 'Admin User',
      created_at: '2026-02-14T10:00:00Z',
    },
  ];

  const mockStaffList = [
    { id: 1, username: 'staff1', first_name: 'Staff', last_name: 'One', role: 'staff' },
    { id: 2, username: 'staff2', first_name: 'Staff', last_name: 'Two', role: 'staff' },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    window.confirm = jest.fn(() => true);
    // Mock successful API responses by default
    adminApi.getTickets.mockResolvedValue({
      tickets: [],
      total: 0,
      total_pages: 1,
    });
    adminApi.getStaffList.mockResolvedValue([]);
    adminApi.updateTicket.mockResolvedValue({ id: 1, status: 'closed' });
    adminApi.deleteTicket.mockResolvedValue({});
    adminApi.getTicketDetail.mockResolvedValue({ id: 1 });
  });

  test('renders loading state initially', () => {
    renderWithProviders(<TicketsManagement />, {
      admin: { ticketsLoading: true }
    });
    expect(screen.getByText('Loading tickets...')).toBeInTheDocument();
  });

  test('renders ticket list after loading', async () => {
    // Mock API to return tickets
    adminApi.getTickets.mockResolvedValue({
      tickets: mockTickets,
      total: 2,
      total_pages: 1,
    });
    adminApi.getStaffList.mockResolvedValue(mockStaffList);

    renderWithProviders(<TicketsManagement />, {
      admin: { 
        tickets: mockTickets,
        ticketsTotal: 2,
        ticketsTotalPages: 1,
        ticketsLoading: false,
        staffList: mockStaffList
      }
    });

    await waitFor(() => {
      expect(screen.getByText('K1234567')).toBeInTheDocument();
    });

    expect(screen.getByText('Computer Science')).toBeInTheDocument();
    expect(screen.getByText('Technical')).toBeInTheDocument();
  });

  test('displays filter controls', async () => {
    renderWithProviders(<TicketsManagement />, {
      admin: { 
        tickets: [],
        ticketsLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Ticket Management')).toBeInTheDocument();
    });

    expect(screen.getByLabelText(/search by name/i)).toBeInTheDocument();
  });

  test('renders error state when API fails', async () => {
    // Mock API to fail
    adminApi.getTickets.mockRejectedValue(new Error('Failed to fetch tickets'));

    renderWithProviders(<TicketsManagement />, {
      admin: { 
        ticketsError: null,
        ticketsLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  test('displays user welcome message', async () => {
    renderWithProviders(<TicketsManagement />, {
      admin: { 
        tickets: [],
        ticketsLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/Welcome, Admin/)).toBeInTheDocument();
    });
  });

  test('renders navigation buttons', async () => {
    renderWithProviders(<TicketsManagement />, {
      admin: { 
        tickets: [],
        ticketsLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('Tickets')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
  });

  test('applies filters and refreshes ticket query', async () => {
    renderWithProviders(<TicketsManagement />, {
      admin: {
        tickets: [],
        ticketsLoading: false,
        ticketsTotalPages: 1,
      },
    });

    await waitFor(() => {
      expect(adminApi.getTickets).toHaveBeenCalled();
    });

    const callsBefore = adminApi.getTickets.mock.calls.length;

    fireEvent.change(screen.getByLabelText(/search by name/i), {
      target: { value: 'john' },
    });
    fireEvent.change(screen.getByDisplayValue('All Statuses'), {
      target: { value: 'pending' },
    });
    fireEvent.click(screen.getByRole('button', { name: /refresh/i }));

    await waitFor(() => {
      expect(adminApi.getTickets.mock.calls.length).toBeGreaterThan(callsBefore);
    });
  });

  test('closes and deletes a ticket through row actions', async () => {
    adminApi.getTickets.mockResolvedValue({
      tickets: mockTickets,
      total: 2,
      total_pages: 1,
    });

    renderWithProviders(<TicketsManagement />, {
      admin: {
        tickets: mockTickets,
        ticketsTotal: 2,
        ticketsTotalPages: 1,
        ticketsLoading: false,
      },
    });

    await waitFor(() => {
      expect(screen.getByText('K1234567')).toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole('button', { name: 'Close' })[0]);

    await waitFor(() => {
      expect(adminApi.updateTicket).toHaveBeenCalledWith(1, { status: 'closed' });
    });

    fireEvent.click(screen.getAllByRole('button', { name: 'Delete' })[0]);

    await waitFor(() => {
      expect(adminApi.deleteTicket).toHaveBeenCalledWith(1);
    });
  });
});
