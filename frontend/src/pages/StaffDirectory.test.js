  test("renders staff card with missing fields", async () => {
    apiFetch.mockResolvedValueOnce([{ id: 3 }]);
    render(
      <MemoryRouter>
        <StaffDirectory />
      </MemoryRouter>
    );
    await waitFor(() => {
      expect(screen.getByText("Staff")).toBeInTheDocument();
    });
  });
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
    apiFetch.mockResolvedValueOnce([
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
    apiFetch.mockResolvedValueOnce([
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
    apiFetch.mockResolvedValueOnce([]);

    render(
      <MemoryRouter>
        <StaffDirectory />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/no staff found/i)).toBeInTheDocument();
    });
  });

  test("shows friendly error when staff load fails", async () => {
    apiFetch.mockRejectedValueOnce(new Error("boom"));

    render(
      <MemoryRouter>
        <StaffDirectory />
      </MemoryRouter>
    );

    expect(await screen.findByText(/failed to load staff/i)).toBeInTheDocument();
  });

  test("changes department and re-fetches with encoded query", async () => {
    apiFetch
      .mockResolvedValueOnce([
        { id: 1, first_name: "Ada", last_name: "Lovelace", department: "Computer Science" },
      ])
      .mockResolvedValueOnce([
        { id: 2, first_name: "Bob", last_name: "Builder", department: "Computer Science" },
      ]);

    render(
      <MemoryRouter>
        <StaffDirectory />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("Ada Lovelace")).toBeInTheDocument());
    await userEvent.selectOptions(screen.getByLabelText(/department:/i), "Computer Science");

    await waitFor(() => {
      expect(apiFetch).toHaveBeenLastCalledWith(
        expect.stringContaining("department=Computer%20Science"),
        {},
        { auth: true }
      );
      expect(screen.getByText("Bob Builder")).toBeInTheDocument();
    });
  });

  test("supports pagination controls and page number buttons", async () => {
    const staffRows = Array.from({ length: 13 }, (_, i) => ({
      id: i + 1,
      first_name: `User${i + 1}`,
      last_name: "Staff",
      department: "IT",
    }));
    apiFetch.mockResolvedValueOnce(staffRows);

    render(
      <MemoryRouter>
        <StaffDirectory />
      </MemoryRouter>
    );

    await waitFor(() => expect(screen.getByText("User1 Staff")).toBeInTheDocument());

    const prev = screen.getByRole("button", { name: /prev/i });
    const next = screen.getByRole("button", { name: /next/i });
    expect(prev).toBeDisabled();
    expect(next).not.toBeDisabled();

    await userEvent.click(screen.getByRole("button", { name: "2" }));
    expect(await screen.findByText("User13 Staff")).toBeInTheDocument();
    expect(next).toBeDisabled();

    await userEvent.click(prev);
    expect(await screen.findByText("User1 Staff")).toBeInTheDocument();
  });
});
