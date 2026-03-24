import React from "react";
import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

import Login from "./Login";
import { login as loginAction } from "./store/slices/authSlice";

const mockNavigate = jest.fn();
const mockDispatch = jest.fn();
let mockAuthState = { auth: { user: null } };

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

jest.mock("react-redux", () => ({
  useDispatch: () => mockDispatch,
  useSelector: (fn) => fn(mockAuthState),
}));

jest.mock("./store/slices/authSlice", () => ({
  login: jest.fn((payload) => ({ type: "auth/login", payload })),
}));

describe("Login", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    jest.useRealTimers();
    mockAuthState = { auth: { user: null } };
    mockDispatch.mockReturnValue({
      unwrap: () => Promise.resolve({ id: 1, role: "student" }),
    });
  });

  test("shows validation when fields empty", async () => {
    render(<Login />);
    await userEvent.click(screen.getByRole("button", { name: /^login$/i }));
    expect(await screen.findByText(/enter both username and password/i)).toBeInTheDocument();
    expect(mockDispatch).not.toHaveBeenCalled();
  });

  test("dispatches login and navigates student to dashboard", async () => {
    render(<Login />);

    await userEvent.type(screen.getByLabelText(/username/i), "student1");
    await userEvent.type(screen.getByLabelText(/^password$/i), "pass12345");
    await userEvent.click(screen.getByRole("button", { name: /^login$/i }));

    await waitFor(() => {
      expect(mockDispatch).toHaveBeenCalled();
    });
    expect(loginAction).toHaveBeenCalledWith({ username: "student1", password: "pass12345" });
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/dashboard", { replace: true });
    });
  });

  test("navigates admin to admin dashboard", async () => {
    mockDispatch.mockReturnValue({
      unwrap: () => Promise.resolve({ id: 2, role: "admin", is_superuser: false }),
    });

    render(<Login />);
    await userEvent.type(screen.getByLabelText(/username/i), "admin");
    await userEvent.type(screen.getByLabelText(/^password$/i), "pass");
    await userEvent.click(screen.getByRole("button", { name: /^login$/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/admin/dashboard", { replace: true });
    });
  });

  test("navigates staff to staff dashboard", async () => {
    mockDispatch.mockReturnValue({
      unwrap: () => Promise.resolve({ id: 3, role: "staff" }),
    });

    render(<Login />);
    await userEvent.type(screen.getByLabelText(/username/i), "staff1");
    await userEvent.type(screen.getByLabelText(/^password$/i), "pass");
    await userEvent.click(screen.getByRole("button", { name: /^login$/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/staff/dashboard", { replace: true });
    });
  });

  test("redirect effect navigates staff when user appears while loading", async () => {
    mockAuthState = { auth: { user: { id: 7, role: "Staff" } } };
    render(<Login />);

    await userEvent.type(screen.getByLabelText(/username/i), "x");
    await userEvent.type(screen.getByLabelText(/^password$/i), "y");
    await userEvent.click(screen.getByRole("button", { name: /^login$/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/staff/dashboard", { replace: true });
    });
  });

  test("redirect effect navigates admin when user appears while loading", async () => {
    mockAuthState = { auth: { user: { id: 8, role: "admin" } } };
    render(<Login />);

    await userEvent.type(screen.getByLabelText(/username/i), "x");
    await userEvent.type(screen.getByLabelText(/^password$/i), "y");
    await userEvent.click(screen.getByRole("button", { name: /^login$/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/admin/dashboard", { replace: true });
    });
  });

  test("redirect effect navigates student when user appears while loading", async () => {
    mockAuthState = { auth: { user: { id: 9, role: "student" } } };
    render(<Login />);

    await userEvent.type(screen.getByLabelText(/username/i), "x");
    await userEvent.type(screen.getByLabelText(/^password$/i), "y");
    await userEvent.click(screen.getByRole("button", { name: /^login$/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/dashboard", { replace: true });
    });
  });

  test("shows fallback login error message", async () => {
    mockDispatch.mockReturnValue({
      unwrap: () => Promise.reject("")
    });

    render(<Login />);
    await userEvent.type(screen.getByLabelText(/username/i), "user1");
    await userEvent.type(screen.getByLabelText(/^password$/i), "bad");
    await userEvent.click(screen.getByRole("button", { name: /^login$/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Invalid username or password");
  });

  test("toggles password visibility", async () => {
    render(<Login />);

    const pwd = screen.getByLabelText(/^password$/i);
    const toggle = screen.getByRole("button", { name: /show password/i });
    expect(pwd).toHaveAttribute("type", "password");

    await userEvent.click(toggle);
    expect(pwd).toHaveAttribute("type", "text");
    expect(screen.getByRole("button", { name: /hide password/i })).toBeInTheDocument();
  });

  test("prevents double submit while loading", async () => {
    let resolveLogin;
    const pendingLogin = new Promise((resolve) => {
      resolveLogin = resolve;
    });

    mockDispatch.mockReturnValue({
      unwrap: () => pendingLogin,
    });

    render(<Login />);
    await userEvent.type(screen.getByLabelText(/username/i), "student1");
    await userEvent.type(screen.getByLabelText(/^password$/i), "pass");

    const submit = screen.getByRole("button", { name: /^login$/i });
    await userEvent.click(submit);
    await userEvent.click(submit);

    expect(mockDispatch).toHaveBeenCalledTimes(1);

    resolveLogin({ id: 1, role: "student" });
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/dashboard", { replace: true });
    });
  });

  test("syncs browser autofill values before submit", async () => {
    jest.useFakeTimers();
    render(<Login />);

    const userInput = screen.getByLabelText(/username/i);
    const passInput = screen.getByLabelText(/^password$/i);
    userInput.value = "autofilled_user";
    passInput.value = "autofilled_pass";

    act(() => {
      jest.advanceTimersByTime(120);
    });

    fireEvent.click(screen.getByRole("button", { name: /^login$/i }));

    await waitFor(() => {
      expect(loginAction).toHaveBeenCalledWith({
        username: "autofilled_user",
        password: "autofilled_pass",
      });
    });
  });
});
