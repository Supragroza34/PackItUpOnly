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
});
