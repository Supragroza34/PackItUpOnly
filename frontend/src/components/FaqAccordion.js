import React, { useState } from 'react';

const renderAnswerBlocks = (answer) =>
  answer
    .split('\n\n')
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block, index) => {
      const lines = block
        .split('\n')
        .map((line) => line.trim())
        .filter(Boolean);

      const isBulletBlock = lines.length > 0 && lines.every((line) => line.startsWith('- '));
      if (isBulletBlock) {
        return (
          <ul key={`list-${index}`}>
            {lines.map((line, lineIndex) => (
              <li key={`${line}-${lineIndex}`}>{line.replace('- ', '')}</li>
            ))}
          </ul>
        );
      }

      return <p key={`paragraph-${index}`}>{block}</p>;
    });

const FaqAccordion = ({ items }) => {
  const [expandedItemId, setExpandedItemId] = useState(null);

  const handleToggle = (itemId) => {
    setExpandedItemId((currentId) => (currentId === itemId ? null : itemId));
  };

  return (
    <div className="faq-accordion">
      {items.map((item) => {
        const buttonId = `faq-button-${item.id}`;
        const panelId = `faq-panel-${item.id}`;
        const isExpanded = expandedItemId === item.id;

        return (
          <section key={item.id} className="faq-item">
            <h2 className="faq-item-heading">
              <button
                id={buttonId}
                type="button"
                className="faq-item-trigger"
                aria-expanded={isExpanded}
                aria-controls={panelId}
                onClick={() => handleToggle(item.id)}
              >
                <span>{item.question}</span>
                <span className="faq-item-icon" aria-hidden="true">
                  {isExpanded ? '-' : '+'}
                </span>
              </button>
            </h2>
            <div
              id={panelId}
              role="region"
              aria-labelledby={buttonId}
              className={`faq-item-panel ${isExpanded ? 'expanded' : ''}`}
              hidden={!isExpanded}
            >
              <div className="faq-item-answer">{renderAnswerBlocks(item.answer)}</div>
            </div>
          </section>
        );
      })}
    </div>
  );
};

export default FaqAccordion;
