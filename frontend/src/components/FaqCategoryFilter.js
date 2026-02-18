import React from 'react';

const FaqCategoryFilter = ({ categories, selectedCategory, counts, onSelect }) => (
  <div className="faq-category-filter" role="tablist" aria-label="FAQ categories">
    {categories.map((category) => (
      <button
        key={category}
        type="button"
        role="tab"
        aria-selected={selectedCategory === category}
        className={`faq-chip ${selectedCategory === category ? 'active' : ''}`}
        onClick={() => onSelect(category)}
      >
        {category}
        <span className="faq-chip-count">{counts[category] ?? 0}</span>
      </button>
    ))}
  </div>
);

export default FaqCategoryFilter;
