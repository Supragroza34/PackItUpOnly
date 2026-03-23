import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Provider } from "react-redux";
import { configureStore } from "@reduxjs/toolkit";
import "@testing-library/jest-dom";

import Profile from "./Profile";
import authReducer from "./store/slices/authSlice";

jest.mock("./components/UserNavbar", () => () => <nav data-testid="navbar" />);

jest.mock("./api", () => ({
  apiFetch: jest.fn(),
  authHeaders: jest.fn(() => ({ Authorization: "Bearer t" })),
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

function renderProfile() {
  const store = configureStore({
    reducer: { auth: authReducer },
    preloadedState: {
      auth: {
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
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve(testUser),
    });
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
  });
});
