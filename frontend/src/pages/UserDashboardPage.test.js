import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { Provider } from "react-redux";
import { MemoryRouter } from "react-router-dom";
import { configureStore } from "@reduxjs/toolkit";

import UserDashboardPage from "./UserDashboardPage";

// Mock AuthContext
jest.mock("../context/AuthContext", () => ({
  useAuth: () => ({ logout: jest.fn() }),
}));

// Mock react-router navigate
const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

function renderWithStore(preloadedState) {
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
    localStorage.clear();
  });

  test("shows loading state when no user", () => {
    const preloadedState = { auth: { user: null, loading: true } };
    renderWithStore(preloadedState);
    expect(screen.getByText(/loading your dashboard/i)).toBeInTheDocument();
  });

  test("redirects to login if no token", async () => {
    const preloadedState = { auth: { user: { first_name: "John", last_name: "Doe" }, loading: false } };
    renderWithStore(preloadedState);

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });
  });

  test("renders tickets after successful fetch", async () => {
    localStorage.setItem("access", "fake-token");

    const tickets = [
      {
        id: 1,
        type_of_issue: "Login issue",
        department: "IT",
        additional_details: "Cannot login",
        status: "pending",
        priority: "high",
        created_at: "2025-01-01T10:00:00Z",
        replies: [],
      },
    ];

    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets }) })
    );

    const preloadedState = { auth: { user: { first_name: "John", last_name: "Doe" }, loading: false } };
    renderWithStore(preloadedState);

    expect(await screen.findByText(/login issue/i)).toBeInTheDocument();
    expect(screen.getByText(/it/i)).toBeInTheDocument();
    expect(screen.getByText(/cannot login/i)).toBeInTheDocument();
  });

  test("shows empty state when no tickets", async () => {
    localStorage.setItem("access", "fake-token");

    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets: [] }) })
    );

    const preloadedState = { auth: { user: { first_name: "Jane", last_name: "Smith" }, loading: false } };
    renderWithStore(preloadedState);

    expect(await screen.findByText(/you haven't submitted any tickets/i)).toBeInTheDocument();
  });

  test("opens and closes ticket modal", async () => {
    localStorage.setItem("access", "fake-token");

    const tickets = [
      {
        id: 2,
        type_of_issue: "Email problem",
        department: "Support",
        additional_details: "Emails not sending",
        status: "in_progress",
        priority: "medium",
        created_at: "2025-01-02T12:00:00Z",
        replies: [],
      },
    ];

    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets }) })
    );

    const preloadedState = { auth: { user: { first_name: "Sam", last_name: "Lee" }, loading: false } };
    renderWithStore(preloadedState);

    const ticketItem = await screen.findByText(/email problem/i);
    fireEvent.click(ticketItem);

    expect(screen.getByText(/responses from staff/i)).toBeInTheDocument();

    fireEvent.click(screen.getByText("X"));
    await waitFor(() => {
      expect(screen.queryByText(/responses from staff/i)).not.toBeInTheDocument();
    });
  });

  test("handles server error", async () => {
    localStorage.setItem("access", "fake-token");

    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: false, status: 500, text: () => Promise.resolve("Error") })
    );

    const preloadedState = { auth: { user: { first_name: "Alex", last_name: "Ray" }, loading: false } };
    renderWithStore(preloadedState);

    expect(await screen.findByText(/server error/i)).toBeInTheDocument();
  });

  test("navigates to FAQs and Create Ticket pages", () => {
    const preloadedState = { auth: { user: { first_name: "John", last_name: "Doe" }, loading: false } };
    renderWithStore(preloadedState);

    // FAQs link
    const faqsLink = screen.getByText(/view faqs/i);
    expect(faqsLink).toBeInTheDocument();
    expect(faqsLink.getAttribute("href")).toBe("/faqs");

    // Create ticket link
    const createLink = screen.getByText(/create new ticket/i);
    expect(createLink).toBeInTheDocument();
    expect(createLink.getAttribute("href")).toBe("/create-ticket");
  });
});

