import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

import FaqCategoryFilter from "./FaqCategoryFilter";

describe("FaqCategoryFilter", () => {
  test("calls onSelect when chip clicked", async () => {
    const onSelect = jest.fn();
    const categories = ["All", "Tickets"];

    render(
      <FaqCategoryFilter
        categories={categories}
        selectedCategory="All"
        counts={{ All: 3, Tickets: 1 }}
        onSelect={onSelect}
      />
    );

    await userEvent.click(screen.getByRole("tab", { name: /Tickets/i }));
    expect(onSelect).toHaveBeenCalledWith("Tickets");
  });

  test("shows 0 when counts omit a category", () => {
    render(
      <FaqCategoryFilter
        categories={["All", "Other"]}
        selectedCategory="All"
        counts={{ All: 2 }}
        onSelect={jest.fn()}
      />
    );

    expect(screen.getByRole("tab", { name: /Other/i })).toHaveTextContent("0");
  });

  test("marks selected tab with aria-selected and active class", () => {
    const { container } = render(
      <FaqCategoryFilter
        categories={["All", "Tickets"]}
        selectedCategory="Tickets"
        counts={{ All: 1, Tickets: 2 }}
        onSelect={jest.fn()}
      />
    );

    const ticketsTab = screen.getByRole("tab", { name: /Tickets/i });
    expect(ticketsTab).toHaveAttribute("aria-selected", "true");
    expect(ticketsTab.className).toMatch(/active/);
    expect(screen.getByRole("tab", { name: /All/i })).toHaveAttribute("aria-selected", "false");
    expect(container.querySelector(".faq-chip-count")).toHaveTextContent("1");
  });
});
