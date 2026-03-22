import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

import CreateTicketPage from "./CreateTicketPage";

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

jest.mock("../api", () => ({
  apiFetch: jest.fn(),
  authHeaders: jest.fn(() => ({ Authorization: "Bearer x" })),
}));

import { apiFetch } from "../api";

describe("CreateTicketPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("shows validation error when fields empty", async () => {
    render(<CreateTicketPage />);
    await userEvent.click(screen.getByRole("button", { name: /submit ticket/i }));
    expect(
      await screen.findByText(/fill in department/i)
    ).toBeInTheDocument();
    expect(apiFetch).not.toHaveBeenCalled();
  });

  test("submits ticket and navigates to dashboard on success", async () => {
    apiFetch.mockResolvedValue({ id: 1 });

    render(<CreateTicketPage />);

    await userEvent.selectOptions(screen.getByLabelText(/department/i), "Informatics");
    await userEvent.selectOptions(screen.getByLabelText(/type of issue/i), "Technical");
    await userEvent.type(
      screen.getByLabelText(/additional details/i),
      "Need help with VPN"
    );
    await userEvent.click(screen.getByRole("button", { name: /submit ticket/i }));

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        "/tickets/",
        expect.objectContaining({ method: "POST" })
      );
    });
    expect(mockNavigate).toHaveBeenCalledWith("/dashboard", { replace: true });
  });

  test("shows API error message on failure", async () => {
    apiFetch.mockRejectedValue(new Error("Server busy"));

    render(<CreateTicketPage />);

    await userEvent.selectOptions(screen.getByLabelText(/department/i), "Engineering");
    await userEvent.selectOptions(screen.getByLabelText(/type of issue/i), "Access");
    await userEvent.type(screen.getByLabelText(/additional details/i), "Details here");
    await userEvent.click(screen.getByRole("button", { name: /submit ticket/i }));

    expect(await screen.findByText(/Server busy/i)).toBeInTheDocument();
  });

  test("cancel navigates back to dashboard", async () => {
    render(<CreateTicketPage />);
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
  });
});
