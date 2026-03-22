import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { renderWithProviders } from '../../utils/testUtils';
import Statistics from './Statistics';
import adminApi from '../../services/adminApi';

jest.mock('../../services/adminApi', () => ({
  __esModule: true,
  default: {
    getStatistics: jest.fn(),
  },
}));

jest.mock('./AdminTopbar', () => {
  return function MockAdminTopbar() {
    return <div data-testid="admin-topbar">AdminTopbar</div>;
  };
});

describe('Statistics', () => {
  const mockStats = {
    total_tickets: 12,
    department_statistics: [
      {
        department: 'Computer Science',
        total_tickets: 7,
        status_breakdown: {
          pending: 2,
          in_progress: 1,
          resolved: 2,
          closed: 2,
        },
        priority_breakdown: {
          low: 1,
          medium: 2,
          high: 3,
          urgent: 1,
        },
        avg_resolution_time_hours: 30,
        avg_response_time_hours: 2.5,
      },
      {
        department: 'IT',
        total_tickets: 5,
        status_breakdown: {
          pending: 1,
          in_progress: 1,
          resolved: 1,
          closed: 2,
        },
        priority_breakdown: {
          low: 2,
          medium: 1,
          high: 1,
          urgent: 1,
        },
        avg_resolution_time_hours: null,
        avg_response_time_hours: 26,
      },
    ],
  };

  const originalFetch = global.fetch;
  const originalAlert = window.alert;
  const originalCreateObjectURL = window.URL.createObjectURL;
  const originalAnchorClick = HTMLAnchorElement.prototype.click;

  beforeEach(() => {
    jest.clearAllMocks();
    adminApi.getStatistics.mockResolvedValue(mockStats);
    global.fetch = jest.fn();
    window.alert = jest.fn();
    window.URL.createObjectURL = jest.fn(() => 'blob:mock-url');
    HTMLAnchorElement.prototype.click = jest.fn();
    localStorage.setItem('access', 'token-123');
  });

  afterAll(() => {
    global.fetch = originalFetch;
    window.alert = originalAlert;
    window.URL.createObjectURL = originalCreateObjectURL;
    HTMLAnchorElement.prototype.click = originalAnchorClick;
  });

  test('shows loading state', () => {
    renderWithProviders(<Statistics />, {
      admin: {
        statisticsLoading: true,
      },
    });

    expect(screen.getByText('Loading statistics...')).toBeInTheDocument();
  });

  test('shows error state', async () => {
    adminApi.getStatistics.mockRejectedValueOnce(new Error('Boom'));

    renderWithProviders(<Statistics />, {
      admin: {
        statisticsLoading: false,
      },
    });

    await waitFor(() => {
      expect(screen.getByText('Error: Boom')).toBeInTheDocument();
    });
  });

  test('renders no-data state when statistics are missing', async () => {
    adminApi.getStatistics.mockResolvedValueOnce({});

    renderWithProviders(<Statistics />, {
      admin: {
        statisticsLoading: false,
      },
    });

    await waitFor(() => {
      expect(
        screen.getByText('No statistics available for the selected date range.')
      ).toBeInTheDocument();
    });
  });

  test('renders tables and formatted durations from statistics data', async () => {
    renderWithProviders(<Statistics />, {
      admin: {
        statisticsLoading: false,
      },
    });

    await waitFor(() => {
      expect(screen.getAllByText('Total Tickets').length).toBeGreaterThan(0);
    });

    expect(screen.getByText('Ticket Statistics & Analytics')).toBeInTheDocument();
    expect(screen.getByText('12')).toBeInTheDocument();
    expect(screen.getByText('Department Breakdown')).toBeInTheDocument();
    expect(screen.getByText('Priority Distribution by Department')).toBeInTheDocument();
    expect(screen.getAllByText('Computer Science').length).toBeGreaterThan(0);
    expect(screen.getAllByText('IT').length).toBeGreaterThan(0);

    // formatHours branches: >=24, <24, and null
    expect(screen.getByText('1d 6h')).toBeInTheDocument();
    expect(screen.getByText('2.5 hours')).toBeInTheDocument();
    expect(screen.getByText('N/A')).toBeInTheDocument();
    expect(screen.getByText('1d 2h')).toBeInTheDocument();
  });

  test('quick filter buttons trigger statistics refetch', async () => {
    renderWithProviders(<Statistics />, {
      admin: {
        statisticsLoading: false,
      },
    });

    await waitFor(() => {
      expect(adminApi.getStatistics).toHaveBeenCalled();
    });

    const callsBefore = adminApi.getStatistics.mock.calls.length;
    fireEvent.click(screen.getByRole('button', { name: /last 7 days/i }));

    await waitFor(() => {
      expect(adminApi.getStatistics.mock.calls.length).toBeGreaterThan(callsBefore);
    });
  });

  test('export statistics success downloads file', async () => {
    const blob = new Blob(['csv-data'], { type: 'text/csv' });
    global.fetch.mockResolvedValue({
      ok: true,
      blob: jest.fn().mockResolvedValue(blob),
    });

    renderWithProviders(<Statistics />, {
      admin: {
        statisticsLoading: false,
      },
    });

    fireEvent.click(screen.getByRole('button', { name: /export statistics csv/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
      expect(window.URL.createObjectURL).toHaveBeenCalled();
    });
  });

  test('export all tickets failure shows alert', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 500,
      statusText: 'Server Error',
    });

    renderWithProviders(<Statistics />, {
      admin: {
        statisticsLoading: false,
      },
    });

    fireEvent.click(screen.getByRole('button', { name: /export all tickets csv/i }));

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(
        expect.stringMatching(/Failed to export tickets:/)
      );
    });
  });
});
