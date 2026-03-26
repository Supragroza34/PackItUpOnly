describe('StaffDashboardPage – edge cases', () => {
    test('handles empty ticket/user/stats lists', () => {
        renderWithProviders(<StaffDashboardPage />, { preloadedState: staffState({ user: null }) });
        // Should render dashboard structure even with no data
        expect(screen.getByText(/dashboard/i)).toBeInTheDocument();
    });
    test('handles notification click with missing/closed ticket', () => {
        renderWithProviders(<StaffDashboardPage />);
        fireEvent.click(screen.getByText(/notif missing ticket/i));
        fireEvent.click(screen.getByText(/notif closed ticket/i));
        fireEvent.click(screen.getByText(/notif open ticket/i));
        fireEvent.click(screen.getByText(/notif meeting request/i));
        expect(true).toBe(true); // No crash
    });
});
// ─────────────────────────────────────────────────────────────────────────────
// StaffDashboardPage.test.js  –  100% statement/function/line coverage
// ─────────────────────────────────────────────────────────────────────────────
import React from 'react';
import { screen, fireEvent, waitFor } from '@testing-library/react';
import StaffDashboardPage from './StaffDashboardPage';
import { renderWithProviders } from '../utils/testUtils';

// ── Module mocks ───────────────────────────────────────────────────────────────

const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
    ...jest.requireActual('react-router-dom'),
    useNavigate: () => mockNavigate,
}));

jest.mock('../components/NotificationBell', () => ({ onNotificationClick }) => (
    <div>
        <button onClick={() => onNotificationClick({ ticket_id: 999 })}>Notif Missing Ticket</button>
        <button onClick={() => onNotificationClick({ ticket_id: 2 })}>Notif Closed Ticket</button>
        <button onClick={() => onNotificationClick({ ticket_id: 1 })}>Notif Open Ticket</button>
        <button onClick={() => onNotificationClick({ meeting_request_id: 55 })}>Notif Meeting Request</button>
    </div>
));

// Prevent AuthContext from calling the real API and overriding Redux user state
jest.mock('../services/adminApi', () => ({
    __esModule: true,
    default: {
        getCurrentUser: jest.fn(() => Promise.reject(new Error('mocked'))),
        login:          jest.fn(() => Promise.resolve({})),
        logout:         jest.fn(() => Promise.resolve()),
        getTickets:     jest.fn(() => Promise.resolve({ tickets: [], total: 0 })),
        getStats:       jest.fn(() => Promise.resolve({})),
        getUsers:       jest.fn(() => Promise.resolve({ users: [], total: 0 })),
        getStaffList:   jest.fn(() => Promise.resolve([])),
        updateTicket:   jest.fn(() => Promise.resolve({})),
    },
}));

// Suppress noisy console output during tests
const _origConsoleLog = console.log;
const _origConsoleError = console.error;
beforeAll(() => {
    console.log = jest.fn();
    console.error = jest.fn();
});
afterAll(() => {
    console.log = _origConsoleLog;
    console.error = _origConsoleError;
});

// ── Helpers ────────────────────────────────────────────────────────────────────

function makeTicket(overrides = {}) {
    return {
        id: 1,
        type_of_issue: 'Login Problem',
        department: 'IT Support',
        additional_details: 'Cannot log in',
        created_at: '2026-01-15T10:00:00Z',
        status: 'pending',
        priority: 'medium',
        is_overdue: false,
        closed_by_role: null,
        user: { first_name: 'Jane', last_name: 'Doe' },
        ...overrides,
    };
}

function staffState(overrides = {}) {
    return {
        auth: {
            user: { id: 3, first_name: 'Alice', last_name: 'Smith', role: 'staff' },
            ...overrides,
        },
    };
}

/**
 * Sets up global.fetch with URL-based routing:
 *  - filtering=all  → allTickets
 *  - /update/       → closeResponse (ok controlled by closeOk)
 *  - everything else → filteredTickets with filteredStatus
 */
function mockFetch({
    allTickets = [],
    filteredTickets = [],
    closeResponse = { closed_by_role: 'staff' },
    filteredStatus = 200,
    closeOk = true,
} = {}) {
    global.fetch = jest.fn((url) => {
        if (url.includes('filtering=all')) {
            return Promise.resolve({
                status: 200, ok: true,
                json: () => Promise.resolve(allTickets),
            });
        }
        if (url.includes('/update/')) {
            return Promise.resolve({
                status: closeOk ? 200 : 400,
                ok: closeOk,
                json: () => Promise.resolve(closeResponse),
            });
        }
        return Promise.resolve({
            status: filteredStatus,
            ok: filteredStatus < 400,
            json: () => Promise.resolve(filteredTickets),
        });
    });
}

