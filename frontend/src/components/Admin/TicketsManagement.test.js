import React from "react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import TicketsManagement from "./TicketsManagement";
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
    getTickets: jest.fn(),
    getStaffList: jest.fn(),
    getTicketDetail: jest.fn(),
    updateTicket: jest.fn(),
    deleteTicket: jest.fn(),
  },
}));

jest.mock("./AdminTopbar", () => ({ user, handleLogout }) => (
  <div>
    <span>Welcome, {user?.first_name || "Admin"}</span>
    <button onClick={handleLogout}>Topbar Logout</button>
  </div>
));

function renderTickets(preloadedAdmin = {}, preloadedAuth = {}) {
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
      <TicketsManagement />
    </Provider>
  );
}

describe("TicketsManagement", () => {
  const tickets = [
    {
      id: 1,
      user_name: "John Doe",
      user_k_number: "K123",
      department: "IT",
      type_of_issue: "Login",
      status: "pending",
      priority: "high",
      assigned_to: null,
      created_at: "2026-02-10T10:00:00Z",
    },
    {
      id: 2,
      user_name: "Jane Doe",
      user_k_number: "K124",
      department: "CS",
      type_of_issue: "Access",
      status: "closed",
      closed_by_role: "staff",
      priority: "low",
      assigned_to: 2,
      created_at: "2026-02-11T10:00:00Z",
    },
  ];

  const detailedTicket = {
    id: 1,
    user: {
      first_name: "John",
      last_name: "Doe",
      k_number: "K123",
      email: "john@example.com",
    },
    department: "IT",
    type_of_issue: "Login",
    additional_details: "Cannot login",
    created_at: "2026-02-10T10:00:00Z",
    status: "pending",
    priority: "high",
    assigned_to: 2,
    admin_notes: "Investigating",
    replies: [
      {
        id: 11,
        user_username: "student1",
        body: "Please help",
        created_at: "2026-02-10T11:00:00Z",
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
    window.alert = jest.fn();
    window.confirm = jest.fn(() => true);
    global.fetch = jest.fn();
    localStorage.setItem("access", "token123");

    adminApi.getTickets.mockResolvedValue({
      tickets,
      total: tickets.length,
      total_pages: 2,
    });
    adminApi.getStaffList.mockResolvedValue([
      { id: 2, first_name: "Staff", last_name: "One", role: "staff" },
      { id: 3, first_name: "Staff", last_name: "Two", role: "staff" },
    ]);
    adminApi.getTicketDetail.mockResolvedValue(detailedTicket);
    adminApi.updateTicket.mockResolvedValue({ ...detailedTicket, status: "resolved" });
    adminApi.deleteTicket.mockResolvedValue({});
  });

  test("shows loading state", () => {
    renderTickets({ ticketsLoading: true });
    expect(screen.getByText(/loading tickets/i)).toBeInTheDocument();
  });

  test("shows error state when ticket fetch fails", async () => {
    adminApi.getTickets.mockRejectedValueOnce(new Error("Boom"));
    renderTickets({ ticketsLoading: false, ticketsError: null });

    expect(await screen.findByText(/error: boom/i)).toBeInTheDocument();
  });

  test("renders ticket rows, closed label variants, and no staff hint", async () => {
    adminApi.getStaffList.mockResolvedValueOnce([]);
    renderTickets({ tickets, ticketsTotalPages: 2, staffList: [] });

    expect(await screen.findByText("K123")).toBeInTheDocument();
    expect(screen.getByText(/closed by staff/i)).toBeInTheDocument();
    expect(screen.getAllByText(/no staff in list/i).length).toBeGreaterThan(0);
  });

  test("applies filters and paginates", async () => {
    renderTickets({ tickets, ticketsTotalPages: 2 });

    await waitFor(() => expect(adminApi.getTickets).toHaveBeenCalled());

    fireEvent.change(screen.getByLabelText(/search by name/i), { target: { value: "john" } });
    fireEvent.change(screen.getByDisplayValue("All Statuses"), { target: { value: "pending" } });
    fireEvent.change(screen.getByDisplayValue("All Priorities"), { target: { value: "high" } });
    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));
    const nextBtn = await screen.findByRole("button", { name: /next/i });
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(adminApi.getTickets).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 2 })
      );
    });
  });

  test("assigns ticket with numeric value", async () => {
    renderTickets({ tickets, ticketsTotalPages: 1, staffList: [{ id: 2, first_name: "Staff", last_name: "One" }] });

    expect(await screen.findByText("K123")).toBeInTheDocument();

    const assigns = screen.getAllByTitle(/assign to staff/i);
    fireEvent.change(assigns[0], { target: { value: "2" } });

    await waitFor(() => {
      expect(adminApi.updateTicket).toHaveBeenCalledWith(1, { assigned_to: 2 });
    });
  });

  test("assigns ticket with empty value as null", async () => {
    renderTickets({ tickets, ticketsTotalPages: 1, staffList: [{ id: 2, first_name: "Staff", last_name: "One" }] });

    expect(await screen.findByText("K124")).toBeInTheDocument();

    const assigns = screen.getAllByTitle(/assign to staff/i);
    fireEvent.change(assigns[1], { target: { value: "" } });

    await waitFor(() => {
      expect(adminApi.updateTicket).toHaveBeenCalledWith(2, { assigned_to: null });
    });
  });

  test("handles assign failure", async () => {
    adminApi.updateTicket.mockRejectedValueOnce(new Error("assign failed"));
    renderTickets({ tickets, ticketsTotalPages: 1, staffList: [{ id: 2, first_name: "Staff", last_name: "One" }] });

    expect(await screen.findByText("K123")).toBeInTheDocument();
    fireEvent.change(screen.getAllByTitle(/assign to staff/i)[0], { target: { value: "2" } });

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining("Failed to assign ticket"));
    });
  });

  test("close confirmation branches and successful close", async () => {
    renderTickets({ tickets, ticketsTotalPages: 1 });
    expect(await screen.findByText("K123")).toBeInTheDocument();

    window.confirm
      .mockReturnValueOnce(false)
      .mockReturnValueOnce(true)
      .mockReturnValueOnce(false)
      .mockReturnValueOnce(true)
      .mockReturnValueOnce(true);

    const closeBtn = screen.getAllByRole("button", { name: "Close" })[0];

    fireEvent.click(closeBtn);
    fireEvent.click(closeBtn);
    expect(adminApi.updateTicket).not.toHaveBeenCalledWith(1, { status: "closed" });

    fireEvent.click(closeBtn);
    await waitFor(() => {
      expect(adminApi.updateTicket).toHaveBeenCalledWith(1, { status: "closed" });
    });
  });

  test("delete cancel and delete failure branches", async () => {
    adminApi.deleteTicket.mockRejectedValueOnce(new Error("delete failed"));
    renderTickets({ tickets, ticketsTotalPages: 1 });

    expect(await screen.findByText("K123")).toBeInTheDocument();

    window.confirm.mockReturnValueOnce(false);
    fireEvent.click(screen.getAllByRole("button", { name: "Delete" })[0]);
    expect(adminApi.deleteTicket).not.toHaveBeenCalled();

    window.confirm.mockReturnValueOnce(true);
    fireEvent.click(screen.getAllByRole("button", { name: "Delete" })[0]);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining("Failed to delete ticket"));
    });
  });

  test("view ticket modal, update success/failure, and close controls", async () => {
    renderTickets({ tickets, ticketsTotalPages: 1, selectedTicket: detailedTicket });

    expect(await screen.findByText("K123")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /view\/edit/i })[0]);

    expect(await screen.findByText(/edit ticket #1/i)).toBeInTheDocument();
    expect(screen.getByText(/please help/i)).toBeInTheDocument();

    const modal = document.querySelector(".modal-content");
    const selects = modal.querySelectorAll("select");
    const statusSelect = selects[0];
    const prioritySelect = selects[1];
    const adminNotes = modal.querySelectorAll("textarea")[1];

    fireEvent.change(statusSelect, { target: { value: "resolved" } });
    fireEvent.change(prioritySelect, { target: { value: "urgent" } });
    fireEvent.change(adminNotes, { target: { value: "Updated notes" } });

    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));
    await waitFor(() => {
      expect(adminApi.updateTicket).toHaveBeenCalledWith(
        1,
        expect.objectContaining({
          status: "resolved",
          priority: "urgent",
          admin_notes: "Updated notes",
        })
      );
    });

    adminApi.updateTicket.mockRejectedValueOnce(new Error("update failed"));
    fireEvent.click(screen.getAllByRole("button", { name: /view\/edit/i })[0]);
    expect(await screen.findByText(/edit ticket #1/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining("Failed to update ticket"));
    });

    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    await waitFor(() => {
      expect(screen.queryByText(/edit ticket #1/i)).not.toBeInTheDocument();
    });
  });

  test("ticket detail fetch failure alerts user", async () => {
    adminApi.getTicketDetail.mockRejectedValueOnce(new Error("detail failed"));
    renderTickets({ tickets, ticketsTotalPages: 1 });

    expect(await screen.findByText("K123")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /view\/edit/i })[0]);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining("Failed to load ticket details"));
    });
  });

  test("reply submit branches: empty, success, and failure", async () => {
    global.fetch.mockResolvedValueOnce({ ok: true, json: async () => ({}) });

    renderTickets({ tickets, ticketsTotalPages: 1, selectedTicket: detailedTicket });
    expect(await screen.findByText("K123")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /view\/edit/i })[0]);

    expect(await screen.findByText(/edit ticket #1/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /send reply/i }));
    expect(global.fetch).not.toHaveBeenCalled();

    fireEvent.change(screen.getByPlaceholderText(/write a reply/i), {
      target: { value: "Admin response" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reply/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/replies/create/",
        expect.objectContaining({
          method: "POST",
          headers: expect.objectContaining({ Authorization: "Bearer token123" }),
        })
      );
    });

    global.fetch.mockResolvedValueOnce({ ok: false });
    fireEvent.change(screen.getByPlaceholderText(/write a reply/i), {
      target: { value: "Another response" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reply/i }));

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining("Failed to send reply"));
    });
  });

  test("topbar logout triggers navigation", async () => {
    renderTickets({ tickets, ticketsTotalPages: 1 });
    fireEvent.click(screen.getByRole("button", { name: /topbar logout/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
  });
});
