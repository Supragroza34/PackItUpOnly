describe("setupTests", () => {
  test("provides global alert mock", () => {
    expect(typeof global.alert).toBe("function");
  });

  test("jest-dom matchers are available", () => {
    document.body.innerHTML = "<span data-testid='x'>ok</span>";
    const el = document.querySelector("[data-testid='x']");
    expect(el).toBeInTheDocument();
  });
});
