import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

import Signup from "./Signup";

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

jest.mock("./api", () => ({
  apiFetch: jest.fn(),
}));

import { apiFetch } from "./api";

describe("Signup", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("submits registration and redirects to login", async () => {
    apiFetch.mockResolvedValue({});

    render(<Signup />);

    await userEvent.type(screen.getByLabelText(/username/i), "newuser");
    await userEvent.type(screen.getByLabelText(/^email$/i), "n@kcl.ac.uk");
    await userEvent.type(screen.getByLabelText(/^password$/i), "secret123");
    await userEvent.type(screen.getByLabelText(/k number/i), "K1234567");

    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        "/auth/register/",
        expect.objectContaining({ method: "POST" })
      );
    });
    expect(mockNavigate).toHaveBeenCalledWith("/login");
  });

  test("shows error when registration fails", async () => {
    apiFetch.mockRejectedValue(new Error("Email already exists"));

    render(<Signup />);

    await userEvent.type(screen.getByLabelText(/username/i), "u");
    await userEvent.type(screen.getByLabelText(/^email$/i), "e@e.com");
    await userEvent.type(screen.getByLabelText(/^password$/i), "p");
    await userEvent.type(screen.getByLabelText(/k number/i), "K1");

    await userEvent.click(screen.getByRole("button", { name: /create account/i }));

    expect(await screen.findByText(/Email already exists/i)).toBeInTheDocument();
  });
});
