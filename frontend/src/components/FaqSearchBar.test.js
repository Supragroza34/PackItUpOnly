import React, { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";

import FaqSearchBar from "./FaqSearchBar";

function ControlledSearch() {
  const [value, setValue] = useState("");
  return <FaqSearchBar value={value} onChange={setValue} />;
}

describe("FaqSearchBar", () => {
  test("updates value via onChange", async () => {
    render(<ControlledSearch />);

    await userEvent.type(screen.getByPlaceholderText(/keyword/i), "wifi");
    expect(screen.getByPlaceholderText(/keyword/i)).toHaveValue("wifi");
  });
});
