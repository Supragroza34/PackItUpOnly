  test("initials function edge cases", () => {
    const { initials } = require("./StaffMeetingRequestsPage");
    expect(initials("")).toBe("");
    expect(initials("A")).toBe("A");
    expect(initials("A B")).toBe("AB");
    expect(initials("A B C")).toBe("AB");
  });
  test("StatusBadge renders all statuses", () => {
    const { StatusBadge } = require("./StaffMeetingRequestsPage");
    ["pending", "accepted", "denied", "other"].forEach(status => {
      const { container } = render(<StatusBadge status={status} />);
      expect(container).toHaveTextContent(/pending|accepted|declined|other/i);
    });
  });
  test("accept/deny/add office hours error handling", async () => {
    apiFetch.mockResolvedValueOnce([{ id: 1, status: "pending" }]);
    apiFetch.mockRejectedValue(new Error("fail"));
    render(<StaffMeetingRequestsPage />);
    expect(await screen.findByText(/meeting requests/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /accept/i }));
    await waitFor(() => expect(screen.getByText(/fail/i)).toBeInTheDocument());
  });
import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import StaffMeetingRequestsPage from "./StaffMeetingRequestsPage";
import { apiFetch } from "../api";
import { useDispatch } from "react-redux";

const mockNavigate = jest.fn();
const mockDispatch = jest.fn(() => Promise.resolve());

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

jest.mock("react-redux", () => ({
  useDispatch: jest.fn(),
}));

jest.mock("../api", () => ({
  apiFetch: jest.fn(),
}));

jest.mock("../store/slices/authSlice", () => ({
  logout: jest.fn(() => ({ type: "auth/logout" })),
}));

jest.mock("../components/NotificationBell", () => ({ onNotificationClick }) => (
  <div>
    <button onClick={() => onNotificationClick({ meeting_request_id: 9 })}>Notification</button>
    <button onClick={() => onNotificationClick({ ticket_id: 22 })}>Ticket Notification</button>
  </div>
));

jest.mock("./WeeklyCalendar", () => ({ officeHours, acceptedMeetings }) => (
  <div>
    WeeklyCalendar {officeHours.length}/{acceptedMeetings.length}
  </div>
));

