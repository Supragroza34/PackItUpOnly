import staffApi from "./staffApi";

describe("staffApi", () => {
  const originalFetch = global.fetch;

  beforeEach(() => {
    localStorage.setItem("access", "jwt-test");
    global.fetch = jest.fn();
  });

  afterEach(() => {
    global.fetch = originalFetch;
    localStorage.clear();
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
});
