import React from 'react';
import { render } from '@testing-library/react';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { configureStore } from '@reduxjs/toolkit';
import authReducer from '../store/slices/authSlice';
import adminReducer from '../store/slices/adminSlice';

export const createMockStore = (initialState = {}) => {
  return configureStore({
    reducer: {
      auth: authReducer,
      admin: adminReducer,
    },
    preloadedState: {
      auth: {
        user: { id: 1, username: 'admin', first_name: 'Admin', role: 'admin' },
        loading: false,
        error: null,
        isAuthenticated: true,
        ...initialState.auth,
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
        selectedTicket: null,
        users: [],
        usersTotal: 0,
        usersTotalPages: 0,
        usersLoading: false,
        usersError: null,
        selectedUser: null,
        staffList: [],
        staffListLoading: false,
        staffListError: null,
        ...initialState.admin,
      },
    },
  });
};

export const renderWithProviders = (component, initialState = {}) => {
  const store = createMockStore(initialState);
  return render(
    <Provider store={store}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </Provider>
  );
};
