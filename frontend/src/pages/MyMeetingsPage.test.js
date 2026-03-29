  test("renders staff card with missing name and department", async () => {
    apiFetch.mockResolvedValue([
      { id: 3, staff_name: "", staff_department: "", meeting_datetime: "2026-01-15T10:00:00Z", status: "pending", description: "No name" },
      { id: 4, staff_name: "Single", meeting_datetime: "2026-01-15T10:00:00Z", status: "pending", description: "Single name" },
    ]);
    render(<MyMeetingsPage />);
    await waitFor(() => {
      expect(screen.getByText("Staff")).toBeInTheDocument();
      expect(screen.getByText("Single")).toBeInTheDocument();
    });
    // Initials fallback
    expect(screen.getAllByText("S").length).toBeGreaterThan(0);
  });
import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import MyMeetingsPage from "./MyMeetingsPage";

jest.mock("../components/UserNavbar", () => () => <nav data-testid="navbar" />);

jest.mock("../api", () => ({
  apiFetch: jest.fn(),
}));

import { apiFetch } from "../api";

describe("MyMeetingsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("shows loading then meetings", async () => {
    apiFetch.mockResolvedValue([
      {
        id: 1,
        staff_name: "Ada Lovelace",
        staff_department: "Informatics",
        meeting_datetime: "2026-01-15T10:00:00Z",
        status: "pending",
        description: "Discuss project",
      },
    ]);

    render(<MyMeetingsPage />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText("Ada Lovelace")).toBeInTheDocument();
    });
    expect(screen.getByText(/pending/i)).toBeInTheDocument();
    expect(apiFetch).toHaveBeenCalledWith("/meeting-requests/", {}, { auth: true });
  });

  test("shows error when API fails", async () => {
    apiFetch.mockRejectedValue(new Error("Network down"));

    render(<MyMeetingsPage />);

    await waitFor(() => {
      expect(screen.getByText(/Network down/i)).toBeInTheDocument();
    });
  });

  test("shows empty state", async () => {
    apiFetch.mockResolvedValue([]);

    render(<MyMeetingsPage />);

    await waitFor(() => {
      expect(screen.getByText(/no meetings scheduled/i)).toBeInTheDocument();
    });
  });

  test("falls back to raw meeting datetime when date formatting throws", async () => {
    const originalToLocaleString = Date.prototype.toLocaleString;
    Date.prototype.toLocaleString = jest.fn(() => {
      throw new Error("format fail");
    });

    apiFetch.mockResolvedValue([
      {
        id: 2,
        staff_name: "Grace Hopper",
        staff_department: "Engineering",
        meeting_datetime: "RAW_DATE_VALUE",
        status: "accepted",
        description: "Office hour",
      },
    ]);

    render(<MyMeetingsPage />);

    await waitFor(() => {
      expect(screen.getByText(/RAW_DATE_VALUE/i)).toBeInTheDocument();
    });

    Date.prototype.toLocaleString = originalToLocaleString;
  });
});
