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
      name: 'John',
      surname: 'Doe',
      k_number: 'K1234567',
      department: 'Computer Science',
      type_of_issue: 'Technical',
      status: 'pending',
      priority: 'high',
      assigned_to_name: null,
      created_at: '2026-02-15T10:00:00Z',
    },
    {
      id: 2,
      name: 'Jane',
      surname: 'Smith',
      k_number: 'K7654321',
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
    // Mock successful API responses by default
    adminApi.getTickets.mockResolvedValue({
      tickets: [],
      total: 0,
      total_pages: 1,
    });
    adminApi.getStaffList.mockResolvedValue([]);
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

    expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
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
});
