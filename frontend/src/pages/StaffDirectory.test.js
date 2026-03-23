import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import "@testing-library/jest-dom";

import StaffDirectory from "./StaffDirectory";

jest.mock("../components/UserNavbar", () => () => <nav data-testid="navbar" />);

jest.mock("../api", () => ({
  apiFetch: jest.fn(),
}));

import { apiFetch } from "../api";

describe("StaffDirectory", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("loads departments and staff, shows cards", async () => {
    apiFetch
      .mockResolvedValueOnce(["Informatics", "Engineering"])
      .mockResolvedValueOnce([
        {
          id: 1,
          first_name: "Jane",
          last_name: "Doe",
          department: "Informatics",
        },
      ]);

    render(
      <MemoryRouter>
        <StaffDirectory />
      </MemoryRouter>
    );

    expect(screen.getByTestId("navbar")).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("Jane Doe")).toBeInTheDocument();
    });
    expect(screen.getByRole("link", { name: /book meeting/i })).toHaveAttribute(
      "href",
      "/staff/1"
    );
  });

  test("filters by search", async () => {
    apiFetch
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        { id: 1, first_name: "Alpha", last_name: "One", department: "IT" },
        { id: 2, first_name: "Beta", last_name: "Two", department: "IT" },
      ]);

    render(
      <MemoryRouter>
        <StaffDirectory />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("Alpha One")).toBeInTheDocument());

    await userEvent.type(screen.getByPlaceholderText(/search by name/i), "Beta");
    expect(screen.queryByText("Alpha One")).not.toBeInTheDocument();
    expect(screen.getByText("Beta Two")).toBeInTheDocument();
  });

  test("shows empty message when no staff", async () => {
    apiFetch.mockResolvedValueOnce([]).mockResolvedValueOnce([]);

    render(
      <MemoryRouter>
        <StaffDirectory />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no staff found/i)).toBeInTheDocument();
    });
  });
});
