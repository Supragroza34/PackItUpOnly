  test("handles slot fetch error and loading state", async () => {
    apiFetch.mockResolvedValueOnce(staff);
    apiFetch.mockRejectedValueOnce(new Error("Slot error"));
    render(<StaffMeetingPage />);
    expect(await screen.findByText("Alice Johnson")).toBeInTheDocument();
    const dateInput = document.querySelector('input[type="date"]');
    fireEvent.change(dateInput, { target: { value: "2026-03-25" } });
    expect(await screen.findByText("Slot error")).toBeInTheDocument();
  });
  test("renders staff details with missing fields", async () => {
    apiFetch.mockResolvedValueOnce({ ...staff, department: undefined, email: undefined, k_number: undefined });
    render(<StaffMeetingPage />);
    expect(await screen.findByText("—")).toBeInTheDocument();
  });
import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import StaffMeetingPage from "./StaffMeetingPage";
import { apiFetch } from "../api";

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: () => ({ id: "42" }),
}));

jest.mock("../api", () => ({
  apiFetch: jest.fn(),
}));

jest.mock("../components/UserNavbar", () => () => <div>Mock Navbar</div>);

describe("StaffMeetingPage", () => {
  const staff = {
    id: 42,
    first_name: "Alice",
    last_name: "Johnson",
    department: "IT",
    email: "alice@kcl.ac.uk",
    k_number: "K100",
    office_hours: [
      { day_of_week: "Friday", start_time: "10:00:00", end_time: "12:00:00" },
      { day_of_week: "Monday", start_time: "09:00:00", end_time: "11:00:00" },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders staff details and office hours", async () => {
    apiFetch.mockResolvedValueOnce(staff);

    render(<StaffMeetingPage />);

    expect(await screen.findByText("Alice Johnson")).toBeInTheDocument();
    expect(screen.getByText(/department:/i)).toBeInTheDocument();
    expect(screen.getByText(/email:/i)).toBeInTheDocument();
    expect(screen.getByText(/monday: 09:00/i)).toBeInTheDocument();
    expect(screen.getByText(/friday: 10:00/i)).toBeInTheDocument();
  });

  test("shows staff load error", async () => {
    apiFetch.mockRejectedValueOnce(new Error("Not found"));

    render(<StaffMeetingPage />);

    expect(await screen.findByText("Not found")).toBeInTheDocument();
  });

  test("shows fallback when staff payload is null", async () => {
    apiFetch.mockResolvedValueOnce(null);
    render(<StaffMeetingPage />);
    expect(await screen.findByText(/not found/i)).toBeInTheDocument();
  });

  test("shows no office hours message when office_hours is empty", async () => {
    apiFetch.mockResolvedValueOnce({ ...staff, office_hours: [] });
    render(<StaffMeetingPage />);
    expect(await screen.findByText(/no office hours set/i)).toBeInTheDocument();
  });

  test("loads slots, submits meeting request successfully, and clears form", async () => {
    apiFetch
      .mockResolvedValueOnce(staff)
      .mockResolvedValueOnce({ slots: ["2026-03-25T09:00:00Z", "2026-03-25T09:15:00Z"] })
      .mockResolvedValueOnce({ id: 1 });

    render(<StaffMeetingPage />);

    expect(await screen.findByText("Alice Johnson")).toBeInTheDocument();

    const dateInput = document.querySelector('input[type="date"]');
    fireEvent.change(dateInput, { target: { value: "2026-03-25" } });

    expect(await screen.findByRole("button", { name: /09:00/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /09:00/i }));

    fireEvent.change(screen.getByPlaceholderText(/describe what you want to meet about/i), {
      target: { value: "Need help with assignment" },
    });

    fireEvent.click(screen.getByRole("button", { name: /send meeting request/i }));

    expect(await screen.findByText(/meeting request submitted successfully/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/describe what you want to meet about/i)).toHaveValue("");

    expect(apiFetch).toHaveBeenCalledWith(
      "/meeting-requests/",
      expect.objectContaining({ method: "POST" }),
      { auth: true }
    );
  });

  test("requires slot before submit and handles slot fetch failure", async () => {
    apiFetch
      .mockResolvedValueOnce(staff)
      .mockRejectedValueOnce(new Error("Slots failed"));

    render(<StaffMeetingPage />);

    expect(await screen.findByText("Alice Johnson")).toBeInTheDocument();

    const dateInput = document.querySelector('input[type="date"]');
    fireEvent.change(dateInput, { target: { value: "2026-03-25" } });
    expect(await screen.findByText("Slots failed")).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/describe what you want to meet about/i), { target: { value: "Hi" } });
    const submitBtn = screen.getByRole("button", { name: /send meeting request/i });
    expect(submitBtn).toBeDisabled();
    fireEvent.click(submitBtn);

    expect(apiFetch).not.toHaveBeenCalledWith(
      "/meeting-requests/",
      expect.anything(),
      expect.anything()
    );
  });

  test("handles submit failure after slot selection", async () => {
    apiFetch
      .mockResolvedValueOnce(staff)
      .mockResolvedValueOnce({ slots: ["2026-03-25T09:00:00Z"] })
      .mockRejectedValueOnce(new Error("Submit failed"));

    render(<StaffMeetingPage />);
    expect(await screen.findByText("Alice Johnson")).toBeInTheDocument();

    const dateInput = document.querySelector('input[type="date"]');
    fireEvent.change(dateInput, { target: { value: "2026-03-25" } });
    fireEvent.click(await screen.findByRole("button", { name: /09:00/i }));
    fireEvent.change(screen.getByPlaceholderText(/describe what you want to meet about/i), { target: { value: "Need help" } });
    fireEvent.click(screen.getByRole("button", { name: /send meeting request/i }));

    expect(await screen.findByText(/submit failed/i)).toBeInTheDocument();
  });

  test("shows slot-required validation when submitting without selecting a slot", async () => {
    apiFetch
      .mockResolvedValueOnce(staff)
      .mockResolvedValueOnce({ slots: ["2026-03-25T09:00:00Z"] });

    render(<StaffMeetingPage />);
    expect(await screen.findByText("Alice Johnson")).toBeInTheDocument();

    const dateInput = document.querySelector('input[type="date"]');
    fireEvent.change(dateInput, { target: { value: "2026-03-25" } });
    expect(await screen.findByRole("button", { name: /09:00/i })).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/describe what you want to meet about/i), {
      target: { value: "Need advice" },
    });

    const form = document.querySelector("form");
    fireEvent.submit(form);

    expect(await screen.findByText(/please select a time slot/i)).toBeInTheDocument();
  });
});
