import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import AdminDashboard from './AdminDashboard';
import { renderWithProviders } from '../../utils/testUtils';
import adminApi from '../../services/adminApi';

// Mock the adminApi module
jest.mock('../../services/adminApi', () => ({
  __esModule: true,
  default: {
    getDashboardStats: jest.fn(),
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

describe('AdminDashboard', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock successful API response by default
    adminApi.getDashboardStats.mockResolvedValue({
      total_tickets: 0,
      pending_tickets: 0,
      in_progress_tickets: 0,
      resolved_tickets: 0,
      total_users: 0,
      staff_count: 0,
      student_count: 0,
    });
  });

  test('renders loading state initially', () => {
    renderWithProviders(<AdminDashboard />, {
      admin: { statsLoading: true }
    });
    expect(screen.getByText('Loading dashboard...')).toBeInTheDocument();
  });

  test('renders dashboard stats after loading', async () => {
    const mockStats = {
      total_tickets: 100,
      pending_tickets: 25,
      in_progress_tickets: 30,
      resolved_tickets: 45,
      total_users: 50,
      staff_count: 10,
      student_count: 40,
    };

    // Mock API to return the stats
    adminApi.getDashboardStats.mockResolvedValue(mockStats);

    renderWithProviders(<AdminDashboard />, {
      admin: { stats: mockStats, statsLoading: false }
    });

    await waitFor(() => {
      expect(screen.getByText('Admin Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('Total Tickets')).toBeInTheDocument();
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getByText('Pending')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('30')).toBeInTheDocument();
    expect(screen.getByText('Resolved')).toBeInTheDocument();
    expect(screen.getByText('45')).toBeInTheDocument();
  });

  test('renders error state when API fails', async () => {
    // Mock API to fail
    adminApi.getDashboardStats.mockRejectedValue(new Error('Failed to fetch stats'));

    renderWithProviders(<AdminDashboard />, {
      admin: { statsError: null, statsLoading: false }
    });

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  test('displays user welcome message', async () => {
    renderWithProviders(<AdminDashboard />, {
      admin: {
        stats: {
          total_tickets: 0,
          pending_tickets: 0,
          in_progress_tickets: 0,
          resolved_tickets: 0,
          total_users: 0,
          staff_count: 0,
          student_count: 0,
        },
        statsLoading: false,
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/Welcome, Admin/)).toBeInTheDocument();
    });
  });

  test('renders navigation buttons', async () => {
    renderWithProviders(<AdminDashboard />, {
      admin: {
        stats: {
          total_tickets: 0,
          pending_tickets: 0,
          in_progress_tickets: 0,
          resolved_tickets: 0,
          total_users: 0,
          staff_count: 0,
          student_count: 0,
        },
        statsLoading: false,
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('Tickets')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
  });

  test('renders logout button', async () => {
    renderWithProviders(<AdminDashboard />, {
      admin: {
        stats: {
          total_tickets: 0,
          pending_tickets: 0,
          in_progress_tickets: 0,
          resolved_tickets: 0,
          total_users: 0,
          staff_count: 0,
          student_count: 0,
        },
        statsLoading: false,
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Logout')).toBeInTheDocument();
    });
  });
});
