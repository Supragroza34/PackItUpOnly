import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import "@testing-library/jest-dom";

import Profile from "./Profile";
import authReducer from "./store/slices/authSlice";
import adminApi from "./services/adminApi";

jest.mock("./components/UserNavbar", () => () => <nav data-testid="navbar" />);

jest.mock("./api", () => ({
  apiFetch: jest.fn(),
  authHeaders: jest.fn(() => ({ Authorization: "Bearer t" })),
}));

jest.mock("./services/adminApi", () => ({
  __esModule: true,
  default: {
    getCurrentUser: jest.fn(),
  },
}));

import { apiFetch } from "./api";

const testUser = {
  id: 1,
  username: "u1",
  email: "u@kcl.ac.uk",
  first_name: "Ann",
  last_name: "Lee",
  k_number: "K999",
  department: "IT",
  role: "student",
};

function renderProfile(preloadedAuth) {
  const store = configureStore({
    reducer: { auth: authReducer },
    preloadedState: {
      auth: preloadedAuth || {
        user: testUser,
        loading: false,
        error: null,
        isAuthenticated: true,
      },
    },
  });

  return render(
    <Provider store={store}>
      <Profile />
    </Provider>
  );
}

describe("Profile", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    sessionStorage.setItem("access", "token");
    adminApi.getCurrentUser.mockResolvedValue(testUser);
  });

  test("renders user fields", async () => {
    renderProfile();

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /profile/i })).toBeInTheDocument();
    });
    expect(screen.getByText(/student/i)).toBeInTheDocument();
    expect(screen.getByDisplayValue("Ann")).toBeInTheDocument();
  });

  test("save updates profile via API", async () => {
    apiFetch.mockResolvedValue({
      ...testUser,
      last_name: "Updated",
    });

    renderProfile();

    await waitFor(() => expect(screen.getByDisplayValue("Lee")).toBeInTheDocument());

    await userEvent.clear(screen.getByPlaceholderText(/last name/i));
    await userEvent.type(screen.getByPlaceholderText(/last name/i), "Updated");
    await userEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        "/users/me/",
        expect.objectContaining({ method: "PATCH" })
      );
    });

    expect(await screen.findByText(/profile updated successfully/i)).toBeInTheDocument();
  });

  test("shows loading state when auth is loading", () => {
    renderProfile({ user: null, loading: true, error: null, isAuthenticated: false });
    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  test("shows save error from API", async () => {
    apiFetch.mockRejectedValueOnce(new Error("Boom"));

    renderProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Ann")).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /save changes/i }));
    expect(await screen.findByText("Boom")).toBeInTheDocument();
  });

  test("uses fallback save error message when error has no message", async () => {
    apiFetch.mockRejectedValueOnce({});

    renderProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Ann")).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /save changes/i }));
    expect(await screen.findByText("Save failed")).toBeInTheDocument();
  });

  test("renders empty editable fields when profile values are null", async () => {
    const nullUser = {
      ...testUser,
      first_name: null,
      last_name: null,
      department: null,
    };

    adminApi.getCurrentUser.mockResolvedValueOnce(nullUser);
    renderProfile({
      user: nullUser,
      loading: false,
      error: null,
      isAuthenticated: true,
    });

    await waitFor(() => expect(screen.getByRole("heading", { name: /my profile/i })).toBeInTheDocument());
    expect(screen.getByPlaceholderText(/first name/i)).toHaveValue("");
    expect(screen.getByPlaceholderText(/last name/i)).toHaveValue("");
    expect(screen.getByPlaceholderText(/department/i)).toHaveValue("");
  });

  test("cancel resets edited fields and clears alerts", async () => {
    renderProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Ann")).toBeInTheDocument());

    const firstName = screen.getByPlaceholderText(/first name/i);
    const dept = screen.getByPlaceholderText(/department/i);
    const lastName = screen.getByPlaceholderText(/last name/i);

    await userEvent.clear(firstName);
    await userEvent.type(firstName, "Annie");
    await userEvent.clear(dept);
    await userEvent.type(dept, "Support");
    await userEvent.clear(lastName);
    await userEvent.type(lastName, "Temp");

    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));

    expect(screen.getByDisplayValue("Ann")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Lee")).toBeInTheDocument();
    expect(screen.getByDisplayValue("IT")).toBeInTheDocument();
    expect(screen.queryByText("Boom")).not.toBeInTheDocument();
  });

  test("shows saving state while save is pending", async () => {
    let resolveSave;
    const pendingSave = new Promise((resolve) => {
      resolveSave = resolve;
    });
    apiFetch.mockReturnValueOnce(pendingSave);

    renderProfile();
    await waitFor(() => expect(screen.getByDisplayValue("Ann")).toBeInTheDocument());

    await userEvent.click(screen.getByRole("button", { name: /save changes/i }));
    expect(screen.getByRole("button", { name: /saving/i })).toBeDisabled();
    expect(screen.getByRole("button", { name: /cancel/i })).toBeDisabled();

    resolveSave({ ...testUser });
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /save changes/i })).toBeInTheDocument();
    });
  });
});
