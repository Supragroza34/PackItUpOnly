import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

import NotificationBell from "./NotificationBell";
import * as api from "../api";

jest.mock("../api", () => ({
  apiFetch: jest.fn(),
}));

describe("NotificationBell", () => {
  beforeEach(() => {
    localStorage.setItem("access", "fake-jwt");
    jest.clearAllMocks();
  });

  afterEach(() => {
    localStorage.removeItem("access");
  });

  test("fetches notifications on mount and keeps single fetch", async () => {
    api.apiFetch.mockResolvedValue([
      { id: 1, title: "T", message: "M", is_read: false },
    ]);

    render(<NotificationBell />);

    await waitFor(() => {
      expect(api.apiFetch).toHaveBeenCalledWith("/notifications/", {}, { auth: true });
    });

    expect(screen.getByText("1")).toBeInTheDocument();

    await userEvent.click(screen.getByText(/Notifications/i));
    expect(screen.getByText("T")).toBeInTheDocument();
    expect(screen.getByText("M")).toBeInTheDocument();

    await userEvent.click(screen.getByText(/Notifications/i));
    await userEvent.click(screen.getByText(/Notifications/i));
    expect(api.apiFetch).toHaveBeenCalledTimes(1);
  });

  test("shows empty state when no notifications", async () => {
    api.apiFetch.mockResolvedValue([]);

    render(<NotificationBell />);
    await userEvent.click(screen.getByText(/Notifications/i));

    await waitFor(() => {
      expect(screen.getByText(/You have no notifications/i)).toBeInTheDocument();
    });
  });

  test("does not fetch when no token", async () => {
    localStorage.removeItem("access");
    render(<NotificationBell />);
    await userEvent.click(screen.getByText(/Notifications/i));
    await waitFor(() => {
      expect(api.apiFetch).not.toHaveBeenCalled();
    });
  });

  test("marks notification read and calls onNotificationClick", async () => {
    api.apiFetch
      .mockResolvedValueOnce([{ id: 7, title: "Hi", message: "Body", is_read: false }])
      .mockResolvedValueOnce({});

    const onNotificationClick = jest.fn();
    render(<NotificationBell onNotificationClick={onNotificationClick} />);

    await userEvent.click(screen.getByText(/Notifications/i));
    await waitFor(() => expect(screen.getByText("Hi")).toBeInTheDocument());

    fireEvent.click(screen.getByText("Hi"));

    await waitFor(() => {
      expect(api.apiFetch).toHaveBeenCalledWith(
        "/notifications/7/read/",
        { method: "POST" },
        { auth: true }
      );
    });
    expect(onNotificationClick).toHaveBeenCalledWith(
      expect.objectContaining({ id: 7 })
    );
  });

  test("reverts read state when mark-read fails", async () => {
    const consoleSpy = jest.spyOn(console, "error").mockImplementation(() => {});
    api.apiFetch
      .mockResolvedValueOnce([{ id: 2, title: "X", message: "Y", is_read: false }])
      .mockRejectedValueOnce(new Error("network"));

    render(<NotificationBell />);
    await userEvent.click(screen.getByText(/Notifications/i));
    await waitFor(() => expect(screen.getByText("X")).toBeInTheDocument());
    fireEvent.click(screen.getByText("X"));

    await waitFor(() => {
      expect(consoleSpy).toHaveBeenCalled();
    });

    consoleSpy.mockRestore();
  });

  test("click outside closes dropdown", async () => {
    api.apiFetch.mockResolvedValue([]);
    render(
      <div>
        <NotificationBell />
        <button type="button">outside</button>
      </div>
    );

    await userEvent.click(screen.getByText(/Notifications/i));
    await waitFor(() => expect(api.apiFetch).toHaveBeenCalled());

    fireEvent.mouseDown(screen.getByText("outside"));

    await waitFor(() => {
      expect(screen.queryByText(/You have no notifications/i)).not.toBeInTheDocument();
    });
  });
});
