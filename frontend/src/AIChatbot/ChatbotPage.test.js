import React from "react";
import { render, screen } from "@testing-library/react";
import ChatbotPage from "./ChatbotPage";

jest.mock("./Chatbot", () => () => <div>Mock Chatbot</div>);
jest.mock("../components/UserNavbar", () => () => <div>Mock Navbar</div>);

describe("ChatbotPage", () => {
  test("renders heading and chatbot content", () => {
    render(<ChatbotPage />);

    expect(screen.getByText("AI Helper")).toBeInTheDocument();
    expect(screen.getByText("Mock Navbar")).toBeInTheDocument();
    expect(screen.getByText("Mock Chatbot")).toBeInTheDocument();
  });
});
