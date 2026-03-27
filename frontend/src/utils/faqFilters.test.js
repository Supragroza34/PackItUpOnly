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

  test('invalid role string shows all audience-visible rows (no filter by audience)', () => {
    const tiny = [
      { id: 1, category: 'A', audience: 'all', question: 'q', answer: 'a', tags: [] },
      { id: 2, category: 'A', audience: 'staff', question: 'q2', answer: 'a2', tags: [] },
    ];
    const out = filterFaqs(tiny, { role: 'guest', category: 'All', searchTerm: '' });
    expect(out.length).toBe(2);
  });

  test('trimmed role and staff-only audience', () => {
    const tiny = [
      { id: 1, category: 'A', audience: 'staff', question: 'q', answer: 'a', tags: [] },
      { id: 2, category: 'A', audience: 'student', question: 's', answer: 'b', tags: [] },
    ];
    const staff = filterFaqs(tiny, { role: '  STAFF  ', category: 'All', searchTerm: '' });
    expect(staff.map((f) => f.id)).toEqual([1]);

    const student = filterFaqs(tiny, { role: 'student', category: 'All', searchTerm: '' });
    expect(student.map((f) => f.id)).toEqual([2]);
  });

  test('search term whitespace-only matches all', () => {
    const tiny = [
      { id: 1, category: 'A', audience: 'all', question: 'hello', answer: 'world', tags: [] },
    ];
    expect(filterFaqs(tiny, { category: 'All', role: 'student', searchTerm: '   ' })).toHaveLength(1);
  });

  test('search matches tags and question text', () => {
    const tiny = [
      { id: 1, category: 'A', audience: 'all', question: 'alpha', answer: 'beta', tags: ['gamma'] },
    ];
    expect(filterFaqs(tiny, { category: 'All', role: 'student', searchTerm: 'gamma' })).toHaveLength(1);
    expect(filterFaqs(tiny, { category: 'All', role: 'student', searchTerm: 'ALPHA' })).toHaveLength(1);
    expect(filterFaqs(tiny, { category: 'All', role: 'student', searchTerm: 'nomatch' })).toHaveLength(0);
  });

  test('getCategoryCounts counts non-All category buckets', () => {
    const tiny = [
      { id: 1, category: 'A', audience: 'all', question: 'q', answer: 'a', tags: [] },
      { id: 2, category: 'B', audience: 'all', question: 'q', answer: 'a', tags: [] },
    ];
    const counts = getCategoryCounts(tiny, ['All', 'A', 'B'], 'student');
    expect(counts.All).toBe(2);
    expect(counts.A).toBe(1);
    expect(counts.B).toBe(1);
  });

  test('non-string role is treated as no role filter', () => {
    const tiny = [
      { id: 1, category: 'A', audience: 'staff', question: 'q', answer: 'a', tags: [] },
    ];
    const out = filterFaqs(tiny, { role: null, category: 'All', searchTerm: '' });
    expect(out.length).toBe(1);
  });
});
