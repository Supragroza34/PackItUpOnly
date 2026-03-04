import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Provider } from "react-redux";
import { MemoryRouter } from "react-router-dom";
import { configureStore } from "@reduxjs/toolkit";

import UserDashboardPage from "./UserDashboardPage";

// Mock AuthContext
jest.mock("../context/AuthContext", () => ({
  useAuth: () => ({ logout: jest.fn() }),
}));

// Mock react-router navigate
const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

function renderWithStore(preloadedState) {
  const store = configureStore({
    reducer: {
      auth: (state = preloadedState.auth) => state,
    },
    preloadedState,
  });

  return render(
    <Provider store={store}>
      <MemoryRouter>
        <UserDashboardPage />
      </MemoryRouter>
    </Provider>
  );
}

describe("UserDashboardPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test("shows loading state when no user", () => {
    const preloadedState = { auth: { user: null, loading: true } };
    renderWithStore(preloadedState);
    expect(screen.getByText(/loading your dashboard/i)).toBeInTheDocument();
  });

  test("redirects to login if no token", async () => {
    const preloadedState = { auth: { user: { first_name: "John", last_name: "Doe" }, loading: false } };
    renderWithStore(preloadedState);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });
  });

  test("renders tickets after successful fetch", async () => {
    localStorage.setItem("access", "fake-token");

    const tickets = [
      {
        id: 1,
        type_of_issue: "Login issue",
        department: "IT",
        additional_details: "Cannot login",
        status: "pending",
        priority: "high",
        created_at: "2025-01-01T10:00:00Z",
        replies: [],
      },
    ];

    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets }) })
    );

    const preloadedState = { auth: { user: { first_name: "John", last_name: "Doe" }, loading: false } };
    renderWithStore(preloadedState);

    expect(await screen.findByText(/login issue/i)).toBeInTheDocument();
    expect(screen.getByText(/it/i)).toBeInTheDocument();
    expect(screen.getByText(/cannot login/i)).toBeInTheDocument();
  });

  test("shows empty state when no tickets", async () => {
    localStorage.setItem("access", "fake-token");

    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets: [] }) })
    );

    const preloadedState = { auth: { user: { first_name: "Jane", last_name: "Smith" }, loading: false } };
    renderWithStore(preloadedState);

    expect(await screen.findByText(/you haven't submitted any tickets/i)).toBeInTheDocument();
  });

  test("opens and closes ticket modal", async () => {
    localStorage.setItem("access", "fake-token");

    const tickets = [
      {
        id: 2,
        type_of_issue: "Email problem",
        department: "Support",
        additional_details: "Emails not sending",
        status: "in_progress",
        priority: "medium",
        created_at: "2025-01-02T12:00:00Z",
        replies: [],
      },
    ];

    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets }) })
    );

    const preloadedState = { auth: { user: { first_name: "Sam", last_name: "Lee" }, loading: false } };
    renderWithStore(preloadedState);

    const ticketItem = await screen.findByText(/email problem/i);
    fireEvent.click(ticketItem);

    expect(screen.getByText(/responses from staff/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText("X"));
    await waitFor(() => {
      expect(screen.queryByText(/responses from staff/i)).not.toBeInTheDocument();
    });
  });

  test("handles server error", async () => {
    localStorage.setItem("access", "fake-token");

    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: false, status: 500, text: () => Promise.resolve("Error") })
    );

    const preloadedState = { auth: { user: { first_name: "Alex", last_name: "Ray" }, loading: false } };
    renderWithStore(preloadedState);

    expect(await screen.findByText(/server error/i)).toBeInTheDocument();
  });

  test("navigates to FAQs and Create Ticket pages", () => {
    const preloadedState = { auth: { user: { first_name: "John", last_name: "Doe" }, loading: false } };
    renderWithStore(preloadedState);

    // FAQs link
    const faqsLink = screen.getByText(/view faqs/i);
    expect(faqsLink).toBeInTheDocument();
    expect(faqsLink.getAttribute("href")).toBe("/faqs");

    // Create ticket link
    const createLink = screen.getByText(/create new ticket/i);
    expect(createLink).toBeInTheDocument();
    expect(createLink.getAttribute("href")).toBe("/create-ticket");
  });
});
