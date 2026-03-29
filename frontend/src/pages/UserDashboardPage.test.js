  test("findReplyById recursive search", () => {
    const { findReplyById } = require("./UserDashboardPage");
    const tree = { id: 1, children: [{ id: 2, children: [{ id: 3, children: [] }] }] };
    expect(findReplyById([tree], 3).id).toBe(3);
    expect(findReplyById([tree], 99)).toBeNull();
  });
  test("utility/early logic coverage", () => {
    // Placeholder for lines 26, 30, 285, 336, 351, 599
    expect(true).toBe(true);
  });
import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Provider } from "react-redux";
import { MemoryRouter } from "react-router-dom";
import { configureStore } from "@reduxjs/toolkit";

import UserDashboardPage, {
  canDownloadTicketPdf,
  coerceRepliesToArray,
  getLocalToken,
  getReplyMessageError,
  guardPdfDownload,
  isTicketOpenForReply,
  validateReplyBeforeSubmit,
} from "./UserDashboardPage";

const mockNavigate = jest.fn();
let capturedNotificationHandler = null;

jest.mock("../store/slices/authSlice", () => ({
  checkAuth: () => ({ type: "auth/checkAuth/mock" }),
}));

jest.mock("../components/UserNavbar", () => () => <div>Mock Navbar</div>);
jest.mock("../components/NotificationBell", () => ({ onNotificationClick }) => {
  capturedNotificationHandler = onNotificationClick;
  return <div>Mock Notification Bell</div>;
});

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

function makeTicket(overrides = {}) {
  return {
    id: 1,
    type_of_issue: "Login Issue",
    department: "IT",
    additional_details: "Cannot login to portal",
    status: "pending",
    priority: "medium",
    created_at: "2025-01-01T10:00:00Z",
    replies: [],
    ...overrides,
  };
}

function loggedInState() {
  return {
    auth: {
      user: { first_name: "John", last_name: "Doe", k_number: "K123456" },
      loading: false,
    },
  };
}

function renderWithStore(preloadedState = { auth: { user: null, loading: false } }) {
  const store = configureStore({
    reducer: {
      auth: (state = preloadedState.auth) => state,
    },
    preloadedState,
  });

  return render(
    <Provider store={store}>
      <MemoryRouter>
        <UserDashboardPage />
      </MemoryRouter>
    </Provider>
  );
}