// ─── Shared helpers for PDF feature tests ────────────────────────────────────

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
  return { auth: { user: { first_name: "John", last_name: "Doe" }, loading: false } };
}

function mockFetch(tickets, pdfOk = true, pdfDetail = null) {
  global.fetch = jest.fn((url) => {
    if (url.includes("/dashboard/"))
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets }) });
    if (pdfOk) {
      const blob = new Blob(["PDF"], { type: "application/pdf" });
      return Promise.resolve({ ok: true, blob: () => Promise.resolve(blob) });
    }
    return Promise.resolve({
      ok: false,
      status: 403,
      json: () => Promise.resolve({ detail: pdfDetail || "Forbidden" }),
    });
  });
}

// ─── PDF feature: download button visibility ─────────────────────────────────

describe("PDF feature — download button visibility", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    localStorage.setItem("access", "test-token");
    URL.createObjectURL = jest.fn(() => "blob:fake-url");
    URL.revokeObjectURL = jest.fn();
    window.alert = jest.fn();
  });

  test("renders a download button for every ticket in the list", async () => {
    const tickets = [makeTicket({ id: 1 }), makeTicket({ id: 2, status: "closed" })];
    mockFetch(tickets);
    renderWithStore(loggedInState());
    const buttons = await screen.findAllByText(/Download Summary/i);
    expect(buttons).toHaveLength(2);
  });

  test("download button is disabled for a pending ticket", async () => {
    mockFetch([makeTicket({ status: "pending" })]);
    renderWithStore(loggedInState());
    const btn = await screen.findByText(/Download Summary/i);
    expect(btn).toBeDisabled();
  });

  test("download button is disabled for an in_progress ticket", async () => {
    mockFetch([makeTicket({ status: "in_progress" })]);
    renderWithStore(loggedInState());
    const btn = await screen.findByText(/Download Summary/i);
    expect(btn).toBeDisabled();
  });

  test("download button is disabled for a resolved ticket", async () => {
    mockFetch([makeTicket({ status: "resolved" })]);
    renderWithStore(loggedInState());
    const btn = await screen.findByText(/Download Summary/i);
    expect(btn).toBeDisabled();
  });

  test("download button is enabled for a closed ticket", async () => {
    mockFetch([makeTicket({ status: "closed" })]);
    renderWithStore(loggedInState());
    const btn = await screen.findByText(/Download Summary/i);
    expect(btn).not.toBeDisabled();
  });

  test("disabled button carries 'available once closed' tooltip", async () => {
    mockFetch([makeTicket({ status: "pending" })]);
    renderWithStore(loggedInState());
    const btn = await screen.findByText(/Download Summary/i);
    expect(btn).toHaveAttribute("title", "Available once the ticket is closed");
  });

  test("enabled button carries 'download pdf summary' tooltip", async () => {
    mockFetch([makeTicket({ status: "closed" })]);
    renderWithStore(loggedInState());
    const btn = await screen.findByText(/Download Summary/i);
    expect(btn).toHaveAttribute("title", "Download PDF summary");
  });
});

// ─── PDF feature: modal download button ──────────────────────────────────────

describe("PDF feature — modal download button", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    localStorage.setItem("access", "test-token");
    URL.createObjectURL = jest.fn(() => "blob:fake-url");
    URL.revokeObjectURL = jest.fn();
    window.alert = jest.fn();
  });

  async function openModal(ticket) {
    mockFetch([ticket]);
    renderWithStore(loggedInState());
    const item = await screen.findByText(ticket.type_of_issue);
    fireEvent.click(item);
    await screen.findByText(/Responses From Staff/i);
  }

  test("modal download button is disabled for a non-closed ticket", async () => {
    await openModal(makeTicket({ status: "in_progress" }));
    const btn = screen.getByText(/Download PDF Summary/i);
    expect(btn).toBeDisabled();
  });

  test("modal download button is enabled for a closed ticket", async () => {
    await openModal(makeTicket({ status: "closed" }));
    const btn = screen.getByText(/Download PDF Summary/i);
    expect(btn).not.toBeDisabled();
  });

  test("modal disabled button carries 'available once closed' tooltip", async () => {
    await openModal(makeTicket({ status: "pending" }));
    const btn = screen.getByText(/Download PDF Summary/i);
    expect(btn).toHaveAttribute("title", "Available once the ticket is closed");
  });

  test("modal enabled button carries 'download pdf summary' tooltip", async () => {
    await openModal(makeTicket({ status: "closed" }));
    const btn = screen.getByText(/Download PDF Summary/i);
    expect(btn).toHaveAttribute("title", "Download PDF summary");
  });
});

