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

  test("getDashboardStats success", async () => {
    global.fetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ ok: true }) });
    await expect(adminApi.getDashboardStats()).resolves.toEqual({ ok: true });
  });

  test("getDashboardStats maps 401 and text error", async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: false, status: 401, text: () => Promise.resolve("") })
      .mockResolvedValueOnce({ ok: false, status: 500, text: () => Promise.resolve("boom") });

    await expect(adminApi.getDashboardStats()).rejects.toThrow(/please log in again/i);
    await expect(adminApi.getDashboardStats()).rejects.toThrow(/boom/i);
  });

  test("ticket detail and delete ticket branches", async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 1 }) })
      .mockResolvedValueOnce({ ok: false, json: () => Promise.resolve({ error: "bad delete" }) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ ok: true }) });

    await expect(adminApi.getTicketDetail(1)).resolves.toEqual({ id: 1 });
    await expect(adminApi.deleteTicket(1)).rejects.toThrow(/bad delete/i);
    await expect(adminApi.deleteTicket(1)).resolves.toEqual({ ok: true });
  });

  test("updateTicket accepts error and detail fallbacks", async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: false, json: () => Promise.resolve({ error: "x" }) })
      .mockResolvedValueOnce({ ok: false, json: () => Promise.resolve({ detail: "y" }) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 2 }) });

    await expect(adminApi.updateTicket(1, {})).rejects.toThrow(/^x$/i);
    await expect(adminApi.updateTicket(1, {})).rejects.toThrow(/^y$/i);
    await expect(adminApi.updateTicket(1, {})).resolves.toEqual({ id: 2 });
  });

  test("users API methods success and failure", async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ users: [] }) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 7 }) })
      .mockResolvedValueOnce({ ok: false, json: () => Promise.resolve({ error: "no" }) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 8 }) })
      .mockResolvedValueOnce({ ok: false, json: () => Promise.resolve({ error: "cannot" }) });

    await expect(adminApi.getUsers({ role: "staff" })).resolves.toEqual({ users: [] });
    await expect(adminApi.getUserDetail(7)).resolves.toEqual({ id: 7 });
    await expect(adminApi.updateUser(7, {})).rejects.toThrow(/no/i);
    await expect(adminApi.updateUser(7, {})).resolves.toEqual({ id: 8 });
    await expect(adminApi.deleteUser(7)).rejects.toThrow(/cannot/i);
  });

  test("staff list and statistics failure branches", async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: false })
      .mockResolvedValueOnce({ ok: false });

    await expect(adminApi.getStaffList()).rejects.toThrow(/failed to fetch staff list/i);
    await expect(adminApi.getStatistics({ start_date: "2026-01-01", end_date: "2026-01-10" })).rejects.toThrow(
      /failed to fetch statistics/i
    );
  });

  test("getAuthHeaders omits Authorization when no token", async () => {
    localStorage.clear();
    global.fetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ results: [] }) });

    await adminApi.getTickets({});

    expect(global.fetch.mock.calls[0][1].headers.Authorization).toBeUndefined();
  });

  test("getTickets failure and all filter query params", async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: false })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ results: [] }) });

    await expect(adminApi.getTickets({})).rejects.toThrow(/failed to fetch tickets/i);

    await adminApi.getTickets({
      search: "q",
      status: "open",
      priority: "high",
      department: "IT",
      assigned_to: 3,
      page: 2,
      page_size: 20,
    });

    const url = global.fetch.mock.calls[1][0];
    expect(url).toContain("search=q");
    expect(url).toContain("status=open");
    expect(url).toContain("priority=high");
    expect(url).toContain("department=IT");
    expect(url).toContain("assigned_to=3");
    expect(url).toContain("page=2");
    expect(url).toContain("page_size=20");
  });

  test("getTicketDetail and getUsers and getUserDetail failures", async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: false })
      .mockResolvedValueOnce({ ok: false })
      .mockResolvedValueOnce({ ok: false });

    await expect(adminApi.getTicketDetail(99)).rejects.toThrow(/failed to fetch ticket details/i);
    await expect(adminApi.getUsers({})).rejects.toThrow(/failed to fetch users/i);
    await expect(adminApi.getUserDetail(5)).rejects.toThrow(/failed to fetch user details/i);
  });

  test("deleteTicket success and deleteUser success", async () => {
    global.fetch
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ deleted: true }) })
      .mockResolvedValueOnce({ ok: true, json: () => Promise.resolve({ id: 1 }) });

    await expect(adminApi.deleteTicket(3)).resolves.toEqual({ deleted: true });
    await expect(adminApi.deleteUser(2)).resolves.toEqual({ id: 1 });
  });

  test("getStaffList success returns JSON", async () => {
    global.fetch.mockResolvedValue({ ok: true, json: () => Promise.resolve([{ id: 1 }]) });

    await expect(adminApi.getStaffList()).resolves.toEqual([{ id: 1 }]);
  });

  test("updateTicket throws generic message when body empty", async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({}),
    });

    await expect(adminApi.updateTicket(1, {})).rejects.toThrow(/failed to update ticket/i);
  });

  test("updateTicket uses formatValidationErrors for non-array field values", async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ status: "not an array" }),
    });

    await expect(adminApi.updateTicket(1, {})).rejects.toThrow(/status:/i);
  });
});

describe("adminApi non-localhost base URLs", () => {
  const originalLocation = window.location;
  const originalFetch = global.fetch;

  afterEach(() => {
    window.location = originalLocation;
    global.fetch = originalFetch;
    localStorage.clear();
    jest.resetModules();
  });

  test("uses deployed origin for dashboard and me when hostname is not local", async () => {
    localStorage.setItem("access", "tok");
    delete window.location;
    window.location = {
      hostname: "deployed.example",
      origin: "https://deployed.example",
    };

    jest.resetModules();
    const adminApiProd = require("./adminApi").default;
    global.fetch = jest.fn().mockResolvedValue({ ok: true, json: () => Promise.resolve({ ok: 1 }) });

    await adminApiProd.getDashboardStats();
    expect(global.fetch.mock.calls[0][0]).toBe(
      "https://deployed.example/api/admin/dashboard/stats/"
    );

    await adminApiProd.getCurrentUser();
    expect(global.fetch.mock.calls[1][0]).toBe("https://deployed.example/api/users/me/");
  });
});
