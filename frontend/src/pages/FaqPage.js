import React, { useMemo, useState } from 'react';
import FaqAccordion from '../components/FaqAccordion';
import FaqCategoryFilter from '../components/FaqCategoryFilter';
import FaqSearchBar from '../components/FaqSearchBar';
import { FAQ_CATEGORIES, faqItems } from '../data/faqs';
import { filterFaqs, getCategoryCounts } from '../utils/faqFilters';
import './FaqPage.css';

const FaqPage = ({ userRole, onNavigate }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  const categoryCounts = useMemo(
    () => getCategoryCounts(faqItems, FAQ_CATEGORIES, userRole),
    [userRole]
  );

  const filteredFaqs = useMemo(
    () =>
      filterFaqs(faqItems, {
        category: selectedCategory,
        role: userRole,
        searchTerm
      }),
    [searchTerm, selectedCategory, userRole]
  );

  const handleNavigateToCreateTicket = (event) => {
    if (onNavigate) {
      onNavigate(event, '/');
    }
  };

  return (
    <div className="faq-page">
      <header className="faq-header">
        <h1>FAQs</h1>
        <p>Answers to common questions about tickets, tracking, and using the platform.</p>
      </header>

      <section className="faq-controls">
        <FaqSearchBar value={searchTerm} onChange={setSearchTerm} />
        <FaqCategoryFilter
          categories={FAQ_CATEGORIES}
          selectedCategory={selectedCategory}
          counts={categoryCounts}
          onSelect={setSelectedCategory}
        />
      </section>

      {filteredFaqs.length > 0 ? (
        <FaqAccordion items={filteredFaqs} />
      ) : (
        <section className="faq-empty-state">
          <h2>No FAQs found</h2>
          <p>Try a different keyword or category, or create a ticket for direct support.</p>
        </section>
      )}

      <section className="faq-cta">
        <h2>Still need help?</h2>
        <p>Create a new ticket and our team will assist you directly.</p>
        <a href="/" className="faq-cta-button" onClick={handleNavigateToCreateTicket}>
          Create a new ticket
        </a>
      </section>
    </div>
  );
};

export default FaqPage;
