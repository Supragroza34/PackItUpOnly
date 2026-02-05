import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

describe('App Component', () => {
  test('renders TicketForm component on root route', () => {
    window.history.pushState({}, '', '/');
    render(<App />);
    expect(screen.getByText('Ticket Form')).toBeInTheDocument();
  });

  test('renders faq page on /faqs route', () => {
    window.history.pushState({}, '', '/faqs');
    render(<App />);
    expect(screen.getByText('FAQs')).toBeInTheDocument();
    expect(
      screen.getByText('Answers to common questions about tickets, tracking, and using the platform.')
    ).toBeInTheDocument();
  });
});
