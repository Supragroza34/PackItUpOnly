import { configureStore } from '@reduxjs/toolkit';
import staffReducer, {
  reassignTicket,
  fetchStaffList,
  clearTicketsError,
  clearUsersError,
  setSelectedTicket,
} from './staffSlice';

jest.mock('../../services/staffApi', () => ({
  __esModule: true,
  default: {
    reassignTicket: jest.fn(),
    getStaffList: jest.fn(),
  },
}));

import staffApi from '../../services/staffApi';

describe('staffSlice', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  const createStore = (preloadedState = {}) =>
    configureStore({
      reducer: { staff: staffReducer },
      preloadedState: { staff: preloadedState },
    });

  describe('reducers', () => {
    test('clearTicketsError sets ticketsError to null', () => {
      const store = createStore({ ticketsError: 'err' });
      store.dispatch(clearTicketsError());
      expect(store.getState().staff.ticketsError).toBeNull();
    });
    test('clearUsersError sets usersError to null', () => {
      const store = createStore({ usersError: 'err' });
      store.dispatch(clearUsersError());
      expect(store.getState().staff.usersError).toBeNull();
    });
    test('setSelectedTicket sets selectedTicket', () => {
      const store = createStore({});
      const ticket = { id: 1 };
      store.dispatch(setSelectedTicket(ticket));
      expect(store.getState().staff.selectedTicket).toEqual(ticket);
    });
  });

  describe('reassignTicket', () => {
    test('fulfilled sets ticket', async () => {
      const updated = { id: 1, status: 'in_progress' };
      staffApi.reassignTicket.mockResolvedValue(updated);
      const store = createStore();
      await store.dispatch(reassignTicket({ ticketId: 1, updates: { status: 'in_progress' } }));
      expect(store.getState().staff.ticket).toEqual(updated);
    });
    test('rejected sets error', async () => {
      staffApi.reassignTicket.mockRejectedValue(new Error('fail'));
      const store = createStore();
      await store.dispatch(reassignTicket({ ticketId: 1, updates: {} }));
      expect(store.getState().staff.error).toBeDefined();
    });
  });

  describe('fetchStaffList', () => {
    test('fulfilled sets staffList from staff key', async () => {
      staffApi.getStaffList.mockResolvedValue({ staff: [{ id: 1 }] });
      const store = createStore();
      await store.dispatch(fetchStaffList());
      expect(store.getState().staff.staffList).toEqual([{ id: 1 }]);
      expect(store.getState().staff.staffListLoading).toBe(false);
    });
    test('fulfilled uses payload directly when no staff key', async () => {
      staffApi.getStaffList.mockResolvedValue([{ id: 1 }]);
      const store = createStore();
      await store.dispatch(fetchStaffList());
      expect(store.getState().staff.staffList).toEqual([{ id: 1 }]);
    });
    test('rejected sets staffListError', async () => {
      staffApi.getStaffList.mockRejectedValue(new Error('fail'));
      const store = createStore();
      await store.dispatch(fetchStaffList());
      expect(store.getState().staff.staffListError).toBe('fail');
    });
  });
});