// ─── PDF feature: handleDownloadPdf logic ────────────────────────────────────

describe("PDF feature — handleDownloadPdf", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    localStorage.setItem("access", "test-token");
    URL.createObjectURL = jest.fn(() => "blob:fake-url");
    URL.revokeObjectURL = jest.fn();
    window.alert = jest.fn();
  });

  async function clickDownload(ticket) {
    mockFetch([ticket]);
    renderWithStore(loggedInState());
    const btn = await screen.findByText(/Download Summary/i);
    fireEvent.click(btn);
  }

  test("calls fetch with correct PDF URL and Authorization header", async () => {
    await clickDownload(makeTicket({ id: 5, status: "closed" }));
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        "http://localhost:8000/api/tickets/5/pdf/",
        expect.objectContaining({
          headers: expect.objectContaining({ Authorization: "Bearer test-token" }),
        })
      );
    });
  });

  test("calls createObjectURL and revokeObjectURL on a successful download", async () => {
    await clickDownload(makeTicket({ id: 5, status: "closed" }));
    await waitFor(() => {
      expect(URL.createObjectURL).toHaveBeenCalled();
      expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:fake-url");
    });
  });

  test("shows alert with server error detail when response is not ok", async () => {
    mockFetch([makeTicket({ id: 5, status: "closed" })], false, "Ticket is not closed.");
    renderWithStore(loggedInState());
    const btn = await screen.findByText(/Download Summary/i);
    fireEvent.click(btn);
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith("Ticket is not closed.");
    });
  });

  test("shows fallback alert when failed response has no JSON detail", async () => {
    global.fetch = jest.fn((url) => {
      if (url.includes("/dashboard/"))
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 5, status: "closed" })] }) });
      return Promise.resolve({ ok: false, status: 403, json: () => Promise.reject(new Error("no json")) });
    });
    renderWithStore(loggedInState());
    const btn = await screen.findByText(/Download Summary/i);
    fireEvent.click(btn);
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith("Could not download PDF (403)");
    });
  });

  test("shows alert with error message on a network failure", async () => {
    global.fetch = jest.fn((url) => {
      if (url.includes("/dashboard/"))
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 5, status: "closed" })] }) });
      return Promise.reject(new Error("Network failure"));
    });
    renderWithStore(loggedInState());
    const btn = await screen.findByText(/Download Summary/i);
    fireEvent.click(btn);
    await waitFor(() => {
      expect(window.alert).toHaveBeenCalledWith("Could not download PDF: Network failure");
    });
  });
});

// ─── Additional coverage: close ticket, replies, error paths ─────────────────

