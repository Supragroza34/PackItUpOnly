import { configureStore } from '@reduxjs/toolkit';
import authReducer, { checkAuth, login, logout, clearError } from './authSlice';

jest.mock('../../services/adminApi', () => ({
  __esModule: true,
  default: {
    getCurrentUser: jest.fn(),
  },
}));

jest.mock('../../api', () => ({
  apiFetch: jest.fn(),
}));

import adminApi from '../../services/adminApi';
import { apiFetch } from '../../api';

describe('authSlice', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  describe('reducers', () => {
    test('clearError sets error to null', () => {
      const store = configureStore({
        reducer: { auth: authReducer },
        preloadedState: {
          auth: {
            user: null,
            loading: false,
            error: 'Some error',
            isAuthenticated: false,
          },
        },
      });
      store.dispatch(clearError());
      expect(store.getState().auth.error).toBeNull();
    });
  });

  describe('checkAuth', () => {
    test('returns null when no token in localStorage', async () => {
      const store = configureStore({ reducer: { auth: authReducer } });
      await store.dispatch(checkAuth());
      const state = store.getState().auth;
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(adminApi.getCurrentUser).not.toHaveBeenCalled();
    });

    test('fulfills with user data when token exists', async () => {
      localStorage.setItem('access', 'token123');
      const mockUser = { id: 1, username: 'admin' };
      adminApi.getCurrentUser.mockResolvedValue(mockUser);

      const store = configureStore({ reducer: { auth: authReducer } });
      await store.dispatch(checkAuth());

      const state = store.getState().auth;
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(state.loading).toBe(false);
    });

    test('rejects and clears user on API error', async () => {
      localStorage.setItem('access', 'token123');
      adminApi.getCurrentUser.mockRejectedValue(new Error('Failed'));

      const store = configureStore({ reducer: { auth: authReducer } });
      await store.dispatch(checkAuth());

      const state = store.getState().auth;
      expect(state.user).toBeNull();
      expect(state.isAuthenticated).toBe(false);
      expect(state.error).toBe('Failed');
    });
  });

  describe('login', () => {
    test('fulfills with user after successful login', async () => {
      apiFetch.mockResolvedValue({ access: 'at', refresh: 'rt' });
      const mockUser = { id: 1, username: 'admin' };
      adminApi.getCurrentUser.mockResolvedValue(mockUser);

      const store = configureStore({ reducer: { auth: authReducer } });
      await store.dispatch(login({ username: 'admin', password: 'pass' }));

      const state = store.getState().auth;
      expect(state.user).toEqual(mockUser);
      expect(state.isAuthenticated).toBe(true);
      expect(localStorage.getItem('access')).toBe('at');
      expect(localStorage.getItem('refresh')).toBe('rt');
    });

    test('rejects with Invalid username or password on 401', async () => {
      apiFetch.mockRejectedValue(new Error('401 Unauthorized'));

      const store = configureStore({ reducer: { auth: authReducer } });
      await store.dispatch(login({ username: 'bad', password: 'bad' }));

      expect(store.getState().auth.error).toBe('Invalid username or password');
    });

    test('rejects with Network error on fetch/network error', async () => {
      apiFetch.mockRejectedValue(new Error('network error'));

      const store = configureStore({ reducer: { auth: authReducer } });
      await store.dispatch(login({ username: 'u', password: 'p' }));

      expect(store.getState().auth.error).toBe('Network error. Please check your connection.');
    });

    test('rejects with Server error on 500', async () => {
      apiFetch.mockRejectedValue(new Error('500 Internal Server Error'));

      const store = configureStore({ reducer: { auth: authReducer } });
      await store.dispatch(login({ username: 'u', password: 'p' }));

      expect(store.getState().auth.error).toBe('Server error. Please try again later.');
    });
  });

  describe('logout', () => {
    test('clears tokens and user', async () => {
      localStorage.setItem('access', 'at');
      localStorage.setItem('refresh', 'rt');

      const store = configureStore({
        reducer: { auth: authReducer },
        preloadedState: {
          auth: {
            user: { id: 1 },
            loading: false,
            error: null,
            isAuthenticated: true,
          },
        },
      });
      await store.dispatch(logout());

      expect(localStorage.getItem('access')).toBeNull();
      expect(localStorage.getItem('refresh')).toBeNull();
      expect(store.getState().auth.user).toBeNull();
      expect(store.getState().auth.isAuthenticated).toBe(false);
    });
  });
});
