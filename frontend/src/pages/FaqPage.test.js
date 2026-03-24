import React from "react";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

import FaqPage from "./FaqPage";

jest.mock("../components/UserNavbar", () => () => <nav data-testid="mock-navbar" />);

describe("FaqPage", () => {
  test("renders header and filters FAQs by search", async () => {
    render(<FaqPage userRole="student" />);

    expect(screen.getByTestId("mock-navbar")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /FAQs/i })).toBeInTheDocument();

    const input = screen.getByPlaceholderText(/keyword/i);
    await userEvent.type(input, "zzzznotfoundzzzz");

    await waitFor(() => {
      expect(screen.getByText(/No FAQs found/i)).toBeInTheDocument();
    });
  });

  test("create ticket CTA calls onNavigate when provided", async () => {
    const onNavigate = jest.fn();
    render(<FaqPage userRole="student" onNavigate={onNavigate} />);

    const link = screen.getByRole("link", { name: /Create a new ticket/i });
    await userEvent.click(link);

    expect(onNavigate).toHaveBeenCalled();
  });

  test("create ticket CTA works without onNavigate callback", async () => {
    render(<FaqPage userRole="student" />);

    const link = screen.getByRole("link", { name: /Create a new ticket/i });
    await userEvent.click(link);

    expect(link).toHaveAttribute("href", "/create-ticket");
  });
});