describe("UserDashboardPage — close ticket and remaining coverage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    localStorage.setItem("access", "test-token");
    URL.createObjectURL = jest.fn(() => "blob:fake-url");
    URL.revokeObjectURL = jest.fn();
    window.alert = jest.fn();
    window.confirm = jest.fn();
  });

  test("redirects to login on a 401 response from dashboard", async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({ ok: false, status: 401, text: () => Promise.resolve("Unauthorized") })
    );
    renderWithStore(loggedInState());
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true });
    });
  });

  test("shows connect error when dashboard fetch throws a network error", async () => {
    global.fetch = jest.fn(() => Promise.reject(new Error("ECONNREFUSED")));
    renderWithStore(loggedInState());
    expect(await screen.findByText(/could not connect to the server/i)).toBeInTheDocument();
  });

  test("modal renders staff replies when the ticket has replies", async () => {
    const reply = { id: 10, user_username: "janedee", body: "Please reset your password.", created_at: "2025-01-02T10:00:00Z" };
    const ticket = makeTicket({ status: "in_progress", replies: [reply] });
    mockFetch([ticket]);
    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/Login Issue/i));
    const replyBodies = await screen.findAllByText(/Please reset your password/i);
    expect(replyBodies.length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("janedee").length).toBeGreaterThanOrEqual(1);
  });

  test("close ticket button is not rendered for a closed ticket", async () => {
    mockFetch([makeTicket({ status: "closed" })]);
    renderWithStore(loggedInState());
    await screen.findByText(/Download Summary/i);
    expect(screen.queryByText(/Close ticket/i)).not.toBeInTheDocument();
  });

  test("cancelling the first confirm prevents the close endpoint being called", async () => {
    window.confirm = jest.fn(() => false);
    mockFetch([makeTicket({ status: "pending" })]);
    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/Close ticket/i));
    const urls = global.fetch.mock.calls.map((c) => c[0]);
    expect(urls.every((u) => !u.includes("/close/"))).toBe(true);
  });

  test("cancelling the second confirm prevents the close endpoint being called", async () => {
    window.confirm = jest.fn().mockReturnValueOnce(true).mockReturnValueOnce(false);
    mockFetch([makeTicket({ status: "pending" })]);
    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/Close ticket/i));
    const urls = global.fetch.mock.calls.map((c) => c[0]);
    expect(urls.every((u) => !u.includes("/close/"))).toBe(true);
  });

  test("successful close ticket enables the download button", async () => {
    window.confirm = jest.fn(() => true);
    global.fetch = jest.fn((url) => {
      if (url.includes("/dashboard/") && !url.includes("/close/"))
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 1, status: "pending" })] }) });
      return Promise.resolve({ ok: true, json: () => Promise.resolve({ success: true, status: "closed", closed_by_role: "student" }) });
    });
    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/Close ticket/i));
    await waitFor(() => expect(screen.getByText(/Download Summary/i)).not.toBeDisabled());
  });

  test("failed close ticket response shows the server error message", async () => {
    window.confirm = jest.fn(() => true);
    global.fetch = jest.fn((url) => {
      if (url.includes("/dashboard/") && !url.includes("/close/"))
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 1, status: "pending" })] }) });
      return Promise.resolve({ ok: false, json: () => Promise.resolve({ error: "Cannot close this ticket" }) });
    });
    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/Close ticket/i));
    await waitFor(() => expect(screen.getByText(/Cannot close this ticket/i)).toBeInTheDocument());
  });

  test("close ticket network error shows the connection error message", async () => {
    window.confirm = jest.fn(() => true);
    global.fetch = jest.fn((url) => {
      if (url.includes("/dashboard/") && !url.includes("/close/"))
        return Promise.resolve({ ok: true, json: () => Promise.resolve({ tickets: [makeTicket({ id: 1, status: "pending" })] }) });
      return Promise.reject(new Error("Connection lost"));
    });
    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/Close ticket/i));
    await waitFor(() => expect(screen.getByText(/Could not close ticket: Connection lost/i)).toBeInTheDocument());
  });

  test("getStatusLabel shows closed_by_role when ticket is closed with a role", async () => {
    mockFetch([makeTicket({ status: "closed", closed_by_role: "staff" })]);
    renderWithStore(loggedInState());
    expect(await screen.findByText(/Closed by Staff/i)).toBeInTheDocument();
  });

  test("getProgressWidth covers resolved and default cases via modal", async () => {
    mockFetch([makeTicket({ status: "resolved" })]);
    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/Login Issue/i));
    expect(await screen.findByText(/90%/i)).toBeInTheDocument();
  });

  test("clicking the modal overlay closes the modal", async () => {
    mockFetch([makeTicket({ status: "pending" })]);
    renderWithStore(loggedInState());
    fireEvent.click(await screen.findByText(/Login Issue/i));
    await screen.findByText(/Responses From Staff/i);
    fireEvent.click(document.querySelector(".modal-overlay"));
    await waitFor(() => expect(screen.queryByText(/Responses From Staff/i)).not.toBeInTheDocument());
  });
});
