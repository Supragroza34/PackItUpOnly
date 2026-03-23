import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

import Login from "./Login";

const mockNavigate = jest.fn();
const mockDispatch = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

jest.mock("react-redux", () => ({
  useDispatch: () => mockDispatch,
  useSelector: (fn) => fn({ auth: { user: null } }),
}));

describe("Login", () => {
  beforeEach(() => {
    jest.clearAllMocks();
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
});
