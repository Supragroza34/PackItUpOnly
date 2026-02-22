import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import StaffDashboardPage from './StaffDashboardPage';

// Mock useNavigate
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
}));

// Sample ticket data
const mockTickets = [
    {
        id: 1,
        type_of_issue: 'Login Problem',
        k_number: '12345678',
        created_at: '2026-02-18T10:00:00Z',
        status: 'Open',
        is_overdue: false,
    },
    {
        id: 2,
        type_of_issue: 'Network Issue',
        k_number: '87654321',
        created_at: '2026-02-15T08:00:00Z',
        status: 'Open',
        is_overdue: true,
    },
];

// Helper to render component with router
const renderWithRouter = (component) => {
    return render(<BrowserRouter>{component}</BrowserRouter>);
};

describe('StaffDashboardPage', () => {
    beforeEach(() => {
        jest.clearAllMocks();
        localStorage.clear();
        localStorage.setItem('access', 'test-token-123');
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    test('renders the Staff Dashboard heading', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                status: 200,
                json: () => Promise.resolve([]),
            })
        );

        renderWithRouter(<StaffDashboardPage />);

        expect(screen.getByText('Staff Dashboard')).toBeInTheDocument();
    });

    test('renders filter dropdown with all options', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                status: 200,
                json: () => Promise.resolve([]),
            })
        );

        renderWithRouter(<StaffDashboardPage />);

        const select = screen.getByRole('combobox');
        expect(select).toBeInTheDocument();

        expect(screen.getByText('Open')).toBeInTheDocument();
        expect(screen.getByText('Overdue')).toBeInTheDocument();
        expect(screen.getByText('Closed')).toBeInTheDocument();
        expect(screen.getByText('All')).toBeInTheDocument();
    });

    test('shows "No tickets available" when no tickets', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                status: 200,
                json: () => Promise.resolve([]),
            })
        );

        renderWithRouter(<StaffDashboardPage />);

        await waitFor(() => {
            expect(screen.getByText('No tickets available.')).toBeInTheDocument();
        });
    });

    test('displays tickets when data is returned', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                status: 200,
                json: () => Promise.resolve(mockTickets),
            })
        );

        renderWithRouter(<StaffDashboardPage />);

        await waitFor(() => {
            expect(screen.getByText('Type of issue:Login Problem')).toBeInTheDocument();
            expect(screen.getByText('K-Number: 12345678')).toBeInTheDocument();
        });

        await waitFor(() => {
            expect(screen.getByText('Type of issue:Network Issue')).toBeInTheDocument();
            expect(screen.getByText('K-Number: 87654321')).toBeInTheDocument();
        });
    });

    test('shows "Overdue" status for overdue tickets', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                status: 200,
                json: () => Promise.resolve(mockTickets),
            })
        );

        renderWithRouter(<StaffDashboardPage />);

        await waitFor(() => {
            // First ticket is not overdue
            expect(screen.getByText('Status: Open')).toBeInTheDocument();
            // Second ticket is overdue
            expect(screen.getByText('Status: Overdue')).toBeInTheDocument();
        });
    });

    test('sends Authorization header with fetch request', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                status: 200,
                json: () => Promise.resolve([]),
            })
        );

        renderWithRouter(<StaffDashboardPage />);

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                '/api/staff-dashboard/?filtering=open',
                {
                    headers: {
                        Authorization: 'Bearer test-token-123',
                    },
                }
            );
        });
    });

    test('changing filter triggers new fetch with correct filter value', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                status: 200,
                json: () => Promise.resolve([]),
            })
        );

        renderWithRouter(<StaffDashboardPage />);

        // Initial fetch with "open"
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                '/api/staff-dashboard/?filtering=open',
                expect.any(Object)
            );
        });

        // Change filter to "closed"
        const select = screen.getByRole('combobox');
        fireEvent.change(select, { target: { value: 'closed' } });

        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                '/api/staff-dashboard/?filtering=closed',
                expect.any(Object)
            );
        });
    });

    test('redirects to login on 401 unauthorized', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                status: 401,
                json: () => Promise.resolve({ error: 'Unauthorized' }),
            })
        );

        renderWithRouter(<StaffDashboardPage />);

        await waitFor(() => {
            expect(global.alert).toHaveBeenCalledWith(
                'You do not have permission to access this page.'
            );
            expect(localStorage.getItem('access')).toBeNull();
            expect(mockNavigate).toHaveBeenCalledWith('/login');
        });
    });

    test('handles fetch error gracefully', async () => {
        const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

        global.fetch = jest.fn(() => Promise.reject(new Error('Network error')));

        renderWithRouter(<StaffDashboardPage />);

        await waitFor(() => {
            expect(consoleSpy).toHaveBeenCalledWith('Error:', expect.any(Error));
        });

        consoleSpy.mockRestore();
    });

    test('tickets are clickable links to ticket detail page', async () => {
        global.fetch = jest.fn(() =>
            Promise.resolve({
                status: 200,
                json: () => Promise.resolve(mockTickets),
            })
        );

        renderWithRouter(<StaffDashboardPage />);

        await waitFor(() => {
            const links = screen.getAllByRole('link');
            expect(links[0]).toHaveAttribute('href', '/ticket/1');
            expect(links[1]).toHaveAttribute('href', '/ticket/2');
        });
    });
});
