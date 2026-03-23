import adminApi from "./adminApi";

describe("adminApi", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    localStorage.setItem("access", "admintoken");
    global.fetch = jest.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    localStorage.clear();
  });

  test("getCurrentUser returns JSON", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 1, username: "admin" }),
    });

    const u = await adminApi.getCurrentUser();
    expect(u.username).toBe("admin");
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/users/me/",
      expect.any(Object)
    );
  });

  test("getCurrentUser throws when unauthorized", async () => {
    global.fetch.mockResolvedValue({ ok: false, status: 401 });

    await expect(adminApi.getCurrentUser()).rejects.toThrow(/Failed to fetch user/i);
  });

  test("getDashboardStats maps 403 message", async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 403,
      text: () => Promise.resolve(""),
    });

    await expect(adminApi.getDashboardStats()).rejects.toThrow(/Access denied/i);
  });

  test("getTickets builds query string", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ results: [] }),
    });

    await adminApi.getTickets({ search: "foo", page: 2, page_size: 10 });

    expect(global.fetch).toHaveBeenCalledWith(
      expect.stringContaining("search=foo"),
      expect.any(Object)
    );
    expect(global.fetch.mock.calls[0][0]).toContain("page=2");
  });

  test("updateTicket throws with DRF validation", async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ status: ["Invalid"] }),
    });

    await expect(adminApi.updateTicket(1, { status: "bad" })).rejects.toThrow(/status/i);
  });

  test("getStatistics appends date params", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({}),
    });

    await adminApi.getStatistics({ days: 30 });

    expect(global.fetch.mock.calls[0][0]).toContain("days=30");
  });
});
