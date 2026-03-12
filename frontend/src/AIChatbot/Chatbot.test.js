import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import Chatbot from './Chatbot';

describe('Chatbot component (AI helper)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Ensure authHeaders() returns a token
    localStorage.setItem('access', 'test-token-123');
  });

  afterEach(() => {
    delete global.fetch;
  });

  test('shows welcome text initially', () => {
    render(<Chatbot />);
    expect(
      screen.getByText(/ask me anything about support, tickets, or studying/i)
    ).toBeInTheDocument();
  });

  test('sends user message and renders assistant reply', async () => {
    const mockResponse = {
      message: { role: 'assistant', content: 'Hello student!' },
    };

    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve(mockResponse),
      })
    );

    render(<Chatbot />);

    const input = screen.getByPlaceholderText(/type your question/i);
    fireEvent.change(input, { target: { value: 'Hi' } });
    fireEvent.submit(input.closest('form'));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    });

    await waitFor(() => {
      expect(screen.getByText('Hello student!')).toBeInTheDocument();
    });
  });
});

