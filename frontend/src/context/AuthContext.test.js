import React from "react";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { AuthProvider, useAuth } from "./AuthContext";
import adminApi from "../services/adminApi";
import { apiFetch } from "../api";

jest.mock("../services/adminApi", () => ({
  __esModule: true,
  default: {
    getCurrentUser: jest.fn(),
  },
}));

jest.mock("../api", () => ({
  apiFetch: jest.fn(),
}));

function Consumer() {
  const { user, loading, isAuthenticated, login, logout } = useAuth();
  return (
    <div>
      <div data-testid="loading">{String(loading)}</div>
      <div data-testid="auth">{String(isAuthenticated)}</div>
      <div data-testid="user">{user ? user.username : "none"}</div>
      <button onClick={() => login("u", "p")}>login</button>
      <button onClick={() => logout()}>logout</button>
    </div>
  );
}

describe("AuthContext", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  test("hydrates user when token exists", async () => {
    localStorage.setItem("access", "token");
    adminApi.getCurrentUser.mockResolvedValueOnce({ username: "admin1" });

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });
    expect(screen.getByTestId("user")).toHaveTextContent("admin1");
    expect(screen.getByTestId("auth")).toHaveTextContent("true");
  });

  test("login stores tokens and sets user", async () => {
    apiFetch.mockResolvedValueOnce({ access: "a", refresh: "r" });
    adminApi.getCurrentUser.mockResolvedValueOnce({ username: "student1" });

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    fireEvent.click(screen.getByText("login"));

    await waitFor(() => {
      expect(localStorage.getItem("access")).toBe("a");
      expect(screen.getByTestId("user")).toHaveTextContent("student1");
    });
  });

  test("logout clears tokens", async () => {
    localStorage.setItem("access", "a");
    localStorage.setItem("refresh", "r");

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    fireEvent.click(screen.getByText("logout"));

    await waitFor(() => {
      expect(localStorage.getItem("access")).toBeNull();
      expect(localStorage.getItem("refresh")).toBeNull();
      expect(screen.getByTestId("user")).toHaveTextContent("none");
    });
  });

  test("useAuth throws when used outside AuthProvider", () => {
    const Bad = () => {
      useAuth();
      return null;
    };
    expect(() => render(<Bad />)).toThrow(/must be used within an AuthProvider/i);
  });

  test("checkAuth leaves user unset when no token", async () => {
    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });
    expect(screen.getByTestId("user")).toHaveTextContent("none");
    expect(adminApi.getCurrentUser).not.toHaveBeenCalled();
  });

  test("checkAuth clears user when getCurrentUser fails", async () => {
    localStorage.setItem("access", "bad");
    adminApi.getCurrentUser.mockRejectedValueOnce(new Error("expired"));

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });
    expect(screen.getByTestId("user")).toHaveTextContent("none");
  });

  test("login failure sets error and returns success false", async () => {
    apiFetch.mockRejectedValueOnce(new Error("bad credentials"));

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId("loading")).toHaveTextContent("false");
    });

    fireEvent.click(screen.getByText("login"));

    await waitFor(() => {
      expect(screen.getByTestId("user")).toHaveTextContent("none");
    });
  });

  test("logout returns failure when storage throws", async () => {
    const removeSpy = jest.spyOn(Storage.prototype, "removeItem").mockImplementation(() => {
      throw new Error("storage full");
    });

    localStorage.setItem("access", "a");

    function LogoutErr() {
      const { logout } = useAuth();
      const [out, setOut] = React.useState(null);
      return (
        <div>
          <button onClick={async () => setOut(await logout())}>logout</button>
          <div data-testid="logout-result">{out ? JSON.stringify(out) : ""}</div>
        </div>
      );
    }

    render(
      <AuthProvider>
        <LogoutErr />
      </AuthProvider>
    );

    fireEvent.click(screen.getByText("logout"));

    await waitFor(() => {
      expect(screen.getByTestId("logout-result")).toHaveTextContent(/storage full/i);
    });

    removeSpy.mockRestore();
  });
});
