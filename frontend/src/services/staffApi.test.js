import staffApi from "./staffApi";

describe("staffApi", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    sessionStorage.setItem("access", "jwt-test");
    global.fetch = jest.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    sessionStorage.clear();
  });

  test("getStaffList returns JSON on success", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ staff: [{ id: 1 }] }),
    });

    const data = await staffApi.getStaffList();
    expect(data).toEqual({ staff: [{ id: 1 }] });
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/staff/list/",
      expect.objectContaining({
        headers: expect.objectContaining({ Authorization: "Bearer jwt-test" }),
      })
    );
  });

  test("getStaffList throws when not ok", async () => {
    global.fetch.mockResolvedValue({ ok: false, json: () => Promise.resolve({}) });

    await expect(staffApi.getStaffList()).rejects.toThrow(/Failed to fetch staff list/i);
  });

  test("reassignTicket throws with backend error field", async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ assigned_to: ["Invalid pk"] }),
    });

    await expect(
      staffApi.reassignTicket(5, { assigned_to: 99 })
    ).rejects.toThrow(/assigned_to/i);
  });

  test("reassignTicket returns body on success", async () => {
    global.fetch.mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ id: 5, status: "pending" }),
    });

    const out = await staffApi.reassignTicket(5, { assigned_to: 2 });
    expect(out.status).toBe("pending");
  });

  test("getAuthHeaders omits Authorization when no token", async () => {
    sessionStorage.clear();
    global.fetch.mockResolvedValue({ ok: true, json: () => Promise.resolve({ staff: [] }) });

    await staffApi.getStaffList();

    expect(global.fetch.mock.calls[0][1].headers.Authorization).toBeUndefined();
  });

  test("reassignTicket throws with detail and generic fallback", async () => {
    global.fetch
      .mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: "Not allowed" }),
      })
      .mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({}),
      })
      .mockResolvedValueOnce({
        ok: false,
        json: () => Promise.reject(new Error("bad json")),
      });

    await expect(staffApi.reassignTicket(1, {})).rejects.toThrow(/Not allowed/i);
    await expect(staffApi.reassignTicket(1, {})).rejects.toThrow(/failed to reassign ticket/i);
    await expect(staffApi.reassignTicket(1, {})).rejects.toThrow(/failed to reassign ticket/i);
  });
});
