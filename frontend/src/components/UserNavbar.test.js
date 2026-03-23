import React from "react";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { BrowserRouter } from "react-router-dom";

import UserNavbar from "./UserNavbar";

// ─── Mocks ────────────────────────────────────────────────────────────────────

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useNavigate: () => mockNavigate,
}));

const mockLogout = jest.fn();

jest.mock("../context/AuthContext", () => ({
  useAuth: () => ({ logout: mockLogout }),
}));

// ─── Helper ───────────────────────────────────────────────────────────────────

function renderNavbar() {
  return render(
    <BrowserRouter>
      <UserNavbar />
    </BrowserRouter>
  );
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe("UserNavbar — rendering", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("renders the KCL Ticketing brand link", () => {
    renderNavbar();
    expect(screen.getByText(/KCL Ticketing/i)).toBeInTheDocument();
  });

  test("brand link points to /dashboard", () => {
    renderNavbar();
    const brand = screen.getByText(/KCL Ticketing/i).closest("a");
    expect(brand).toHaveAttribute("href", "/dashboard");
  });

  test("renders a Home link pointing to /dashboard", () => {
    renderNavbar();
    // There are two links to /dashboard (brand + Home); find the one with text "Home"
    const homeLink = screen.getByRole("link", { name: /^home$/i });
    expect(homeLink).toBeInTheDocument();
    expect(homeLink).toHaveAttribute("href", "/dashboard");
  });

  test("renders a View FAQs link pointing to /faqs", () => {
    renderNavbar();
    const faqLink = screen.getByRole("link", { name: /view faqs/i });
    expect(faqLink).toBeInTheDocument();
    expect(faqLink).toHaveAttribute("href", "/faqs");
  });

  test("renders the Profile toggle button", () => {
    renderNavbar();
    expect(
      screen.getByRole("button", { name: /profile/i })
    ).toBeInTheDocument();
  });

  test("renders the Log Out button", () => {
    renderNavbar();
    expect(
      screen.getByRole("button", { name: /log out/i })
    ).toBeInTheDocument();
  });

  test("profile dropdown is hidden on initial render", () => {
    renderNavbar();
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("UserNavbar — Profile dropdown", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("dropdown opens when the Profile button is clicked", () => {
    renderNavbar();
    const toggle = screen.getByRole("button", { name: /profile/i });
    fireEvent.click(toggle);
    expect(screen.getByRole("menu")).toBeInTheDocument();
  });

  test("dropdown closes when the Profile button is clicked again", () => {
    renderNavbar();
    const toggle = screen.getByRole("button", { name: /profile/i });
    fireEvent.click(toggle);
    expect(screen.getByRole("menu")).toBeInTheDocument();
    fireEvent.click(toggle);
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  test("dropdown opens on mouse enter and closes on mouse leave", () => {
    renderNavbar();
    const wrapper = screen
      .getByRole("button", { name: /profile/i })
      .closest(".navbar-dropdown-wrapper");

    fireEvent.mouseEnter(wrapper);
    expect(screen.getByRole("menu")).toBeInTheDocument();

    fireEvent.mouseLeave(wrapper);
    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  test("dropdown shows 'Edit Profile' menu item when open", () => {
    renderNavbar();
    fireEvent.click(screen.getByRole("button", { name: /profile/i }));

    const items = screen.getAllByRole("menuitem");
    expect(items).toHaveLength(1);
    expect(items[0]).toHaveTextContent("Edit Profile");
  });

  test("'Edit Profile' menu item links to /profile", () => {
    renderNavbar();
    fireEvent.click(screen.getByRole("button", { name: /profile/i }));

    const editProfileItem = screen.getAllByRole("menuitem")[0];
    expect(editProfileItem).toHaveAttribute("href", "/profile");
  });

  test("clicking the Edit Profile menu item closes the dropdown", () => {
    renderNavbar();
    fireEvent.click(screen.getByRole("button", { name: /profile/i }));
    expect(screen.getByRole("menu")).toBeInTheDocument();

    const editProfileItem = screen.getAllByRole("menuitem")[0];
    fireEvent.click(editProfileItem);

    expect(screen.queryByRole("menu")).not.toBeInTheDocument();
  });

  test("Profile toggle has correct aria-haspopup attribute", () => {
    renderNavbar();
    const toggle = screen.getByRole("button", { name: /profile/i });
    expect(toggle).toHaveAttribute("aria-haspopup", "true");
  });

  test("Profile toggle aria-expanded is false when dropdown is closed", () => {
    renderNavbar();
    const toggle = screen.getByRole("button", { name: /profile/i });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
  });

  test("Profile toggle aria-expanded is true when dropdown is open", () => {
    renderNavbar();
    const toggle = screen.getByRole("button", { name: /profile/i });
    fireEvent.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "true");
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("UserNavbar — Log Out", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLogout.mockResolvedValue({ success: true });
  });

  test("clicking Log Out calls the logout function", async () => {
    renderNavbar();
    fireEvent.click(screen.getByRole("button", { name: /log out/i }));
    await waitFor(() => expect(mockLogout).toHaveBeenCalledTimes(1));
  });

  test("clicking Log Out navigates to /login after logout resolves", async () => {
    renderNavbar();
    fireEvent.click(screen.getByRole("button", { name: /log out/i }));
    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true })
    );
  });

  test("logout still navigates to /login even if logout() rejects", async () => {
    mockLogout.mockRejectedValue(new Error("network error"));
    renderNavbar();
    fireEvent.click(screen.getByRole("button", { name: /log out/i }));
    // Component catches the error and navigates anyway — user is never left stuck
    await waitFor(() =>
      expect(mockNavigate).toHaveBeenCalledWith("/login", { replace: true })
    );
  });
});

// ─────────────────────────────────────────────────────────────────────────────

describe("UserNavbar — navigation links", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("navbar contains exactly two links pointing to /dashboard (brand + Home)", () => {
    renderNavbar();
    const dashboardLinks = screen
      .getAllByRole("link")
      .filter((l) => l.getAttribute("href") === "/dashboard");
    expect(dashboardLinks).toHaveLength(2);
  });

  test("there is exactly one link pointing to /faqs", () => {
    renderNavbar();
    const faqLinks = screen
      .getAllByRole("link")
      .filter((l) => l.getAttribute("href") === "/faqs");
    expect(faqLinks).toHaveLength(1);
  });

  test("profile link to /profile is only visible after opening the dropdown", () => {
    renderNavbar();
    // Before opening — dropdown not rendered, no menuitems
    expect(screen.queryByRole("menuitem")).not.toBeInTheDocument();

    // After opening — one menuitem linking to /profile
    fireEvent.click(screen.getByRole("button", { name: /profile/i }));
    const items = screen.getAllByRole("menuitem");
    expect(items).toHaveLength(1);
    expect(items[0]).toHaveAttribute("href", "/profile");
  });
});
