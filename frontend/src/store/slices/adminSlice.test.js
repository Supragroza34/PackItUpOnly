import { configureStore } from '@reduxjs/toolkit';
import adminReducer, {
  fetchDashboardStats,
  fetchTickets,
  fetchTicketDetail,
  updateTicket,
  deleteTicket,
  fetchUsers,
  fetchUserDetail,
  updateUser,
  deleteUser,
  fetchStaffList,
  fetchStatistics,
  clearTicketsError,
  clearUsersError,
  clearStatsError,
  setSelectedTicket,
  setSelectedUser,
} from './adminSlice';

jest.mock('../../services/adminApi', () => ({
  __esModule: true,
  default: {
    getDashboardStats: jest.fn(),
    getTickets: jest.fn(),
    getTicketDetail: jest.fn(),
    updateTicket: jest.fn(),
    deleteTicket: jest.fn(),
    getUsers: jest.fn(),
    getUserDetail: jest.fn(),
    updateUser: jest.fn(),
    deleteUser: jest.fn(),
    getStaffList: jest.fn(),
    getStatistics: jest.fn(),
  },
}));

import adminApi from '../../services/adminApi';

describe('adminSlice', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const createStore = (preloadedState = {}) =>
    configureStore({
      reducer: { admin: adminReducer },
      preloadedState: { admin: preloadedState },
    });

  describe('reducers', () => {
    test('clearTicketsError clears ticketsError', () => {
      const store = createStore({ ticketsError: 'err' });
      store.dispatch(clearTicketsError());
      expect(store.getState().admin.ticketsError).toBeNull();
    });
    test('clearUsersError clears usersError', () => {
      const store = createStore({ usersError: 'err' });
      store.dispatch(clearUsersError());
      expect(store.getState().admin.usersError).toBeNull();
    });
    test('clearStatsError clears statsError', () => {
      const store = createStore({ statsError: 'err' });
      store.dispatch(clearStatsError());
      expect(store.getState().admin.statsError).toBeNull();
    });
    test('setSelectedTicket sets selectedTicket', () => {
      const store = createStore({});
      const ticket = { id: 1, title: 'T1' };
      store.dispatch(setSelectedTicket(ticket));
      expect(store.getState().admin.selectedTicket).toEqual(ticket);
    });
    test('setSelectedUser sets selectedUser', () => {
      const store = createStore({});
      const user = { id: 2, username: 'u2' };
      store.dispatch(setSelectedUser(user));
      expect(store.getState().admin.selectedUser).toEqual(user);
    });
  });

  describe('fetchDashboardStats', () => {
    test('fulfilled sets stats', async () => {
      const stats = { total_tickets: 10 };
      adminApi.getDashboardStats.mockResolvedValue(stats);
      const store = createStore();
      await store.dispatch(fetchDashboardStats());
      expect(store.getState().admin.stats).toEqual(stats);
      expect(store.getState().admin.statsLoading).toBe(false);
    });
    test('rejected sets statsError', async () => {
      adminApi.getDashboardStats.mockRejectedValue(new Error('fail'));
      const store = createStore();
      await store.dispatch(fetchDashboardStats());
      expect(store.getState().admin.statsError).toBe('fail');
    });
  });

  describe('fetchTickets', () => {
    test('fulfilled sets tickets and pagination', async () => {
      const payload = { tickets: [{ id: 1 }], total: 1, total_pages: 1 };
      adminApi.getTickets.mockResolvedValue(payload);
      const store = createStore();
      await store.dispatch(fetchTickets({ page: 1 }));
      expect(store.getState().admin.tickets).toEqual([{ id: 1 }]);
      expect(store.getState().admin.ticketsTotal).toBe(1);
    });
  });

  describe('fetchTicketDetail', () => {
    test('fulfilled sets selectedTicket', async () => {
      const ticket = { id: 1, title: 'Detail' };
      adminApi.getTicketDetail.mockResolvedValue(ticket);
      const store = createStore();
      await store.dispatch(fetchTicketDetail(1));
      expect(store.getState().admin.selectedTicket).toEqual(ticket);
    });
  });

  describe('updateTicket', () => {
    test('fulfilled updates ticket in list and selectedTicket', async () => {
      const updated = { id: 1, title: 'Updated' };
      adminApi.updateTicket.mockResolvedValue(updated);
      const store = createStore({
        tickets: [{ id: 1, title: 'Old' }],
        selectedTicket: { id: 1, title: 'Old' },
      });
      await store.dispatch(updateTicket({ ticketId: 1, updates: { title: 'Updated' } }));
      expect(store.getState().admin.tickets[0]).toEqual(updated);
      expect(store.getState().admin.selectedTicket).toEqual(updated);
    });
  });

  describe('deleteTicket', () => {
    test('fulfilled removes ticket from list', async () => {
      adminApi.deleteTicket.mockResolvedValue({});
      const store = createStore({
        tickets: [{ id: 1 }],
        selectedTicket: { id: 1 },
      });
      await store.dispatch(deleteTicket(1));
      expect(store.getState().admin.tickets).toHaveLength(0);
      expect(store.getState().admin.selectedTicket).toBeNull();
    });
  });

  describe('fetchUsers', () => {
    test('fulfilled sets users', async () => {
      const payload = { users: [{ id: 1 }], total: 1, total_pages: 1 };
      adminApi.getUsers.mockResolvedValue(payload);
      const store = createStore();
      await store.dispatch(fetchUsers({}));
      expect(store.getState().admin.users).toEqual([{ id: 1 }]);
    });
  });

  describe('fetchUserDetail', () => {
    test('fulfilled sets selectedUser', async () => {
      const user = { id: 1, username: 'u1' };
      adminApi.getUserDetail.mockResolvedValue(user);
      const store = createStore();
      await store.dispatch(fetchUserDetail(1));
      expect(store.getState().admin.selectedUser).toEqual(user);
    });
  });

  describe('updateUser', () => {
    test('fulfilled updates user in list', async () => {
      const updated = { id: 1, username: 'u1-updated' };
      adminApi.updateUser.mockResolvedValue(updated);
      const store = createStore({ users: [{ id: 1, username: 'u1' }] });
      await store.dispatch(updateUser({ userId: 1, updates: {} }));
      expect(store.getState().admin.users[0]).toEqual(updated);
    });
  });

  describe('deleteUser', () => {
    test('fulfilled removes user from list', async () => {
      adminApi.deleteUser.mockResolvedValue({});
      const store = createStore({
        users: [{ id: 1 }],
        selectedUser: { id: 1 },
      });
      await store.dispatch(deleteUser(1));
      expect(store.getState().admin.users).toHaveLength(0);
      expect(store.getState().admin.selectedUser).toBeNull();
    });
  });

  describe('fetchStaffList', () => {
    test('fulfilled sets staffList from staff key', async () => {
      adminApi.getStaffList.mockResolvedValue({ staff: [{ id: 1 }] });
      const store = createStore();
      await store.dispatch(fetchStaffList());
      expect(store.getState().admin.staffList).toEqual([{ id: 1 }]);
    });
    test('fulfilled uses payload directly when no staff key', async () => {
      adminApi.getStaffList.mockResolvedValue([{ id: 1 }]);
      const store = createStore();
      await store.dispatch(fetchStaffList());
      expect(store.getState().admin.staffList).toEqual([{ id: 1 }]);
    });
  });

  describe('fetchStatistics', () => {
    test('fulfilled sets statistics', async () => {
      const stats = { total_tickets: 50 };
      adminApi.getStatistics.mockResolvedValue(stats);
      const store = createStore();
      await store.dispatch(fetchStatistics({}));
      expect(store.getState().admin.statistics).toEqual(stats);
    });
  });
});
