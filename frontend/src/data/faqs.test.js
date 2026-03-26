import { FAQ_CATEGORIES, faqItems } from "./faqs";

describe("faq data", () => {
  test("contains expected categories", () => {
    expect(FAQ_CATEGORIES).toContain("All");
    expect(FAQ_CATEGORIES).toContain("Tickets");
    expect(FAQ_CATEGORIES).toContain("General");
  });

  test("faq items have unique ids and required shape", () => {
    const ids = faqItems.map((item) => item.id);
    const uniqueIds = new Set(ids);

    expect(uniqueIds.size).toBe(ids.length);
    faqItems.forEach((item) => {
      expect(item.question).toBeTruthy();
      expect(item.answer).toBeTruthy();
      expect(Array.isArray(item.tags)).toBe(true);
    });
  });
});
