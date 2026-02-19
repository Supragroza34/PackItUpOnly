import React, { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { apiFetch, authHeaders } from '../api';
import { faqItems } from '../data/faqs';
import { filterFaqs } from '../utils/faqFilters';
import './FaqPage.css';

const STATUS_OPTIONS = [
  { value: 'all', label: 'All statuses' },
  { value: 'pending', label: 'Pending' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'resolved', label: 'Resolved' },
  { value: 'closed', label: 'Closed' }
];

const ORDER_OPTIONS = [
  { value: 'newest', label: 'Newest' },
  { value: 'oldest', label: 'Oldest' }
];

const normalizeType = (value) => (value === 'faqs' ? 'faqs' : 'tickets');

const normalizeStatus = (value) =>
  STATUS_OPTIONS.some((option) => option.value === value) ? value : 'all';

const normalizeOrdering = (value) =>
  ORDER_OPTIONS.some((option) => option.value === value) ? value : 'newest';

const parseParams = (params) => ({
  type: normalizeType(params.get('type')),
  q: params.get('q') || '',
  status: normalizeStatus(params.get('status')),
  ordering: normalizeOrdering(params.get('ordering'))
});

const formatStatus = (value) =>
  value
    ? value
        .split('_')
        .map((chunk) => chunk.charAt(0).toUpperCase() + chunk.slice(1))
        .join(' ')
    : '';

const formatDate = (value) => {
  if (!value) return '';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toLocaleDateString();
};

const SearchPage = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const initial = useMemo(() => parseParams(searchParams), [searchParams]);

  const [type, setType] = useState(initial.type);
  const [status, setStatus] = useState(initial.status);
  const [ordering, setOrdering] = useState(initial.ordering);
  const [query, setQuery] = useState(initial.q);
  const [inputValue, setInputValue] = useState(initial.q);

  const [tickets, setTickets] = useState([]);
  const [ticketsLoading, setTicketsLoading] = useState(false);
  const [ticketsError, setTicketsError] = useState('');

  const searchParamsString = searchParams.toString();

  useEffect(() => {
    const next = parseParams(searchParams);

    if (next.type !== type) setType(next.type);
    if (next.status !== status) setStatus(next.status);
    if (next.ordering !== ordering) setOrdering(next.ordering);
    if (next.q !== query) {
      setQuery(next.q);
      setInputValue(next.q);
    }
  }, [searchParams, type, status, ordering, query]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      if (inputValue !== query) {
        setQuery(inputValue);
      }
    }, 300);

    return () => clearTimeout(timeout);
  }, [inputValue, query]);

  useEffect(() => {
    const params = new URLSearchParams();
    params.set('type', type);

    if (query) {
      params.set('q', query);
    }

    if (type === 'tickets') {
      if (status && status !== 'all') {
        params.set('status', status);
      }

      if (ordering && ordering !== 'newest') {
        params.set('ordering', ordering);
      }
    }

    if (params.toString() !== searchParamsString) {
      setSearchParams(params, { replace: true });
    }
  }, [type, query, status, ordering, searchParamsString, setSearchParams]);

  useEffect(() => {
    if (type !== 'tickets') return;

    const controller = new AbortController();
    const params = new URLSearchParams();

    if (query) params.set('q', query);
    if (status && status !== 'all') params.set('status', status);
    if (ordering) params.set('ordering', ordering);

    const queryString = params.toString();
    const path = queryString ? `/tickets/?${queryString}` : '/tickets/';

    setTicketsLoading(true);
    setTicketsError('');

    apiFetch(path, {
      headers: authHeaders(),
      signal: controller.signal
    })
      .then((data) => setTickets(Array.isArray(data) ? data : []))
      .catch((err) => {
        if (err.name === 'AbortError') return;
        setTicketsError('Unable to load tickets.');
      })
      .finally(() => {
        if (!controller.signal.aborted) {
          setTicketsLoading(false);
        }
      });

    return () => controller.abort();
  }, [type, query, status, ordering]);

  const faqResults = useMemo(
    () => filterFaqs(faqItems, { category: 'All', role: undefined, searchTerm: query }),
    [query]
  );

  const isTickets = type === 'tickets';
  const isFaqs = type === 'faqs';

  const renderTickets = () => {
    if (ticketsLoading) {
      return <p>Loading...</p>;
    }

    if (ticketsError) {
      return (
        <section className="faq-empty-state">
          <h2>Something went wrong</h2>
          <p>{ticketsError}</p>
        </section>
      );
    }

    if (!tickets.length) {
      return (
        <section className="faq-empty-state">
          <h2>No results found</h2>
          <p>No results found</p>
        </section>
      );
    }

    return (
      <div className="faq-accordion">
        {tickets.map((ticket) => (
          <div key={ticket.id} className="faq-item">
            <div className="faq-item-panel">
              <h3 className="faq-item-heading">
                Ticket #{ticket.id} — {ticket.type_of_issue}
              </h3>
              <p>Status: {formatStatus(ticket.status)}</p>
              <p>Created: {formatDate(ticket.created_at)}</p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  const renderFaqs = () => {
    if (!faqResults.length) {
      return (
        <section className="faq-empty-state">
          <h2>No results found</h2>
          <p>No results found</p>
        </section>
      );
    }

    return (
      <div className="faq-accordion">
        {faqResults.map((faq) => (
          <div key={faq.id} className="faq-item">
            <div className="faq-item-panel">
              <h3 className="faq-item-heading">{faq.question}</h3>
              <p>Category: {faq.category}</p>
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="faq-page">
      <header className="faq-header">
        <h1>Search</h1>
        <p>Search across tickets and FAQs.</p>
      </header>

      <section className="faq-controls">
        <div className="faq-search">
          <label htmlFor="search-input" className="sr-only">
            Search
          </label>
          <input
            id="search-input"
            type="text"
            placeholder="Search tickets or FAQs..."
            value={inputValue}
            onChange={(event) => setInputValue(event.target.value)}
          />
        </div>

        <div className="faq-category-filter">
          <button
            type="button"
            className={`faq-chip ${isTickets ? 'active' : ''}`}
            onClick={() => setType('tickets')}
          >
            Tickets
          </button>
          <button
            type="button"
            className={`faq-chip ${isFaqs ? 'active' : ''}`}
            onClick={() => setType('faqs')}
          >
            FAQs
          </button>
        </div>

        {isTickets ? (
          <div className="faq-category-filter">
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Sort
              <select value={ordering} onChange={(event) => setOrdering(event.target.value)}>
                {ORDER_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
        ) : null}
      </section>

      {isTickets ? renderTickets() : renderFaqs()}
    </div>
  );
};

export default SearchPage;
