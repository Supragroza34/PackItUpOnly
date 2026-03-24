import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import TicketPage from "./TicketPage";

const mockNavigate = jest.fn();
const mockDispatch = jest.fn();
let mockState = {
  auth: { user: { id: 1, role: "staff" } },
  staff: { staffList: [{ id: 2, first_name: "Alex", last_name: "Kim", ticket_count: 3 }] },
};

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: () => ({ ticket_id: "9" }),
  useNavigate: () => mockNavigate,
}));

jest.mock("react-redux", () => ({
  useDispatch: () => mockDispatch,
  useSelector: (sel) => sel(mockState),
}));

jest.mock("../store/slices/staffSlice", () => ({
  fetchStaffList: jest.fn(() => ({ type: "staff/fetch" })),
  reassignTicket: jest.fn((payload) => ({ type: "staff/reassign", payload })),
}));

jest.mock("../store/slices/authSlice", () => ({
  checkAuth: jest.fn(() => ({ type: "auth/check" })),
}));

jest.mock("../context/AuthContext", () => ({
  useAuth: () => ({ user: { id: 1, role: "staff" } }),
}));

jest.mock("../components/HtmlContent", () => ({
  HtmlContent: ({ html }) => <div>{html}</div>,
}));

function ticketPayload(overrides = {}) {
  return {
    id: 9,
    type_of_issue: "Login Issue",
    status: "pending",
    priority: "medium",
    department: "IT",
    additional_details: "Cannot sign in",
    user: { first_name: "John", last_name: "Doe", email: "john@kcl.ac.uk" },
    replies: [],
    created_at: "2026-03-01T10:00:00Z",
    updated_at: "2026-03-01T10:00:00Z",
    assigned_to: null,
    ...overrides,
  };
}

describe("TicketPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.setItem("access", "token");
    global.fetch = jest.fn();
    window.confirm = jest.fn(() => true);
    window.alert = jest.fn();
    mockDispatch.mockReturnValue({
      unwrap: () => Promise.resolve({}),
      then: (cb) => cb && cb(),
    });
  });

  test("renders loading state before ticket loads", () => {
    global.fetch.mockReturnValue(new Promise(() => {}));
    render(<TicketPage />);
    expect(screen.getByText(/loading ticket/i)).toBeInTheDocument();
  });

  test("redirects on 401 during fetch", async () => {
    global.fetch.mockResolvedValueOnce({ status: 401, json: () => Promise.resolve({}) });
    render(<TicketPage />);
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login");
    });
  });

  test("shows not found state when ticket has no id", async () => {
    global.fetch.mockResolvedValueOnce({ status: 200, json: () => Promise.resolve({}) });
    render(<TicketPage />);
    expect(await screen.findByText(/ticket not found/i)).toBeInTheDocument();
  });

  test("renders ticket details and reply fallback", async () => {
    global.fetch.mockResolvedValueOnce({ status: 200, json: () => Promise.resolve(ticketPayload({ additional_details: "" })) });
    render(<TicketPage />);

    expect(await screen.findByText(/ticket #9/i)).toBeInTheDocument();
    expect(screen.getByText(/no description provided/i)).toBeInTheDocument();
    expect(screen.getByText(/no replies yet/i)).toBeInTheDocument();
  });

  test("changes status and navigates when reported", async () => {
    global.fetch
      .mockResolvedValueOnce({ status: 200, json: () => Promise.resolve(ticketPayload()) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(ticketPayload({ status: "reported" })) });

    render(<TicketPage />);
    expect(await screen.findByText(/ticket #9/i)).toBeInTheDocument();

    fireEvent.change(screen.getByDisplayValue("Pending"), { target: { value: "reported" } });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/staff/dashboard");
    });
  });

  test("close ticket confirmation flow and patch call", async () => {
    global.fetch
      .mockResolvedValueOnce({ status: 200, json: () => Promise.resolve(ticketPayload()) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve(ticketPayload({ status: "closed" })) });

    render(<TicketPage />);
    expect(await screen.findByText(/ticket #9/i)).toBeInTheDocument();

    window.confirm.mockReturnValueOnce(false);
    fireEvent.click(screen.getByRole("button", { name: /close ticket/i }));
    expect(global.fetch).toHaveBeenCalledTimes(1);

    window.confirm.mockReturnValueOnce(true).mockReturnValueOnce(true);
    fireEvent.click(screen.getByRole("button", { name: /close ticket/i }));
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/staff/dashboard/9/update/",
        expect.objectContaining({ method: "PATCH" })
      );
    });
  });

  test("submits reply and refreshes ticket data", async () => {
    global.fetch
      .mockResolvedValueOnce({ status: 200, json: () => Promise.resolve(ticketPayload()) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 1 }) })
      .mockResolvedValueOnce({ status: 200, json: () => Promise.resolve(ticketPayload({ replies: [{ id: 5, user_username: "staff", body: "ok" }] })) });

    render(<TicketPage />);
    expect(await screen.findByText(/ticket #9/i)).toBeInTheDocument();

    fireEvent.change(screen.getByPlaceholderText(/write a reply/i), { target: { value: "Hello" } });
    fireEvent.click(screen.getByRole("button", { name: /send reply/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "/api/replies/create/",
        expect.objectContaining({ method: "POST" })
      );
    });
    expect(await screen.findByText(/ok/i)).toBeInTheDocument();
  });

  test("supports nested reply target cancel", async () => {
    global.fetch.mockResolvedValueOnce({
      status: 200,
      json: () =>
        Promise.resolve(
          ticketPayload({
            replies: [
              { id: 50, user_username: "staff", body: "top", children: [{ id: 51, user_username: "student", body: "child", children: [] }] },
            ],
          })
        ),
    });

    render(<TicketPage />);
    expect(await screen.findByText(/ticket #9/i)).toBeInTheDocument();

    fireEvent.click(screen.getAllByRole("button", { name: /^reply$/i })[0]);
    expect(screen.getByText(/replying to comment #50/i)).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByText(/replying to comment/i)).not.toBeInTheDocument();
  });

  test("reassigns ticket and handles failure", async () => {
    const { reassignTicket } = require("../store/slices/staffSlice");
    global.fetch.mockResolvedValueOnce({ status: 200, json: () => Promise.resolve(ticketPayload()) });

    mockDispatch
      .mockReturnValueOnce({ unwrap: () => Promise.resolve({}) })
      .mockReturnValueOnce({ unwrap: () => Promise.reject("bad") });

    const { container } = render(<TicketPage />);
    expect(await screen.findByText(/ticket #9/i)).toBeInTheDocument();

    const assignSelect = container.querySelector(".assign-select");
    expect(assignSelect).toBeInTheDocument();

    fireEvent.change(assignSelect, { target: { value: "2" } });
    await waitFor(() => {
      expect(reassignTicket).toHaveBeenCalledWith({ ticketId: 9, updates: { assigned_to: 2 } });
    });

    fireEvent.change(assignSelect, { target: { value: "" } });
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith(expect.stringContaining("Failed to redirect ticket"));
    });
  });
});
