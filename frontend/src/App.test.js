import React from "react";
import { render, screen } from "@testing-library/react";

jest.mock("./context/AuthContext", () => ({
  AuthProvider: ({ children }) => <>{children}</>,
}));

jest.mock("./Login", () => () => <div>Login Page</div>);
jest.mock("./Signup", () => () => <div>Signup Page</div>);
jest.mock("./Profile", () => () => <div>Profile Page</div>);
jest.mock("./pages/UserDashboardPage", () => () => <div>User Dashboard</div>);
jest.mock("./pages/TicketFormPage", () => () => <div>Ticket Form</div>);
jest.mock("./pages/StaffDirectory", () => () => <div>Staff Directory</div>);
jest.mock("./pages/StaffMeetingPage", () => () => <div>Staff Meeting</div>);
jest.mock("./pages/StaffMeetingRequestsPage", () => () => <div>Staff Meeting Requests</div>);
jest.mock("./pages/MyMeetingsPage", () => () => <div>My Meetings</div>);
jest.mock("./pages/StaffDashboardPage", () => () => <div>Staff Dashboard</div>);
jest.mock("./pages/TicketPage", () => () => <div>Ticket Page</div>);
jest.mock("./pages/FaqPage", () => () => <div>FAQ Page</div>);
jest.mock("./AIChatbot/ChatbotPage", () => () => <div>Chatbot Page</div>);
jest.mock("./components/Admin/AdminDashboard", () => () => <div>Admin Dashboard</div>);
jest.mock("./components/Admin/TicketsManagement", () => () => <div>Tickets Management</div>);
jest.mock("./components/Admin/UsersManagement", () => () => <div>Users Management</div>);
jest.mock("./components/Admin/Statistics", () => () => <div>Statistics</div>);

jest.mock("./utils/PrivateRoute", () => ({
  __esModule: true,
  default: ({ children }) => <>{children}</>,
}));

describe("App routes", () => {
  beforeEach(() => {
    localStorage.clear();
    window.history.pushState({}, "", "/");
  });

  test("renders login route", () => {
    window.history.pushState({}, "", "/login");
    const App = require("./App").default;
    render(<App />);
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });

  test("redirects protected route to login when unauthenticated", () => {
    window.history.pushState({}, "", "/dashboard");
    const App = require("./App").default;
    render(<App />);
    expect(screen.getByText("Login Page")).toBeInTheDocument();
  });

  test("renders protected route when authenticated", () => {
    localStorage.setItem("access", "token");
    window.history.pushState({}, "", "/dashboard");
    const App = require("./App").default;
    render(<App />);
    expect(screen.getByText("User Dashboard")).toBeInTheDocument();
  });
});
