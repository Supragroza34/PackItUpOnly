import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";

import PrivateRoute from "./PrivateRoute";
import authReducer from "../store/slices/authSlice";

jest.mock("../context/AuthContext", () => ({
  useAuth: jest.fn(() => ({ user: null })),
}));

import { useAuth } from "../context/AuthContext";

function makeStore(authState) {
  return configureStore({
    reducer: { auth: authReducer },
    preloadedState: { auth: authState },
  });
}

describe("PrivateRoute", () => {
  beforeEach(() => {
    localStorage.clear();
    useAuth.mockReturnValue({ user: null });
  });

  test("shows loading when redux loading and no user", () => {
    const store = makeStore({
      user: null,
      loading: true,
      error: null,
      isAuthenticated: false,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={["/secret"]}>
          <Routes>
            <Route
              path="/secret"
              element={
                <PrivateRoute>
                  <div>Secret</div>
                </PrivateRoute>
              }
            />
            <Route path="/login" element={<div>LoginPage</div>} />
          </Routes>
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText(/Loading/i)).toBeInTheDocument();
  });

  test("renders children when redux user present", () => {
    const store = makeStore({
      user: { id: 1, username: "u" },
      loading: false,
      error: null,
      isAuthenticated: true,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={["/secret"]}>
          <Routes>
            <Route
              path="/secret"
              element={
                <PrivateRoute>
                  <div>Secret</div>
                </PrivateRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText("Secret")).toBeInTheDocument();
  });

  test("uses AuthContext user when redux user null", () => {
    useAuth.mockReturnValue({ user: { id: 2, username: "ctx" } });
    const store = makeStore({
      user: null,
      loading: false,
      error: null,
      isAuthenticated: false,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={["/secret"]}>
          <Routes>
            <Route
              path="/secret"
              element={
                <PrivateRoute>
                  <div>Secret</div>
                </PrivateRoute>
              }
            />
          </Routes>
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText("Secret")).toBeInTheDocument();
  });

  test("redirects to login when no user", () => {
    const store = makeStore({
      user: null,
      loading: false,
      error: null,
      isAuthenticated: false,
    });

    render(
      <Provider store={store}>
        <MemoryRouter initialEntries={["/secret"]}>
          <Routes>
            <Route
              path="/secret"
              element={
                <PrivateRoute>
                  <div>Secret</div>
                </PrivateRoute>
              }
            />
            <Route path="/login" element={<div>LoginPage</div>} />
          </Routes>
        </MemoryRouter>
      </Provider>
    );

    expect(screen.getByText("LoginPage")).toBeInTheDocument();
  });
});
