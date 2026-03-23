import { authHeaders, apiFetch } from "./api";

describe("authHeaders", () => {
  afterEach(() => {
    localStorage.clear();
  });

  test("returns empty object when no token", () => {
    expect(authHeaders()).toEqual({});
  });

  test("returns Authorization header when token present", () => {
    localStorage.setItem("access", "tok123");
    expect(authHeaders()).toEqual({ Authorization: "Bearer tok123" });
  });
});

describe("apiFetch", () => {
  const originalFetch = global.fetch;

  afterEach(() => {
    global.fetch = originalFetch;
    localStorage.clear();
    jest.restoreAllMocks();
  });

  test("returns parsed JSON on success", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ ok: true }),
    });

    const data = await apiFetch("/users/me/");
    expect(data).toEqual({ ok: true });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("/users/me/"),
      expect.objectContaining({
        headers: expect.objectContaining({ "Content-Type": "application/json" }),
      })
    );
  });

  test("returns null on 204 No Content", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 204,
      json: () => Promise.reject(new Error("should not parse")),
    });

    const data = await apiFetch("/noop/");
    expect(data).toBeNull();
  });

  test("includes auth header when auth option true", async () => {
    localStorage.setItem("access", "jwt");
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });

    await apiFetch("/x/", {}, { auth: true });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          Authorization: "Bearer jwt",
        }),
      })
    );
  });

  test("throws with message from DRF field errors object", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 400,
      text: () =>
        Promise.resolve(JSON.stringify({ username: ["Invalid credentials"], detail: "Bad" })),
    });

    await expect(apiFetch("/auth/token/", { method: "POST" })).rejects.toThrow(/Invalid credentials/);
  });

  test("throws with string detail from JSON", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 403,
      text: () => Promise.resolve(JSON.stringify("Forbidden")),
    });

    await expect(apiFetch("/x/")).rejects.toThrow("Forbidden");
  });

  test("throws with raw text when JSON parse fails", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
      text: () => Promise.resolve("Server exploded"),
    });

    await expect(apiFetch("/x/")).rejects.toThrow("Server exploded");
  });

  test("merges custom headers", async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({}),
    });

    await apiFetch("/x/", { headers: { "X-Custom": "1" } });
    expect(global.fetch).toHaveBeenCalledWith(
      expect.any(String),
      expect.objectContaining({
        headers: expect.objectContaining({
          "Content-Type": "application/json",
          "X-Custom": "1",
        }),
      })
    );
  });
});
