import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import "@testing-library/jest-dom";

import TicketFormPage from "./TicketFormPage";

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

function renderWithRouter(ui) {
  return render(<MemoryRouter>{ui}</MemoryRouter>);
}

jest.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { username: "tester", first_name: "Test" } }),
}));

jest.mock("../components/UserNavbar", () => () => <nav data-testid="navbar" />);

jest.mock("../api", () => ({
  authHeaders: jest.fn(() => ({ Authorization: "Bearer tok" })),
}));

describe("TicketFormPage", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  test("shows validation errors when submitting empty", async () => {
    renderWithRouter(<TicketFormPage />);

    await userEvent.click(screen.getByRole("button", { name: /Submit Ticket/i }));

    expect(await screen.findByText(/Department is required/i)).toBeInTheDocument();
  });

  test("submits multipart form and redirects on success", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 42 }),
    });

    renderWithRouter(<TicketFormPage />);

    await userEvent.selectOptions(screen.getByLabelText(/^Department$/i), "Informatics");
    await userEvent.selectOptions(
      screen.getByLabelText(/^Type of Issue$/i),
      "Software Installation Issues"
    );
    await userEvent.type(
      screen.getByLabelText(/^Additional Details$/i),
      "Cannot install IDE"
    );

    await userEvent.click(screen.getByRole("button", { name: /Submit Ticket/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    });
    expect(await screen.findByText(/ticket #42 submitted successfully/i)).toBeInTheDocument();

    await waitFor(
      () => {
        expect(mockNavigate).toHaveBeenCalledWith("/dashboard");
      },
      { timeout: 4000 }
    );
  });
});
