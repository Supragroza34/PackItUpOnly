const normalizeRole = (role) => {
  if (typeof role !== 'string') {
    return null;
  }

  const normalized = role.trim().toLowerCase();
  return normalized === 'student' || normalized === 'staff' ? normalized : null;
};

const isFaqVisibleForRole = (faq, role) => {
  const normalizedRole = normalizeRole(role);

  if (!normalizedRole) {
    return true;
  }

  return faq.audience === 'all' || faq.audience === normalizedRole;
};

const includesSearchTerm = (faq, searchTerm) => {
  if (!searchTerm) {
    return true;
  }

  const query = searchTerm.trim().toLowerCase();
  if (!query) {
    return true;
  }

  const searchableText = [faq.question, faq.answer, ...(faq.tags || [])]
    .join(' ')
    .toLowerCase();

  return searchableText.includes(query);
};

export const getVisibleFaqsByRole = (faqs, role) =>
  faqs.filter((faq) => isFaqVisibleForRole(faq, role));

export const getCategoryCounts = (faqs, categories, role) => {
  const visibleFaqs = getVisibleFaqsByRole(faqs, role);

  return categories.reduce(
    (counts, category) => ({
      ...counts,
      [category]:
        category === 'All'
          ? visibleFaqs.length
          : visibleFaqs.filter((faq) => faq.category === category).length
    }),
    {}
  );
};

export const filterFaqs = (faqs, { category = 'All', role, searchTerm = '' }) =>
  getVisibleFaqsByRole(faqs, role).filter(
    (faq) => (category === 'All' || faq.category === category) && includesSearchTerm(faq, searchTerm)
  );
