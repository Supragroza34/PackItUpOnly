import React from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";

import { HtmlContent } from "./HtmlContent";

describe("HtmlContent", () => {
  test("returns nothing for invalid html input", () => {
    const { container: c1 } = render(<HtmlContent html={null} />);
    expect(c1.firstChild).toBeNull();

    const { container: c2 } = render(<HtmlContent html={123} />);
    expect(c2.firstChild).toBeNull();

    const { container: c3 } = render(<HtmlContent html="" />);
    expect(c3.firstChild).toBeNull();
  });

  test("renders sanitized html with default class", () => {
    render(<HtmlContent html="<p><strong>Bold</strong> text</p>" />);

    const bold = screen.getByText("Bold");
    expect(bold.tagName).toBe("STRONG");
    expect(bold.closest(".html-content")).toBeInTheDocument();
  });

  test("applies custom className along with default class", () => {
    const { container } = render(<HtmlContent html="<p>hello</p>" className="ticket-details" />);

    const wrapper = container.querySelector(".html-content.ticket-details");
    expect(wrapper).toBeInTheDocument();
  });
});
