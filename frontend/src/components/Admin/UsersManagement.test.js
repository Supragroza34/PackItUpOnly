import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import UsersManagement from './UsersManagement';
import { renderWithProviders } from '../../utils/testUtils';
import adminApi from '../../services/adminApi';

// Mock the adminApi module
jest.mock('../../services/adminApi', () => ({
  __esModule: true,
  default: {
    getUsers: jest.fn(),
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

describe('UsersManagement', () => {
  const mockUsers = [
    {
      id: 1,
      username: 'student1',
      first_name: 'John',
      last_name: 'Doe',
      email: 'john@example.com',
      role: 'student',
      k_number: 'K1234567',
      department: 'Computer Science',
    },
    {
      id: 2,
      username: 'staff1',
      first_name: 'Jane',
      last_name: 'Smith',
      email: 'jane@example.com',
      role: 'staff',
      k_number: 'K7654321',
      department: 'IT Support',
    },
  ];

  beforeEach(() => {
    jest.clearAllMocks();
    // Mock successful API response by default
    adminApi.getUsers.mockResolvedValue({
      users: [],
      total: 0,
      total_pages: 1,
    });
  });

  test('renders loading state initially', () => {
    renderWithProviders(<UsersManagement />, {
      admin: { usersLoading: true }
    });
    expect(screen.getByText('Loading users...')).toBeInTheDocument();
  });

  test('renders user list after loading', async () => {
    // Mock API to return users
    adminApi.getUsers.mockResolvedValue({
      users: mockUsers,
      total: 2,
      total_pages: 1,
    });

    renderWithProviders(<UsersManagement />, {
      admin: { 
        users: mockUsers,
        usersTotal: 2,
        usersTotalPages: 1,
        usersLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText('student1')).toBeInTheDocument();
    });

    expect(screen.getByText('staff1')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByText('jane@example.com')).toBeInTheDocument();
  });

  test('displays filter controls', async () => {
    // Mock API to return users
    adminApi.getUsers.mockResolvedValue({
      users: mockUsers,
      total: 2,
      total_pages: 1,
    });

    renderWithProviders(<UsersManagement />, {
      admin: { 
        users: mockUsers,
        usersLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText('student1')).toBeInTheDocument();
    });

    expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument();
  });

  test('renders error state when API fails', async () => {
    // Mock API to fail
    adminApi.getUsers.mockRejectedValue(new Error('Failed to fetch users'));

    renderWithProviders(<UsersManagement />, {
      admin: { 
        usersError: null,
        usersLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  test('displays user welcome message', async () => {
    renderWithProviders(<UsersManagement />, {
      admin: { 
        users: [],
        usersLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/Welcome, Admin/)).toBeInTheDocument();
    });
  });

  test('renders navigation buttons', async () => {
    renderWithProviders(<UsersManagement />, {
      admin: { 
        users: [],
        usersLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText('Dashboard')).toBeInTheDocument();
    });

    expect(screen.getByText('Tickets')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
  });

  test('displays pagination information', async () => {
    // Mock API to return users
    adminApi.getUsers.mockResolvedValue({
      users: mockUsers,
      total: 2,
      total_pages: 1,
    });

    renderWithProviders(<UsersManagement />, {
      admin: { 
        users: mockUsers,
        usersTotal: 2,
        usersTotalPages: 1,
        usersLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText(/Page 1 of 1/)).toBeInTheDocument();
    });
  });

  test('renders action buttons for each user', async () => {
    // Mock API to return users
    adminApi.getUsers.mockResolvedValue({
      users: mockUsers,
      total: 2,
      total_pages: 1,
    });

    renderWithProviders(<UsersManagement />, {
      admin: { 
        users: mockUsers,
        usersLoading: false 
      }
    });

    await waitFor(() => {
      expect(screen.getByText('student1')).toBeInTheDocument();
    });

    const viewButtons = screen.getAllByText('View/Edit');
    expect(viewButtons.length).toBeGreaterThan(0);
  });
});
