import { store } from './index';

describe('store', () => {
  test('has auth, admin, and staff reducers', () => {
    const state = store.getState();
    expect(state).toHaveProperty('auth');
    expect(state).toHaveProperty('admin');
    expect(state).toHaveProperty('staff');
  });

  test('auth has initial shape', () => {
    expect(store.getState().auth).toMatchObject({
      user: null,
      loading: expect.any(Boolean),
      isAuthenticated: false,
    });
  });

  test('admin has initial shape', () => {
    const admin = store.getState().admin;
    expect(admin).toHaveProperty('stats');
    expect(admin).toHaveProperty('tickets');
    expect(admin).toHaveProperty('users');
    expect(admin).toHaveProperty('staffList');
  });

  test('staff has initial shape', () => {
    const staff = store.getState().staff;
    expect(staff).toHaveProperty('ticket');
    expect(staff).toHaveProperty('staffList');
  });
});
