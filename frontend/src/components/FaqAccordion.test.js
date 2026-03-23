import React from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

import FaqAccordion from "./FaqAccordion";

const items = [
  {
    id: "a1",
    question: "Plain question?",
    answer: "First paragraph.\n\nSecond paragraph.",
  },
  {
    id: "a2",
    question: "Bullets?",
    answer: "- One\n- Two",
  },
];

describe("FaqAccordion", () => {
  test("expands and collapses item on toggle", async () => {
    render(<FaqAccordion items={items} />);

    const btn = screen.getByRole("button", { name: /Plain question/i });
    expect(btn).toHaveAttribute("aria-expanded", "false");

    await userEvent.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "true");
    expect(screen.getByText("First paragraph.")).toBeInTheDocument();

    await userEvent.click(btn);
    expect(btn).toHaveAttribute("aria-expanded", "false");
  });

  test("renders bullet list block for lines starting with - ", async () => {
    render(<FaqAccordion items={[items[1]]} />);

    await userEvent.click(screen.getByRole("button", { name: /Bullets/i }));
    expect(screen.getByText("One")).toBeInTheDocument();
    expect(screen.getByText("Two")).toBeInTheDocument();
  });
});