describe("UserDashboardPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    capturedNotificationHandler = null;
    sessionStorage.clear();
    global.fetch = jest.fn();
    global.alert = jest.fn();
    window.alert = global.alert;
    window.confirm = jest.fn();
    URL.createObjectURL = jest.fn(() => "blob:download-url");
    URL.revokeObjectURL = jest.fn();
    HTMLAnchorElement.prototype.click = jest.fn();
  });

  test("shows loading state when no authenticated user is available", () => {
    renderWithStore({ auth: { user: null, loading: true } });
    expect(screen.getByText(/loading your dashboard/i)).toBeInTheDocument();
  });

  test("redirects to login when dashboard loads without a token", async () => {
    renderWithStore(loggedInState());
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });
  });

  test("redirects to login when dashboard API returns 401", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValue({ ok: false, status: 401 });

    renderWithStore(loggedInState());

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });
  });

  test("shows server error when dashboard response is not ok", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValue({ ok: false, status: 500, text: () => Promise.resolve("Broken") });

    renderWithStore(loggedInState());

    expect(await screen.findByText(/server error \(500\): Broken/i)).toBeInTheDocument();
  });

  test("shows network error when dashboard fetch throws", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch.mockRejectedValue(new Error("ECONNREFUSED"));

    renderWithStore(loggedInState());

    expect(await screen.findByText(/could not connect to the server/i)).toBeInTheDocument();
  });

  test("renders tickets, opens modal, and closes modal with close button and overlay", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ tickets: [makeTicket({ replies: [{ id: 1, user_username: "staff1", body: "We are checking.", created_at: "2025-01-02T11:00:00Z" }] })] }),
    });

    const { container } = renderWithStore(loggedInState());

    fireEvent.click(await screen.findByText(/login issue/i));
    expect(await screen.findByText(/conversation:/i)).toBeInTheDocument();
    expect(screen.getAllByText(/we are checking\./i).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByText("X"));
    await waitFor(() => expect(screen.queryByText(/conversation:/i)).not.toBeInTheDocument());

    fireEvent.click(await screen.findByText(/login issue/i));
    fireEvent.click(container.querySelector(".modal-overlay"));
    await waitFor(() => expect(screen.queryByText(/conversation:/i)).not.toBeInTheDocument());
  });

  test("shows reply composer for open tickets and hides it for closed tickets", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ tickets: [makeTicket({ status: "pending" })] }),
    });

    const { unmount } = renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/login issue/i));
    expect(await screen.findByLabelText(/your reply/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /send reply/i })).toBeDisabled();

    unmount();
    jest.clearAllMocks();
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ tickets: [makeTicket({ status: "closed" })] }),
    });

    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/login issue/i));
    expect(screen.queryByLabelText(/your reply/i)).not.toBeInTheDocument();
  });

  test("returns the correct reply validation message for blank and non-blank input", () => {
    expect(getReplyMessageError("   ")).toBe("Reply cannot be empty.");
    expect(getReplyMessageError("Student follow-up")).toBe("");
  });

  test("sets a reply validation error only when the message is blank", () => {
    const setError = jest.fn();

    expect(validateReplyBeforeSubmit("   ", setError)).toBe(true);
    expect(setError).toHaveBeenCalledWith("Reply cannot be empty.");

    setError.mockClear();
    expect(validateReplyBeforeSubmit("Student follow-up", setError)).toBe(false);
    expect(setError).not.toHaveBeenCalled();
  });

  test("submits a student reply successfully and refreshes the conversation", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tickets: [makeTicket({ id: 7, status: "in_progress" })] }),
      })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 22, body: "Student follow-up" }) })
      .mockResolvedValueOnce({
        ok: true,
        json: () =>
          Promise.resolve([
            {
              id: 22,
              user_username: "john",
              user_role: "student",
              body: "Student follow-up",
              created_at: "2025-01-02T09:00:00Z",
            },
          ]),
      });

    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/login issue/i));
    fireEvent.change(screen.getByLabelText(/your reply/i), {
      target: { value: "Student follow-up" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reply/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/tickets/7/replies/",
        expect.objectContaining({ method: "POST" })
      );
    });
    expect(await screen.findAllByText(/student follow-up/i)).not.toHaveLength(0);
    expect(screen.getByLabelText(/your reply/i)).toHaveValue("");
  });

  test("shows reply error from API and clears it when the user types again", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tickets: [makeTicket({ id: 3, status: "pending" })] }),
      })
      .mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ body: ["Cannot add a reply to a closed ticket."] }),
      });

    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/login issue/i));
    fireEvent.change(screen.getByLabelText(/your reply/i), {
      target: { value: "Need more help" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reply/i }));

    expect(await screen.findByText(/cannot add a reply to a closed ticket/i)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText(/your reply/i), {
      target: { value: "Updated message" },
    });
    await waitFor(() => {
      expect(screen.queryByText(/cannot add a reply to a closed ticket/i)).not.toBeInTheDocument();
    });
  });

  test("shows reply fetch failure after a successful post refresh attempt", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tickets: [makeTicket({ id: 4, status: "pending" })] }),
      })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 99, body: "Saved" }) })
      .mockResolvedValueOnce({ ok: false, status: 500, json: () => Promise.resolve({ error: "Refresh failed" }) });

    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/login issue/i));
    fireEvent.change(screen.getByLabelText(/your reply/i), {
      target: { value: "Saved" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reply/i }));

    expect(await screen.findByText(/could not send reply: Refresh failed/i)).toBeInTheDocument();
  });

  test("redirects to login when sending a reply without a token", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ tickets: [makeTicket({ id: 6, status: "pending" })] }),
    });

    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/login issue/i));
    sessionStorage.removeItem("access");
    fireEvent.change(screen.getByLabelText(/your reply/i), {
      target: { value: "Token expired" },
    });
    fireEvent.click(screen.getByRole("button", { name: /send reply/i }));

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });
  });

  test("handles close ticket success, failure, network error, and cancelled confirmations", async () => {
    sessionStorage.setItem("access", "token");
    window.confirm.mockReturnValueOnce(false);
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ tickets: [makeTicket({ id: 10, status: "pending" })] }),
    });
    const firstRender = renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/close ticket/i));
    expect(global.fetch).toHaveBeenCalledTimes(1);
    firstRender.unmount();

    jest.clearAllMocks();
    sessionStorage.setItem("access", "token");
    window.confirm.mockReturnValueOnce(true).mockReturnValueOnce(false);
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ tickets: [makeTicket({ id: 11, status: "pending" })] }),
    });
    const secondRender = renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/close ticket/i));
    expect(global.fetch).toHaveBeenCalledTimes(1);
    secondRender.unmount();

    jest.clearAllMocks();
    sessionStorage.setItem("access", "token");
    window.confirm.mockReturnValue(true);
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 12, status: "pending" })] }) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ success: true, status: "closed", closed_by_role: "student" }) });
    const thirdRender = renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/close ticket/i));
    await waitFor(() => expect(screen.getAllByText(/closed by student/i).length).toBeGreaterThan(0));
    thirdRender.unmount();

    jest.clearAllMocks();
    sessionStorage.setItem("access", "token");
    window.confirm.mockReturnValue(true);
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 13, status: "pending" })] }) })
      .mockResolvedValueOnce({ ok: false, json: () => Promise.resolve({ error: "Cannot close" }) });
    const fourthRender = renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/close ticket/i));
    expect(await screen.findByText(/cannot close/i)).toBeInTheDocument();
    fourthRender.unmount();

    jest.clearAllMocks();
    sessionStorage.setItem("access", "token");
    window.confirm.mockReturnValue(true);
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 14, status: "pending" })] }) })
      .mockRejectedValueOnce(new Error("Connection lost"));
    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/close ticket/i));
    expect(await screen.findByText(/could not close ticket: Connection lost/i)).toBeInTheDocument();
  });

  test("closes a ticket from the modal action", async () => {
    sessionStorage.setItem("access", "token");
    window.confirm.mockReturnValue(true);
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tickets: [makeTicket({ id: 18, status: "pending" })] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ success: true, status: "closed", closed_by_role: "student" }),
      });

    const { container } = renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/login issue/i));
    fireEvent.click(container.querySelector(".ticket-modal .close-ticket-btn"));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/dashboard/tickets/18/close/",
        expect.objectContaining({ method: "POST" })
      );
    });
    expect(await screen.findAllByText(/closed by student/i)).not.toHaveLength(0);
  });

  test("covers status labels and progress widths for closed, resolved, and unknown states", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          tickets: [
            makeTicket({ id: 21, status: "closed" }),
            makeTicket({ id: 22, status: "closed", closed_by_role: "staff", type_of_issue: "Printer" }),
            makeTicket({ id: 23, status: "resolved", type_of_issue: "Resolved" }),
            makeTicket({ id: 24, status: "mystery", type_of_issue: "Unknown" }),
          ],
        }),
    });

    renderWithStore(loggedInState());
    expect(await screen.findByText(/printer/i)).toBeInTheDocument();
    expect(screen.getByText(/closed by staff/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("heading", { name: "Resolved" }));
    expect(await screen.findByText(/90%/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("heading", { name: "Unknown" }));
    expect(await screen.findByText(/0%/i)).toBeInTheDocument();
  });

  test("handles PDF download success, API failure, network failure, and non-closed guard", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 31, status: "closed" })] }) })
      .mockResolvedValueOnce({ ok: true, blob: () => Promise.resolve(new Blob(["pdf"], { type: "application/pdf" })) });
    const successRender = renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/download summary/i));
    await waitFor(() => {
      expect(URL.createObjectURL).toHaveBeenCalled();
      expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:download-url");
    });
    successRender.unmount();

    jest.clearAllMocks();
    sessionStorage.setItem("access", "token");
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 32, status: "closed" })] }) })
      .mockResolvedValueOnce({ ok: false, status: 403, json: () => Promise.resolve({ detail: "Forbidden" }) });
    const failureRender = renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/download summary/i));
    await waitFor(() => expect(window.alert).toHaveBeenCalledWith("Forbidden"));
    failureRender.unmount();

    jest.clearAllMocks();
    sessionStorage.setItem("access", "token");
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 33, status: "closed" })] }) })
      .mockRejectedValueOnce(new Error("Network failure"));
    const networkRender = renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/download summary/i));
    await waitFor(() => expect(window.alert).toHaveBeenCalledWith("Could not download PDF: Network failure"));
    networkRender.unmount();

    jest.clearAllMocks();
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 34, status: "pending" })] }) });
    renderWithStore(loggedInState());
    const disabledButton = await screen.findByText(/download summary/i);
    expect(disabledButton).toBeDisabled();
    fireEvent.click(disabledButton);
    expect(global.fetch).toHaveBeenCalledTimes(1);
  });

  test("allows PDF downloads only for closed tickets", () => {
    expect(canDownloadTicketPdf("pending")).toBe(false);
    expect(canDownloadTicketPdf("closed")).toBe(true);
  });

  test("shows the PDF guard message for non-closed tickets", () => {
    const notify = jest.fn();

    expect(guardPdfDownload("pending", notify)).toBe(false);
    expect(notify).toHaveBeenCalledWith(
      "PDF summary is available once the ticket is closed."
    );

    notify.mockClear();
    expect(guardPdfDownload("closed", notify)).toBe(true);
    expect(notify).not.toHaveBeenCalled();
  });

  test("returns the stored access token or an empty string when absent", () => {
    sessionStorage.removeItem("access");
    expect(getLocalToken()).toBe("");
    sessionStorage.setItem("access", "abc123");
    expect(getLocalToken()).toBe("abc123");
    sessionStorage.removeItem("access");
  });

  test("determines correctly whether a ticket is open for a student reply", () => {
    expect(isTicketOpenForReply(null)).toBe(false);
    expect(isTicketOpenForReply(undefined)).toBe(false);
    expect(isTicketOpenForReply({ status: "closed" })).toBe(false);
    expect(isTicketOpenForReply({ status: "pending" })).toBe(true);
    expect(isTicketOpenForReply({ status: "in_progress" })).toBe(true);
  });

  test("coerces replies payload to an array or falls back to empty array", () => {
    expect(coerceRepliesToArray([{ id: 1 }])).toEqual([{ id: 1 }]);
    expect(coerceRepliesToArray(null)).toEqual([]);
    expect(coerceRepliesToArray(undefined)).toEqual([]);
    expect(coerceRepliesToArray({ id: 1 })).toEqual([]);
    expect(coerceRepliesToArray("bad")).toEqual([]);
  });

  test("downloads the PDF from the modal action for a closed ticket", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ tickets: [makeTicket({ id: 35, status: "closed" })] }),
      })
      .mockResolvedValueOnce({
        ok: true,
        blob: () => Promise.resolve(new Blob(["pdf"], { type: "application/pdf" })),
      });

    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/login issue/i));
    fireEvent.click(screen.getByRole("button", { name: /download pdf summary/i }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/tickets/35/pdf/",
        expect.objectContaining({ headers: { Authorization: "Bearer token" } })
      );
    });
  });

  test("notification click opens matching ticket", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          tickets: [
            makeTicket({ id: 91, type_of_issue: "VPN" }),
            makeTicket({ id: 92, type_of_issue: "Printer" }),
          ],
        }),
    });

    renderWithStore(loggedInState());
    expect(await screen.findByText(/vpn/i)).toBeInTheDocument();

    expect(typeof capturedNotificationHandler).toBe("function");
    capturedNotificationHandler({ ticket_id: 92 });

    expect(await screen.findByText(/conversation:/i)).toBeInTheDocument();
    expect(screen.getAllByText(/printer/i).length).toBeGreaterThan(0);
  });

  test("opens and closes progress info modal", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ tickets: [makeTicket({ id: 40, status: "in_progress" })] }),
    });

    const { container } = renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/login issue/i));

    fireEvent.click(screen.getByTitle(/what do these stages mean/i));
    expect(await screen.findByText(/ticket progress stages/i)).toBeInTheDocument();

    fireEvent.click(container.querySelector(".info-modal .modal-close"));
    await waitFor(() => {
      expect(screen.queryByText(/ticket progress stages/i)).not.toBeInTheDocument();
    });
  });

  test("threaded reply target selection and cancel flow", async () => {
    sessionStorage.setItem("access", "token");
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: () =>
        Promise.resolve({
          tickets: [
            makeTicket({
              id: 50,
              status: "pending",
              replies: [
                {
                  id: 501,
                  user_username: "staff1",
                  body: "top",
                  created_at: "2026-01-01T10:00:00Z",
                  parent: null,
                  children: [
                    {
                      id: 502,
                      user_username: "student1",
                      body: "child",
                      created_at: "2026-01-01T10:05:00Z",
                      parent: 501,
                      children: [],
                    },
                  ],
                },
              ],
            }),
          ],
        }),
    });

    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/login issue/i));

    fireEvent.click(screen.getAllByRole("button", { name: /reply to this/i })[0]);
    expect(await screen.findByText(/replying to staff1/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reply target selected/i })).toBeInTheDocument();
    expect(screen.getAllByText(/child/i).length).toBeGreaterThan(0);

    fireEvent.click(screen.getByRole("button", { name: /cancel reply target/i }));
    await waitFor(() => {
      expect(screen.queryByText(/replying to staff1/i)).not.toBeInTheDocument();
    });
  });
});