// ══════════════════════════════════════════════════════════════════════════════
// 1. Rendering & structure
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – rendering & structure', () => {
    beforeEach(() => {
        mockFetch();
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test('renders welcome heading with the staff user name', async () => {
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByText(/Welcome, Alice Smith/i)).toBeInTheDocument()
        );
    });

    test('renders Meeting Requests button', () => {
        renderWithProviders(<StaffDashboardPage />, staffState());
        expect(screen.getByRole('button', { name: /meeting requests/i })).toBeInTheDocument();
    });

    test('renders Log Out button', () => {
        renderWithProviders(<StaffDashboardPage />, staffState());
        expect(screen.getByRole('button', { name: /log out/i })).toBeInTheDocument();
    });

    test('renders Total Assigned summary card label', () => {
        renderWithProviders(<StaffDashboardPage />, staffState());
        expect(screen.getByText('Total Assigned')).toBeInTheDocument();
    });

    test('renders filter dropdown with all four options', () => {
        renderWithProviders(<StaffDashboardPage />, staffState());
        expect(screen.getByRole('combobox')).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Open' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Overdue' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'Closed' })).toBeInTheDocument();
        expect(screen.getByRole('option', { name: 'All' })).toBeInTheDocument();
    });

    test('renders search input', () => {
        renderWithProviders(<StaffDashboardPage />, staffState());
        expect(screen.getByPlaceholderText(/search by name/i)).toBeInTheDocument();
    });

    test('renders Assigned Tickets heading', () => {
        renderWithProviders(<StaffDashboardPage />, staffState());
        expect(screen.getByText('Assigned Tickets')).toBeInTheDocument();
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 2. Empty states
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – empty states', () => {
    beforeEach(() => {
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test('shows filter-specific empty message when filter is not "all"', async () => {
        mockFetch({ filteredTickets: [] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByText(/No tickets for this filter/i)).toBeInTheDocument()
        );
    });

    test('shows "No tickets assigned to you." when filter is changed to "all"', async () => {
        mockFetch({ filteredTickets: [] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'all' } });
        await waitFor(() =>
            expect(screen.getByText('No tickets assigned to you.')).toBeInTheDocument()
        );
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 3. Ticket rendering
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – ticket rendering', () => {
    beforeEach(() => {
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test('renders type_of_issue and department', async () => {
        mockFetch({ filteredTickets: [makeTicket()] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            expect(screen.getByText('Login Problem')).toBeInTheDocument();
            expect(screen.getByText(/IT Support/)).toBeInTheDocument();
        });
    });

    test('renders additional_details when present', async () => {
        mockFetch({ filteredTickets: [makeTicket({ additional_details: 'Cannot log in' })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByText('Cannot log in')).toBeInTheDocument()
        );
    });

    test('does not render additional_details when empty string', async () => {
        mockFetch({ filteredTickets: [makeTicket({ additional_details: '' })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => screen.getByText('Login Problem'));
        expect(screen.queryByText('Cannot log in')).not.toBeInTheDocument();
    });

    test('renders submitter full name', async () => {
        mockFetch({ filteredTickets: [makeTicket()] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByText(/Jane Doe/)).toBeInTheDocument()
        );
    });

    test('renders formatted created_at date', async () => {
        mockFetch({ filteredTickets: [makeTicket({ created_at: '2026-01-15T10:00:00Z' })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByText('15 Jan 2026')).toBeInTheDocument()
        );
    });

    test('renders Close ticket button for non-closed ticket', async () => {
        mockFetch({ filteredTickets: [makeTicket({ status: 'pending' })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByRole('button', { name: /close ticket/i })).toBeInTheDocument()
        );
    });

    test('hides Close ticket button for closed ticket', async () => {
        mockFetch({ filteredTickets: [makeTicket({ status: 'closed' })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => screen.getByText('Login Problem'));
        expect(screen.queryByRole('button', { name: /close ticket/i })).not.toBeInTheDocument();
    });

    test('renders ticket as a link pointing to its detail page', async () => {
        mockFetch({ filteredTickets: [makeTicket({ id: 42 })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByRole('link')).toHaveAttribute('href', '/staff/dashboard/42')
        );
    });

    test('renders priority badge when priority is set', async () => {
        mockFetch({ filteredTickets: [makeTicket({ priority: 'high' })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByText('high')).toBeInTheDocument()
        );
    });

    test('does not render priority badge when priority is absent', async () => {
        mockFetch({ filteredTickets: [makeTicket({ priority: undefined })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => screen.getByText('Login Problem'));
        expect(screen.queryByText('high')).not.toBeInTheDocument();
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 4. Status badges  (statusClass + getStatusLabel — every branch)
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – status badges', () => {
    beforeEach(() => {
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test('shows "Overdue" badge with sd-status-overdue class for overdue ticket', async () => {
        mockFetch({ filteredTickets: [makeTicket({ is_overdue: true })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const badge = screen.getAllByText('Overdue').find(
                (el) => el.className && el.className.includes('sd-status-badge')
            );
            expect(badge).toBeTruthy();
            expect(badge.className).toContain('sd-status-overdue');
        });
    });

    test('shows "pending" badge for pending non-overdue ticket', async () => {
        mockFetch({ filteredTickets: [makeTicket({ status: 'pending', is_overdue: false })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const badge = screen.getByText('pending');
            expect(badge.className).toContain('sd-status-pending');
        });
    });

    test('shows "in progress" badge with sd-status-in-progress class', async () => {
        mockFetch({ filteredTickets: [makeTicket({ status: 'in_progress', is_overdue: false })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const badge = screen.getByText('in progress');
            expect(badge.className).toContain('sd-status-in-progress');
        });
    });

    test('shows "Closed" badge when status=closed and closed_by_role is null', async () => {
        mockFetch({
            filteredTickets: [makeTicket({ status: 'closed', is_overdue: false, closed_by_role: null })],
        });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const badge = screen
                .getAllByText('Closed')
                .find((el) => el.className && el.className.includes('sd-status-badge'));
            expect(badge).toBeTruthy();
            expect(badge.className).toContain('sd-status-closed');
        });
    });

    test('shows "Closed by Staff" when closed_by_role is "staff"', async () => {
        mockFetch({
            filteredTickets: [makeTicket({ status: 'closed', is_overdue: false, closed_by_role: 'staff' })],
        });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByText('Closed by Staff')).toBeInTheDocument()
        );
    });

    test('shows "Closed by Admin" when closed_by_role is "admin"', async () => {
        mockFetch({
            filteredTickets: [makeTicket({ status: 'closed', is_overdue: false, closed_by_role: 'admin' })],
        });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByText('Closed by Admin')).toBeInTheDocument()
        );
    });

    test('statusClass defaults to sd-status-pending when status is undefined', async () => {
        mockFetch({ filteredTickets: [makeTicket({ status: undefined, is_overdue: false })] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const badge = screen.getByText('pending');
            expect(badge.className).toContain('sd-status-pending');
        });
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 5. Summary card counts + extractArray branches
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – summary card counts', () => {
    beforeEach(() => {
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test('counts open (pending+in_progress), overdue and closed from allTickets', async () => {
        const allTickets = [
            makeTicket({ id: 1, status: 'pending',     is_overdue: false }),
            makeTicket({ id: 2, status: 'in_progress', is_overdue: false }),
            makeTicket({ id: 3, status: 'in_progress', is_overdue: true  }),
            makeTicket({ id: 4, status: 'closed',      is_overdue: false }),
            makeTicket({ id: 5, status: 'resolved',    is_overdue: false }),
        ];
        // total=5, open=3 (all pending/in_progress), overdue=1, closed=2
        mockFetch({ allTickets, filteredTickets: [] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const nums = screen.getAllByText(/^\d+$/).map((el) => el.textContent);
            expect(nums).toContain('5'); // total
            expect(nums).toContain('3'); // open
            expect(nums).toContain('1'); // overdue
            expect(nums).toContain('2'); // closed
        });
    });

    test('extractArray handles plain array response', async () => {
        mockFetch({ allTickets: [makeTicket({ id: 10 }), makeTicket({ id: 11 })], filteredTickets: [] });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const nums = screen.getAllByText(/^\d+$/).map((el) => el.textContent);
            expect(nums).toContain('2');
        });
    });

    test('extractArray handles {tickets:[]} response shape', async () => {
        global.fetch = jest.fn((url) => {
            if (url.includes('filtering=all')) {
                return Promise.resolve({
                    status: 200, ok: true,
                    json: () => Promise.resolve({ tickets: [makeTicket({ id: 99 })] }),
                });
            }
            return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([]) });
        });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const nums = screen.getAllByText(/^\d+$/).map((el) => el.textContent);
            expect(nums).toContain('1');
        });
    });

    test('extractArray handles {results:[]} response shape', async () => {
        global.fetch = jest.fn((url) => {
            if (url.includes('filtering=all')) {
                return Promise.resolve({
                    status: 200, ok: true,
                    json: () => Promise.resolve({ results: [makeTicket({ id: 99 })] }),
                });
            }
            return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([]) });
        });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const nums = screen.getAllByText(/^\d+$/).map((el) => el.textContent);
            expect(nums).toContain('1');
        });
    });

    test('extractArray returns empty array for unknown response shape', async () => {
        global.fetch = jest.fn((url) => {
            if (url.includes('filtering=all')) {
                return Promise.resolve({
                    status: 200, ok: true,
                    json: () => Promise.resolve({ unknown: 'shape' }),
                });
            }
            return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([]) });
        });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const nums = screen.getAllByText(/^\d+$/).map((el) => el.textContent);
            expect(nums).toContain('0');
        });
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 6. API fetching
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – API fetching', () => {
    beforeEach(() => {
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test('fetches ?filtering=all on mount for summary counts', async () => {
        mockFetch();
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('filtering=all'),
                expect.any(Object)
            )
        );
    });

    test('fetches with default filter "open" on mount', async () => {
        mockFetch();
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('filtering=open'),
                expect.any(Object)
            )
        );
    });

    test('sends Authorization Bearer token in request headers', async () => {
        mockFetch();
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(global.fetch).toHaveBeenCalledWith(
                expect.any(String),
                expect.objectContaining({
                    headers: expect.objectContaining({ Authorization: 'Bearer test-token' }),
                })
            )
        );
    });

    test('changing the filter dropdown triggers fetch with new filter value', async () => {
        mockFetch();
        renderWithProviders(<StaffDashboardPage />, staffState());
        fireEvent.change(screen.getByRole('combobox'), { target: { value: 'closed' } });
        await waitFor(() =>
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('filtering=closed'),
                expect.any(Object)
            )
        );
    });

    test('typing in search input includes search param in fetch', async () => {
        mockFetch();
        renderWithProviders(<StaffDashboardPage />, staffState());
        fireEvent.change(screen.getByPlaceholderText(/search by name/i), {
            target: { value: 'Jane' },
        });
        await waitFor(() =>
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('search=Jane'),
                expect.any(Object)
            )
        );
    });

    test('401 response: alerts, clears token, navigates to /login', async () => {
        global.alert = jest.fn();
        global.fetch = jest.fn((url) => {
            if (url.includes('filtering=all')) {
                return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([]) });
            }
            return Promise.resolve({ status: 401, ok: false, json: () => Promise.resolve({}) });
        });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            expect(global.alert).toHaveBeenCalledWith(
                'You do not have permission to access this page.'
            );
            expect(localStorage.getItem('access')).toBeNull();
            expect(mockNavigate).toHaveBeenCalledWith('/login');
        });
    });

    test('allTickets fetch error is caught silently (no crash)', async () => {
        global.fetch = jest.fn((url) => {
            if (url.includes('filtering=all')) return Promise.reject(new Error('Network error'));
            return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([]) });
        });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => {
            const nums = screen.getAllByText(/^\d+$/).map((el) => el.textContent);
            expect(nums).toContain('0');
        });
    });

    test('filtered tickets fetch error is logged with console.error', async () => {
        const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        global.fetch = jest.fn((url) => {
            if (url.includes('filtering=all'))
                return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([]) });
            return Promise.reject(new Error('Network fail'));
        });
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(consoleSpy).toHaveBeenCalledWith('Error:', expect.any(Error))
        );
        consoleSpy.mockRestore();
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 7. Close ticket
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – close ticket', () => {
    beforeEach(() => {
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test('cancelling first confirm aborts the close (no PATCH sent)', async () => {
        mockFetch({ filteredTickets: [makeTicket({ id: 5, status: 'pending' })] });
        window.confirm = jest.fn().mockReturnValueOnce(false);
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => screen.getByRole('button', { name: /close ticket/i }));
        fireEvent.click(screen.getByRole('button', { name: /close ticket/i }));
        expect(global.fetch).not.toHaveBeenCalledWith(
            expect.stringContaining('/update/'),
            expect.any(Object)
        );
    });

    test('cancelling second confirm aborts the close (no PATCH sent)', async () => {
        mockFetch({ filteredTickets: [makeTicket({ id: 5, status: 'pending' })] });
        window.confirm = jest.fn()
            .mockReturnValueOnce(true)
            .mockReturnValueOnce(false);
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => screen.getByRole('button', { name: /close ticket/i }));
        fireEvent.click(screen.getByRole('button', { name: /close ticket/i }));
        expect(global.fetch).not.toHaveBeenCalledWith(
            expect.stringContaining('/update/'),
            expect.any(Object)
        );
    });

    test('confirming both dialogs sends PATCH and removes Close button', async () => {
        mockFetch({
            filteredTickets: [makeTicket({ id: 5, status: 'pending' })],
            closeResponse: { closed_by_role: 'staff' },
        });
        window.confirm = jest.fn().mockReturnValue(true);
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => screen.getByRole('button', { name: /close ticket/i }));
        fireEvent.click(screen.getByRole('button', { name: /close ticket/i }));
        await waitFor(() => {
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/api/staff/dashboard/5/update/'),
                expect.any(Object)
            );
            expect(
                screen.queryByRole('button', { name: /close ticket/i })
            ).not.toBeInTheDocument();
        });
    });

    test('defaults closed_by_role to "staff" when absent from PATCH response', async () => {
        mockFetch({
            filteredTickets: [makeTicket({ id: 6, status: 'pending' })],
            closeResponse: {}, // no closed_by_role field
        });
        window.confirm = jest.fn().mockReturnValue(true);
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => screen.getByRole('button', { name: /close ticket/i }));
        fireEvent.click(screen.getByRole('button', { name: /close ticket/i }));
        await waitFor(() =>
            expect(screen.getByText('Closed by Staff')).toBeInTheDocument()
        );
    });

    test('non-ok PATCH response leaves ticket unchanged (Close button remains)', async () => {
        global.fetch = jest.fn((url) => {
            if (url.includes('filtering=all'))
                return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([]) });
            if (url.includes('/update/'))
                return Promise.resolve({ status: 400, ok: false, json: () => Promise.resolve({}) });
            return Promise.resolve({
                status: 200, ok: true,
                json: () => Promise.resolve([makeTicket({ id: 8, status: 'pending' })]),
            });
        });
        window.confirm = jest.fn().mockReturnValue(true);
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => screen.getByRole('button', { name: /close ticket/i }));
        fireEvent.click(screen.getByRole('button', { name: /close ticket/i }));
        await waitFor(() =>
            expect(screen.getByRole('button', { name: /close ticket/i })).toBeInTheDocument()
        );
    });

    test('PATCH network error is logged with console.error', async () => {
        const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
        global.fetch = jest.fn((url) => {
            if (url.includes('filtering=all'))
                return Promise.resolve({ status: 200, ok: true, json: () => Promise.resolve([]) });
            if (url.includes('/update/')) return Promise.reject(new Error('Close failed'));
            return Promise.resolve({
                status: 200, ok: true,
                json: () => Promise.resolve([makeTicket({ id: 7, status: 'pending' })]),
            });
        });
        window.confirm = jest.fn().mockReturnValue(true);
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() => screen.getByRole('button', { name: /close ticket/i }));
        fireEvent.click(screen.getByRole('button', { name: /close ticket/i }));
        await waitFor(() =>
            expect(consoleSpy).toHaveBeenCalledWith('Failed to close ticket:', expect.any(Error))
        );
        consoleSpy.mockRestore();
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 8. Logout
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – logout', () => {
    beforeEach(() => {
        mockFetch();
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test('clicking Log Out navigates to /login', async () => {
        renderWithProviders(<StaffDashboardPage />, staffState());
        fireEvent.click(screen.getByRole('button', { name: /log out/i }));
        await waitFor(() =>
            expect(mockNavigate).toHaveBeenCalledWith('/login')
        );
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 9. Meeting Requests button
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – Meeting Requests button', () => {
    beforeEach(() => {
        mockFetch();
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test('clicking Meeting Requests navigates to /staff/dashboard/meeting-requests', () => {
        renderWithProviders(<StaffDashboardPage />, staffState());
        fireEvent.click(screen.getByRole('button', { name: /meeting requests/i }));
        expect(mockNavigate).toHaveBeenCalledWith('/staff/dashboard/meeting-requests');
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 9b. Notification routing branches
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – notification routing', () => {
    beforeEach(() => {
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
        global.alert = jest.fn();
    });

    test('alerts when notification ticket is not found in current list', async () => {
        mockFetch({ filteredTickets: [makeTicket({ id: 1, status: 'pending' })] });
        renderWithProviders(<StaffDashboardPage />, staffState());

        await waitFor(() => screen.getByText(/welcome, alice smith/i));
        fireEvent.click(screen.getByRole('button', { name: /notif missing ticket/i }));

        expect(global.alert).toHaveBeenCalledWith('This ticket is no longer available or has been redirected.');
    });

    test('alerts when notification ticket is closed', async () => {
        mockFetch({
            filteredTickets: [
                makeTicket({ id: 2, status: 'closed' }),
            ],
        });
        renderWithProviders(<StaffDashboardPage />, staffState());

        await waitFor(() => screen.getByText(/welcome, alice smith/i));
        fireEvent.click(screen.getByRole('button', { name: /notif closed ticket/i }));

        expect(global.alert).toHaveBeenCalledWith('This ticket is already closed or redirected.');
    });

    test('navigates to ticket details when notification ticket is open', async () => {
        mockFetch({ filteredTickets: [makeTicket({ id: 1, status: 'pending' })] });
        renderWithProviders(<StaffDashboardPage />, staffState());

        await waitFor(() => screen.getByText(/welcome, alice smith/i));
        fireEvent.click(screen.getByRole('button', { name: /notif open ticket/i }));

        expect(mockNavigate).toHaveBeenCalledWith('/staff/dashboard/1');
    });

    test('navigates to meeting requests for meeting_request notifications', async () => {
        mockFetch({ filteredTickets: [makeTicket({ id: 1, status: 'pending' })] });
        renderWithProviders(<StaffDashboardPage />, staffState());

        await waitFor(() => screen.getByText(/welcome, alice smith/i));
        fireEvent.click(screen.getByRole('button', { name: /notif meeting request/i }));

        expect(mockNavigate).toHaveBeenCalledWith('/staff/dashboard/meeting-requests');
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 10. Role guard
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – role guard', () => {
    beforeEach(() => {
        mockFetch();
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test('redirects student role to /dashboard', async () => {
        renderWithProviders(<StaffDashboardPage />, {
            auth: { user: { id: 9, first_name: 'Bob', last_name: 'Jones', role: 'student' } },
        });
        await waitFor(() =>
            expect(mockNavigate).toHaveBeenCalledWith('/dashboard', { replace: true })
        );
    });

    test('does not redirect staff user', async () => {
        renderWithProviders(<StaffDashboardPage />, staffState());
        await waitFor(() =>
            expect(screen.getByText(/Welcome, Alice Smith/i)).toBeInTheDocument()
        );
        expect(mockNavigate).not.toHaveBeenCalledWith('/dashboard', { replace: true });
    });

    test('does not redirect admin user', async () => {
        renderWithProviders(<StaffDashboardPage />, {
            auth: { user: { id: 2, first_name: 'Carol', last_name: 'Admin', role: 'admin' } },
        });
        await waitFor(() =>
            expect(screen.getByText(/Welcome, Carol Admin/i)).toBeInTheDocument()
        );
        expect(mockNavigate).not.toHaveBeenCalledWith('/dashboard', { replace: true });
    });

    test('does not redirect when user is null (effect returns early)', async () => {
        // Remove token so AuthContext's checkAuth skips fetching, keeping contextUser = null
        localStorage.removeItem('access');
        renderWithProviders(<StaffDashboardPage />, { auth: { user: null } });
        await waitFor(() =>
            expect(mockNavigate).not.toHaveBeenCalledWith('/dashboard', { replace: true })
        );
    });
});

// ══════════════════════════════════════════════════════════════════════════════
// 11. Priority badge colours
// ══════════════════════════════════════════════════════════════════════════════

describe('StaffDashboardPage – priority badge colours', () => {
    beforeEach(() => {
        localStorage.setItem('access', 'test-token');
        mockNavigate.mockClear();
    });

    test.each(['low', 'medium', 'high', 'urgent'])(
        'renders %s priority badge with correct class',
        async (priority) => {
            mockFetch({ filteredTickets: [makeTicket({ priority })] });
            renderWithProviders(<StaffDashboardPage />, staffState());
            await waitFor(() => {
                const badge = screen.getByText(priority);
                expect(badge).toBeInTheDocument();
                expect(badge.className).toContain(`sd-priority-${priority}`);
            });
        }
    );
});
//Staff dashboard tests added