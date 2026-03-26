import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
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

jest.mock("../components/RichTextEditor", () => {
  return function MockRichTextEditor({ id, value, onChange, disabled }) {
    return (
      <textarea
        id={id}
        data-testid="mock-rich-text-editor"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
      />
    );
  };
});

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

  test("shows additional details validation error when editor HTML has no plain text", async () => {
    renderWithRouter(<TicketFormPage />);

    await userEvent.selectOptions(screen.getByLabelText(/^Department$/i), "Informatics");
    await userEvent.selectOptions(
      screen.getByLabelText(/^Type of Issue$/i),
      "Software Installation Issues"
    );
    await userEvent.type(screen.getByTestId("mock-rich-text-editor"), "<p><br></p>");

    await userEvent.click(screen.getByRole("button", { name: /Submit Ticket/i }));

    expect(await screen.findByText(/Additional details are required/i)).toBeInTheDocument();
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
    await userEvent.type(screen.getByTestId("mock-rich-text-editor"), "<p><strong>Cannot install IDE</strong></p>");

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

  test("shows server validation errors from backend payload", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ errors: { department: "Bad department" } }),
    });

    renderWithRouter(<TicketFormPage />);
    await userEvent.selectOptions(screen.getByLabelText(/^Department$/i), "Informatics");
    await userEvent.selectOptions(
      screen.getByLabelText(/^Type of Issue$/i),
      "Software Installation Issues"
    );
    await userEvent.type(screen.getByTestId("mock-rich-text-editor"), "Valid text");
    await userEvent.click(screen.getByRole("button", { name: /Submit Ticket/i }));

    expect(await screen.findByText(/Bad department/i)).toBeInTheDocument();
  });

  test("shows generic error when backend responds without errors object", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: "Nope" }),
    });

    renderWithRouter(<TicketFormPage />);
    await userEvent.selectOptions(screen.getByLabelText(/^Department$/i), "Informatics");
    await userEvent.selectOptions(
      screen.getByLabelText(/^Type of Issue$/i),
      "Software Installation Issues"
    );
    await userEvent.type(screen.getByTestId("mock-rich-text-editor"), "Valid text");
    await userEvent.click(screen.getByRole("button", { name: /Submit Ticket/i }));

    expect(await screen.findByText(/something went wrong/i)).toBeInTheDocument();
  });

  test("shows connection error when submit throws", async () => {
    global.fetch = jest.fn().mockRejectedValue(new Error("offline"));

    renderWithRouter(<TicketFormPage />);
    await userEvent.selectOptions(screen.getByLabelText(/^Department$/i), "Informatics");
    await userEvent.selectOptions(
      screen.getByLabelText(/^Type of Issue$/i),
      "Software Installation Issues"
    );
    await userEvent.type(screen.getByTestId("mock-rich-text-editor"), "Valid text");
    await userEvent.click(screen.getByRole("button", { name: /Submit Ticket/i }));

    expect(await screen.findByText(/could not reach the server/i)).toBeInTheDocument();
  });

  test("handles attachments: rejects oversized and allows remove", async () => {
    renderWithRouter(<TicketFormPage />);

    const fileInput = document.querySelector('input[type="file"]');
    const smallFile = new File(["ok"], "note.txt", { type: "text/plain" });
    const bigContent = new Uint8Array(10 * 1024 * 1024 + 1);
    const bigFile = new File([bigContent], "huge.txt", { type: "text/plain" });

    await userEvent.upload(fileInput, [smallFile, bigFile]);

    expect(await screen.findByText(/exceeds the 10 MB limit/i)).toBeInTheDocument();
    expect(screen.getByText("note.txt")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /remove note.txt/i }));
    expect(screen.queryByText("note.txt")).not.toBeInTheDocument();
  });

  test("does not add duplicate attachments", async () => {
    renderWithRouter(<TicketFormPage />);

    const fileInput = document.querySelector('input[type="file"]');
    const file = new File(["same"], "dup.txt", { type: "text/plain" });

    await userEvent.upload(fileInput, [file]);
    await userEvent.upload(fileInput, [file]);

    expect(screen.getByText("dup.txt")).toBeInTheDocument();
    expect(screen.getAllByText("dup.txt")).toHaveLength(1);
  });

  test("clears previous attachment error when subsequent upload is valid", async () => {
    renderWithRouter(<TicketFormPage />);

    const fileInput = document.querySelector('input[type="file"]');
    const bigContent = new Uint8Array(10 * 1024 * 1024 + 1);
    const bigFile = new File([bigContent], "huge.txt", { type: "text/plain" });
    const okFile = new File(["ok"], "fine.txt", { type: "text/plain" });

    await userEvent.upload(fileInput, [bigFile]);
    expect(await screen.findByText(/exceeds the 10 MB limit/i)).toBeInTheDocument();

    await userEvent.upload(fileInput, [okFile]);
    expect(screen.queryByText(/exceeds the 10 MB limit/i)).not.toBeInTheDocument();
    expect(screen.getByText("fine.txt")).toBeInTheDocument();
  });
});
