import React from "react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import AdminDashboard from "./AdminDashboard";
import adminReducer from "../../store/slices/adminSlice";
import authReducer from "../../store/slices/authSlice";
import adminApi from "../../services/adminApi";

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

jest.mock("../../services/adminApi", () => ({
  __esModule: true,
  default: {
    getDashboardStats: jest.fn(),
    updateTicket: jest.fn(),
  },
}));

jest.mock("./AdminTopbar", () => ({ user, handleLogout }) => (
  <div>
    <span>Welcome, {user?.first_name || "Admin"}</span>
    <button onClick={handleLogout}>Topbar Logout</button>
  </div>
));

function renderDashboard(preloadedAdmin = {}, preloadedAuth = {}) {
  const store = configureStore({
    reducer: {
      admin: adminReducer,
      auth: authReducer,
    },
    preloadedState: {
      auth: {
        user: { id: 99, first_name: "Admin", role: "admin" },
        loading: false,
        error: null,
        isAuthenticated: true,
        ...preloadedAuth,
      },
      admin: {
        stats: null,
        statsLoading: false,
        statsError: null,
        tickets: [],
        ticketsTotal: 0,
        ticketsTotalPages: 1,
        ticketsLoading: false,
        ticketsError: null,
        selectedTicket: null,
        users: [],
        usersTotal: 0,
        usersTotalPages: 1,
        usersLoading: false,
        usersError: null,
        selectedUser: null,
        staffList: [],
        staffListLoading: false,
        staffListError: null,
        statistics: null,
        statisticsLoading: false,
        statisticsError: null,
        ...preloadedAdmin,
      },
    },
  });

  return render(
    <Provider store={store}>
      <AdminDashboard />
    </Provider>
  );
}

describe("AdminDashboard", () => {
  const stats = {
    total_tickets: 3,
    pending_tickets: 1,
    in_progress_tickets: 1,
    resolved_tickets: 0,
    closed_tickets: 1,
    total_users: 5,
    total_students: 3,
    total_staff: 2,
    recent_tickets: [
      {
        id: 11,
        user_name: "John Doe",
        user_k_number: "K123",
        department: "IT",
        type_of_issue: "Login",
        status: "in_progress",
        priority: "high",
        created_at: "2026-03-01T10:00:00Z",
      },
      {
        id: 12,
        user_name: "Jane Doe",
        user_k_number: "K124",
        department: "CS",
        type_of_issue: "Access",
        status: "closed",
        closed_by_role: "staff",
        priority: "medium",
        created_at: "2026-03-02T10:00:00Z",
      },
      {
        id: 13,
        user_name: "Sam Doe",
        user_k_number: "K125",
        department: "HR",
        type_of_issue: "Other",
        status: "closed",
        priority: "low",
        created_at: "2026-03-03T10:00:00Z",
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    window.confirm = jest.fn(() => true);
    window.alert = jest.fn();
    adminApi.getDashboardStats.mockResolvedValue(stats);
    adminApi.updateTicket.mockResolvedValue({ ...stats.recent_tickets[0], status: "closed" });
  });

  test("shows loading state", () => {
    renderDashboard({ statsLoading: true });
    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();
  });

  test("shows error state", async () => {
    adminApi.getDashboardStats.mockRejectedValueOnce(new Error("Boom"));
    renderDashboard();
    expect(await screen.findByText(/error: boom/i)).toBeInTheDocument();
  });

  test("shows fallback loading when stats are missing", () => {
    renderDashboard({ stats: null, statsLoading: false, statsError: null });
    expect(screen.getByText(/loading dashboard/i)).toBeInTheDocument();
  });

  test("renders stats table, status labels, and close action visibility", async () => {
    renderDashboard({ stats, statsLoading: false });

    expect(await screen.findByText(/recent tickets/i)).toBeInTheDocument();
    expect(screen.getAllByText(/in progress/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/closed by staff/i)).toBeInTheDocument();
    expect(screen.getAllByText(/^closed$/i).length).toBeGreaterThan(0);
    expect(screen.getByText("K123")).toBeInTheDocument();

    const closeButtons = screen.getAllByRole("button", { name: "Close" });
    expect(closeButtons).toHaveLength(1);
  });

  test("shows no recent tickets state", async () => {
    adminApi.getDashboardStats.mockResolvedValueOnce({ ...stats, recent_tickets: [] });
    renderDashboard();
    expect(await screen.findByText(/no recent tickets/i)).toBeInTheDocument();
  });

  test("close ticket confirmation second step cancel does not update", async () => {
    renderDashboard({ stats, statsLoading: false });
    expect(await screen.findByText("K123")).toBeInTheDocument();

    window.confirm.mockReturnValueOnce(true).mockReturnValueOnce(false);
    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    await waitFor(() => {
      expect(adminApi.updateTicket).not.toHaveBeenCalled();
    });
  });

  test("close ticket success refreshes dashboard", async () => {
    renderDashboard({ stats, statsLoading: false });
    expect(await screen.findByText("K123")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    await waitFor(() => {
      expect(adminApi.updateTicket).toHaveBeenCalledWith(11, { status: "closed" });
      expect(adminApi.getDashboardStats).toHaveBeenCalledTimes(2);
    });
  });

  test("close ticket failure shows alert", async () => {
    adminApi.updateTicket.mockRejectedValueOnce(new Error("cannot close"));
    renderDashboard({ stats, statsLoading: false });
    expect(await screen.findByText("K123")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "Close" }));

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining("Failed to close ticket"));
    });
  });

  test("topbar logout triggers navigate", async () => {
    renderDashboard({ stats, statsLoading: false });
    expect(await screen.findByText(/recent tickets/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /topbar logout/i }));
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
  });
});
