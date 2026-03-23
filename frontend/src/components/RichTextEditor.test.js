import React from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";

import RichTextEditor from "./RichTextEditor";

let latestProps;
let mockEditor;

jest.mock("react-quill", () => {
  const React = require("react");

  return React.forwardRef((props, ref) => {
    latestProps = props;
    mockEditor = {
      getFormat: jest.fn(() => ({
        bold: true,
        list: "bullet",
        color: "red",
        underline: true,
      })),
    };

    React.useImperativeHandle(ref, () => ({ editor: mockEditor }));

    return (
      <div>
        <button
          type="button"
          data-testid="emit-rich-html"
          onClick={() =>
            props.onChange(
              '<p data-indent="2" style="color:red">Text <strong>ok</strong> <u>bad</u><script>alert(1)</script></p>'
            )
          }
        >
          emit-rich-html
        </button>
        <button
          type="button"
          data-testid="emit-empty"
          onClick={() => props.onChange("")}
        >
          emit-empty
        </button>
        <button
          type="button"
          data-testid="emit-list-and-break"
          onClick={() => props.onChange("<ul><li>Item</li></ul><ol><li>One</li></ol><br />")}
        >
          emit-list-and-break
        </button>
      </div>
    );
  });
});

describe("RichTextEditor", () => {
  beforeEach(() => {
    latestProps = undefined;
    mockEditor = undefined;
  });

  test("sanitizes disallowed tags/attributes before calling onChange", () => {
    const onChange = jest.fn();

    render(<RichTextEditor id="additional_details" value="" onChange={onChange} />);

    fireEvent.click(screen.getByTestId("emit-rich-html"));

    expect(onChange).toHaveBeenCalledTimes(1);
    const sanitized = onChange.mock.calls[0][0];
    expect(sanitized).toContain('<p data-indent="2">');
    expect(sanitized).toContain("<strong>ok</strong>");
    expect(sanitized).not.toContain("<u>");
    expect(sanitized).not.toContain("<script");
    expect(sanitized).not.toContain("style=");
  });

  test("passes empty content through sanitize path", () => {
    const onChange = jest.fn();

    render(<RichTextEditor id="additional_details" value="" onChange={onChange} />);
    fireEvent.click(screen.getByTestId("emit-empty"));

    expect(onChange).toHaveBeenCalledWith("");
  });

  test("keeps allowed list and break tags", () => {
    const onChange = jest.fn();

    render(<RichTextEditor id="additional_details" value="" onChange={onChange} />);
    fireEvent.click(screen.getByTestId("emit-list-and-break"));

    const sanitized = onChange.mock.calls[0][0];
    expect(sanitized).toContain("<ul><li>Item</li></ul>");
    expect(sanitized).toContain("<ol><li>One</li></ol>");
    expect(sanitized).toContain("<br>");
  });

  test("applies error class, readOnly mode, allowed formats, and filters getFormat", async () => {
    const onChange = jest.fn();

    const { container } = render(
      <RichTextEditor
        id="additional_details"
        value=""
        onChange={onChange}
        disabled={true}
        hasError={true}
      />
    );

    expect(container.querySelector(".rte-wrapper-error")).toBeInTheDocument();
    expect(latestProps.readOnly).toBe(true);
    expect(latestProps.formats).toEqual(["bold", "italic", "list", "indent"]);

    await waitFor(() => {
      const filtered = mockEditor.getFormat();
      expect(filtered).toEqual({
        bold: true,
        list: "bullet",
      });
      expect(filtered.color).toBeUndefined();
      expect(filtered.underline).toBeUndefined();
    });
  });
});
