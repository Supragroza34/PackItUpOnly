import React from 'react';

const FaqSearchBar = ({ value, onChange }) => (
  <div className="faq-search">
    <label htmlFor="faq-search-input" className="sr-only">
      Search FAQs
    </label>
    <input
      id="faq-search-input"
      type="text"
      placeholder="Search by keyword, question, or tag..."
      value={value}
      onChange={(event) => onChange(event.target.value)}
    />
  </div>
);

export default FaqSearchBar;
