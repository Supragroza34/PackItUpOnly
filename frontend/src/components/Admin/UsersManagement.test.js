import React from "react";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import UsersManagement from "./UsersManagement";
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
    getUsers: jest.fn(),
    getUserDetail: jest.fn(),
    updateUser: jest.fn(),
    deleteUser: jest.fn(),
  },
}));

jest.mock("./AdminTopbar", () => ({ user, handleLogout }) => (
  <div>
    <span>Welcome, {user?.first_name || "Admin"}</span>
    <button onClick={handleLogout}>Topbar Logout</button>
  </div>
));

function renderUsers(preloadedAdmin = {}, preloadedAuth = {}) {
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
      <UsersManagement />
    </Provider>
  );
}

describe("UsersManagement", () => {
  const users = [
    {
      id: 1,
      username: "student1",
      first_name: "John",
      last_name: "Doe",
      email: "john@example.com",
      role: "student",
      k_number: "K123",
      department: "Computer Science",
    },
    {
      id: 2,
      username: "staff1",
      first_name: "Jane",
      last_name: "Smith",
      email: "jane@example.com",
      role: "staff",
      k_number: "K124",
      department: null,
    },
  ];

  const detailedUser = {
    id: 2,
    username: "staff1",
    first_name: "Jane",
    last_name: "Smith",
    email: "jane@example.com",
    role: "staff",
    k_number: "K124",
    department: "IT Support",
  };

  beforeEach(() => {
    jest.clearAllMocks();
    window.alert = jest.fn();
    window.confirm = jest.fn(() => true);

    adminApi.getUsers.mockResolvedValue({
      users,
      total: users.length,
      total_pages: 2,
    });
    adminApi.getUserDetail.mockResolvedValue(detailedUser);
    adminApi.updateUser.mockResolvedValue(detailedUser);
    adminApi.deleteUser.mockResolvedValue({});
  });

  test("shows loading state", () => {
    renderUsers({ usersLoading: true });
    expect(screen.getByText(/loading users/i)).toBeInTheDocument();
  });

  test("shows error state when users fetch fails", async () => {
    adminApi.getUsers.mockRejectedValueOnce(new Error("Failed users"));
    renderUsers({ usersLoading: false, usersError: null });

    expect(await screen.findByText(/error: failed users/i)).toBeInTheDocument();
  });

  test("renders user rows and department fallback", async () => {
    renderUsers({ users, usersTotalPages: 2 });

    expect(await screen.findByText("student1")).toBeInTheDocument();
    expect(screen.getByText("staff1")).toBeInTheDocument();
    expect(screen.getByText("john@example.com")).toBeInTheDocument();
    expect(screen.getByText("-")).toBeInTheDocument();
  });

  test("applies search/role filters and paginates", async () => {
    renderUsers({ users, usersTotalPages: 2 });

    expect(await screen.findByText("student1")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/search by name/i), {
      target: { value: "john" },
    });
    fireEvent.change(screen.getByDisplayValue("All Roles"), {
      target: { value: "staff" },
    });
    fireEvent.click(screen.getByRole("button", { name: /refresh/i }));
    const nextBtn = await screen.findByRole("button", { name: /next/i });
    fireEvent.click(nextBtn);

    await waitFor(() => {
      expect(adminApi.getUsers).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 2, role: "staff", search: "john" })
      );
    });

    fireEvent.click(screen.getByRole("button", { name: /previous/i }));
    await waitFor(() => {
      expect(adminApi.getUsers).toHaveBeenLastCalledWith(
        expect.objectContaining({ page: 1, role: "staff", search: "john" })
      );
    });
  });

  test("disables deleting your own account", async () => {
    renderUsers({ users, usersTotalPages: 1 }, { user: { id: 1, first_name: "Admin", role: "admin" } });

    expect(await screen.findByText("student1")).toBeInTheDocument();

    const deleteButtons = screen.getAllByRole("button", { name: "Delete" });
    expect(deleteButtons[0]).toBeDisabled();
    expect(deleteButtons[1]).not.toBeDisabled();
  });

  test("delete cancel, success and failure branches", async () => {
    renderUsers({ users, usersTotalPages: 1 }, { user: { id: 99, first_name: "Admin", role: "admin" } });

    expect(await screen.findByText("student1")).toBeInTheDocument();

    const deleteButtons = screen.getAllByRole("button", { name: "Delete" });

    window.confirm.mockReturnValueOnce(false);
    fireEvent.click(deleteButtons[0]);
    expect(adminApi.deleteUser).not.toHaveBeenCalled();

    window.confirm.mockReturnValueOnce(true);
    fireEvent.click(deleteButtons[0]);
    await waitFor(() => {
      expect(adminApi.deleteUser).toHaveBeenCalledWith(1);
      expect(window.alert).toHaveBeenCalledWith("User deleted successfully!");
    });

    adminApi.deleteUser.mockRejectedValueOnce(new Error("delete failed"));
    window.confirm.mockReturnValueOnce(true);
    fireEvent.click(deleteButtons[1]);
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining("Failed to delete user"));
    });
  });

  test("opens user modal and updates user details", async () => {
    renderUsers({ users, usersTotalPages: 1, selectedUser: detailedUser });

    expect(await screen.findByText("student1")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /view\/edit/i })[1]);

    expect(await screen.findByText(/edit user #2/i)).toBeInTheDocument();

    const modal = document.querySelector(".modal-content");
    const inputs = modal.querySelectorAll("input");
    const firstName = inputs[0];
    const lastName = inputs[1];
    const email = inputs[2];
    const department = inputs[3];
    const roleSelect = modal.querySelector("select");

    fireEvent.change(firstName, { target: { value: "Janet" } });
    fireEvent.change(lastName, { target: { value: "UpdatedSmith" } });
    fireEvent.change(email, { target: { value: "updated@example.com" } });
    fireEvent.change(department, { target: { value: "Registry" } });
    fireEvent.change(roleSelect, { target: { value: "admin" } });

    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(adminApi.updateUser).toHaveBeenCalledWith(
        2,
        expect.objectContaining({
          first_name: "Janet",
          last_name: "UpdatedSmith",
          email: "updated@example.com",
          department: "Registry",
          role: "admin",
        })
      );
      expect(window.alert).toHaveBeenCalledWith("User updated successfully!");
    });
  });

  test("modal close button and overlay click close modal", async () => {
    renderUsers({ users, usersTotalPages: 1, selectedUser: detailedUser });

    expect(await screen.findByText("student1")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /view\/edit/i })[1]);
    expect(await screen.findByText(/edit user #2/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /close modal/i }));
    await waitFor(() => {
      expect(screen.queryByText(/edit user #2/i)).not.toBeInTheDocument();
    });

    fireEvent.click(screen.getAllByRole("button", { name: /view\/edit/i })[1]);
    expect(await screen.findByText(/edit user #2/i)).toBeInTheDocument();

    const overlay = document.querySelector(".modal-overlay");
    fireEvent.click(overlay);
    await waitFor(() => {
      expect(screen.queryByText(/edit user #2/i)).not.toBeInTheDocument();
    });
  });

  test("update failure alerts and modal close controls work", async () => {
    adminApi.updateUser.mockRejectedValueOnce(new Error("update failed"));

    renderUsers({ users, usersTotalPages: 1, selectedUser: detailedUser });

    expect(await screen.findByText("student1")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /view\/edit/i })[1]);

    expect(await screen.findByText(/edit user #2/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining("Failed to update user"));
    });

    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    await waitFor(() => {
      expect(screen.queryByText(/edit user #2/i)).not.toBeInTheDocument();
    });
  });

  test("user detail fetch failure alerts", async () => {
    adminApi.getUserDetail.mockRejectedValueOnce(new Error("detail failed"));

    renderUsers({ users, usersTotalPages: 1 });

    expect(await screen.findByText("student1")).toBeInTheDocument();
    fireEvent.click(screen.getAllByRole("button", { name: /view\/edit/i })[0]);

    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining("Failed to load user details"));
    });
  });

  test("topbar logout triggers navigation", async () => {
    renderUsers({ users, usersTotalPages: 1 });

    fireEvent.click(screen.getByRole("button", { name: /topbar logout/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
  });
});
