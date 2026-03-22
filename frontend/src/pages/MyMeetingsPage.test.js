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
});
