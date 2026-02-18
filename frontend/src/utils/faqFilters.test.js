import { faqItems } from '../data/faqs';
import { filterFaqs, getCategoryCounts } from './faqFilters';

describe('faq filtering', () => {
  test('filters by role visibility for students', () => {
    const results = filterFaqs(faqItems, { role: 'student' });
    expect(results.every((faq) => faq.audience !== 'staff')).toBe(true);
    expect(results.some((faq) => faq.audience === 'student')).toBe(true);
  });

  test('filters by category and search term', () => {
    const results = filterFaqs(faqItems, {
      category: 'Tracking',
      searchTerm: 'status',
      role: 'staff'
    });

    expect(results.length).toBeGreaterThan(0);
    expect(results.every((faq) => faq.category === 'Tracking')).toBe(true);
    expect(results.every((faq) => faq.question.toLowerCase().includes('status') || faq.answer.toLowerCase().includes('status') || (faq.tags || []).join(' ').toLowerCase().includes('status'))).toBe(true);
  });

  test('category counts are based on visible-by-role faqs', () => {
    const categories = ['All', 'Students', 'Staff'];
    const studentCounts = getCategoryCounts(faqItems, categories, 'student');
    const staffCounts = getCategoryCounts(faqItems, categories, 'staff');

    expect(studentCounts.Staff).toBe(0);
    expect(staffCounts.Students).toBe(0);
    expect(studentCounts.All).toBeGreaterThan(0);
    expect(staffCounts.All).toBeGreaterThan(0);
  });
});
