import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import '@testing-library/jest-dom';
import Statistics from './Statistics';
import adminApi from '../../services/adminApi';
import authReducer from '../../store/slices/authSlice';
import adminReducer from '../../store/slices/adminSlice';

jest.mock('../../services/adminApi', () => ({
  __esModule: true,
  default: {
    getStatistics: jest.fn(),
    getCurrentUser: jest.fn().mockResolvedValue({ id: 1, username: 'admin' }),
  },
}));


function renderStatistics(preloadedAdmin = {}) {
  const store = configureStore({
    reducer: { auth: authReducer, admin: adminReducer },
    preloadedState: {
      auth: {
        user: { id: 1, username: 'admin', first_name: 'Admin' },
        loading: false,
        error: null,
        isAuthenticated: true,
      },
      admin: {
        stats: null,
        statsLoading: false,
        statsError: null,
        tickets: [],
        ticketsTotal: 0,
        ticketsTotalPages: 0,
        ticketsLoading: false,
        ticketsError: null,
        users: [],
        usersTotal: 0,
        usersTotalPages: 0,
        usersLoading: false,
        usersError: null,
        staffList: [],
        staffListLoading: false,
        staffListError: null,
        statistics: null,
        statisticsLoading: false,
        statisticsError: null,
        ...preloadedAdmin,
      },
    },
  });
  return render(
    <Provider store={store}>
      <BrowserRouter>
        <Statistics />
      </BrowserRouter>
    </Provider>
  );
}

const mockStats = {
  total_tickets: 100,
  department_statistics: [
    {
      department: 'IT',
      total_tickets: 50,
      status_breakdown: { pending: 10, in_progress: 15, resolved: 20, closed: 5 },
      priority_breakdown: { low: 20, medium: 15, high: 10, urgent: 5 },
      avg_resolution_time_hours: 24.5,
      avg_response_time_hours: 2.3,
    },
    {
      department: 'HR',
      total_tickets: 50,
      status_breakdown: { pending: 5, in_progress: 10, resolved: 25, closed: 10 },
      priority_breakdown: { low: 30, medium: 10, high: 5, urgent: 5 },
      avg_resolution_time_hours: 48,
      avg_response_time_hours: 1.5,
    },
  ],
};

describe('Statistics', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem('access', 'token');
    adminApi.getStatistics.mockResolvedValue(mockStats);
  });

  afterEach(() => {
    localStorage.clear();
  });

  test('renders loading state initially', () => {
    renderStatistics({ statisticsLoading: true });
    expect(screen.getByText(/Loading statistics/i)).toBeInTheDocument();
  });

  test('renders error state when fetch fails', async () => {
    adminApi.getStatistics.mockRejectedValue(new Error('Failed to load'));
    renderStatistics();
    await waitFor(() => {
      expect(screen.getByText(/Error: Failed to load/)).toBeInTheDocument();
    });
  });

  test('renders statistics when fetch succeeds', async () => {
    renderStatistics();
    const totalTickets = await screen.findAllByText('Total Tickets', {}, { timeout: 3000 });
    expect(totalTickets.length).toBeGreaterThan(0);
    expect(screen.getByText('100')).toBeInTheDocument();
    expect(screen.getAllByText('IT').length).toBeGreaterThan(0);
  });

  test('renders no data message when fetch returns no department_statistics', async () => {
    adminApi.getStatistics.mockResolvedValueOnce({ total_tickets: 0 });
    renderStatistics();
    expect(await screen.findByText(/No statistics available/, {}, { timeout: 3000 })).toBeInTheDocument();
  });
});