describe("StaffMeetingRequestsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useDispatch.mockReturnValue(mockDispatch);
    window.confirm = jest.fn(() => true);
  });

  test("loads requests/office hours and renders pending card", async () => {
    apiFetch
      .mockResolvedValueOnce([
        {
          id: 1,
          student_name: "John Doe",
          student_k_number: "K123",
          student_email: "john@kcl.ac.uk",
          meeting_datetime: "2026-03-25T10:00:00Z",
          description: "Need support",
          status: "pending",
        },
      ])
      .mockResolvedValueOnce([
        { id: 1, day_of_week: "Monday", start_time: "09:00:00", end_time: "11:00:00" },
      ]);

    render(<StaffMeetingRequestsPage />);

    expect(await screen.findByText(/meeting requests/i)).toBeInTheDocument();
    expect(await screen.findByText(/K123/i)).toBeInTheDocument();
    expect(screen.getByText(/weeklycalendar 1\/0/i)).toBeInTheDocument();
  });

  test("accept request updates status and calls endpoint", async () => {
    apiFetch
      .mockResolvedValueOnce([
        {
          id: 1,
          student_name: "John Doe",
          student_k_number: "K123",
          student_email: "john@kcl.ac.uk",
          meeting_datetime: "2026-03-25T10:00:00Z",
          description: "Need support",
          status: "pending",
        },
      ])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({ ok: true });

    render(<StaffMeetingRequestsPage />);

    expect(await screen.findByText(/john doe/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /accept/i }));

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        "/staff/dashboard/meeting-requests/1/accept/",
        { method: "POST" },
        { auth: true }
      );
    });
  });

  test("deny failure rolls back and shows error", async () => {
    apiFetch
      .mockResolvedValueOnce([
        {
          id: 1,
          student_name: "John Doe",
          student_k_number: "K123",
          student_email: "john@kcl.ac.uk",
          meeting_datetime: "2026-03-25T10:00:00Z",
          description: "Need support",
          status: "pending",
        },
      ])
      .mockResolvedValueOnce([])
      .mockRejectedValueOnce(new Error("deny failed"));

    render(<StaffMeetingRequestsPage />);

    expect(await screen.findByText(/john doe/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /decline/i }));

    expect(await screen.findByText(/deny failed/i)).toBeInTheDocument();
  });

  test("adds and deletes office hours", async () => {
    apiFetch
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        { id: 10, day_of_week: "Tuesday", start_time: "10:00:00", end_time: "12:00:00" },
      ])
      .mockResolvedValueOnce({ id: 11, day_of_week: "Monday", start_time: "09:00:00", end_time: "11:00:00" })
      .mockResolvedValueOnce({});

    render(<StaffMeetingRequestsPage />);

    expect(await screen.findByRole("heading", { name: "Office Hours" })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /add block/i }));
    expect(await screen.findByText(/office hours added/i)).toBeInTheDocument();

    fireEvent.click(screen.getAllByTitle(/delete block/i)[0]);

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        expect.stringMatching(/^\/staff\/office-hours\/\d+\/$/),
        { method: "DELETE" },
        { auth: true }
      );
    });
  });

  test("notification, dashboard nav, and logout handlers navigate", async () => {
    apiFetch.mockResolvedValueOnce([]).mockResolvedValueOnce([]);

    render(<StaffMeetingRequestsPage />);

    expect(await screen.findByText(/meeting requests/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /^notification$/i }));
    fireEvent.click(screen.getByRole("button", { name: /ticket notification/i }));
    fireEvent.click(screen.getByRole("button", { name: /dashboard/i }));
    fireEvent.click(screen.getByRole("button", { name: /log out/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/staff/dashboard/meeting-requests");
      expect(mockNavigate).toHaveBeenCalledWith("/staff/dashboard/22");
      expect(mockNavigate).toHaveBeenCalledWith("/staff/dashboard");
      expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
  });

  test("shows load error when initial fetch fails", async () => {
    apiFetch.mockRejectedValueOnce(new Error("load failed"));

    render(<StaffMeetingRequestsPage />);
    expect(await screen.findByText(/load failed/i)).toBeInTheDocument();
  });

  test("shows add office hours error", async () => {
    apiFetch
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockRejectedValueOnce(new Error("add failed"));

    render(<StaffMeetingRequestsPage />);
    expect(await screen.findByRole("button", { name: /add block/i })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /add block/i }));
    expect(await screen.findByText(/add failed/i)).toBeInTheDocument();
  });

  test("delete office hours cancel and failure branches", async () => {
    apiFetch
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([
        { id: 10, day_of_week: "Tuesday", start_time: "10:00:00", end_time: "12:00:00" },
      ])
      .mockRejectedValueOnce(new Error("delete failed"));

    window.confirm.mockReturnValueOnce(false);
    render(<StaffMeetingRequestsPage />);

    expect(await screen.findByRole("heading", { name: "Office Hours" })).toBeInTheDocument();
    fireEvent.click(screen.getAllByTitle(/delete block/i)[0]);
    expect(apiFetch).toHaveBeenCalledTimes(2);

    window.confirm.mockReturnValueOnce(true);
    fireEvent.click(screen.getAllByTitle(/delete block/i)[0]);
    expect(await screen.findByText(/delete failed/i)).toBeInTheDocument();
  });

  test("accept failure rolls back and shows error", async () => {
    apiFetch
      .mockResolvedValueOnce([
        {
          id: 7,
          student_name: "Eve Doe",
          student_k_number: "K777",
          student_email: "eve@kcl.ac.uk",
          meeting_datetime: "2026-04-01T10:00:00Z",
          description: "Need help",
          status: "pending",
        },
      ])
      .mockResolvedValueOnce([])
      .mockRejectedValueOnce(new Error("accept failed"));

    render(<StaffMeetingRequestsPage />);
    expect(await screen.findByText(/eve doe/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /accept/i }));

    expect(await screen.findByText(/accept failed/i)).toBeInTheDocument();
    expect(screen.getByText(/eve doe/i)).toBeInTheDocument();
  });

  test("switches tabs and shows empty accepted/declined states", async () => {
    apiFetch
      .mockResolvedValueOnce([
        {
          id: 1,
          student_name: "John Doe",
          student_k_number: "K123",
          student_email: "john@kcl.ac.uk",
          meeting_datetime: "2026-03-25T10:00:00Z",
          description: "Need support",
          status: "pending",
        },
      ])
      .mockResolvedValueOnce([]);

    render(<StaffMeetingRequestsPage />);
    expect(await screen.findByText(/john doe/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /accepted/i }));
    expect(await screen.findByText(/no accepted requests/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("tab", { name: /declined/i }));
    expect(await screen.findByText(/no declined requests/i)).toBeInTheDocument();
  });

  test("updates day/start/end inputs before adding office hours", async () => {
    apiFetch
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce({
        id: 12,
        day_of_week: "Friday",
        start_time: "11:30:00",
        end_time: "13:30:00",
      });

    render(<StaffMeetingRequestsPage />);
    expect(await screen.findByRole("button", { name: /add block/i })).toBeInTheDocument();

    fireEvent.change(screen.getByDisplayValue("Monday"), { target: { value: "Friday" } });

    const timeInputs = document.querySelectorAll('input[type="time"]');
    fireEvent.change(timeInputs[0], { target: { value: "11:30" } });
    fireEvent.change(timeInputs[1], { target: { value: "13:30" } });

    fireEvent.click(screen.getByRole("button", { name: /add block/i }));

    await waitFor(() => {
      expect(apiFetch).toHaveBeenCalledWith(
        "/staff/office-hours/",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            day_of_week: "Friday",
            start_time: "11:30",
            end_time: "13:30",
          }),
        }),
        { auth: true }
      );
    });
  });
});
