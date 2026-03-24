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

  test('shows error and removes message on non-OK fetch', async () => {
    const mockResponse = { error: 'Something went wrong!' };
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: false,
        status: 400,
        json: () => Promise.resolve(mockResponse),
      })
    );
    render(<Chatbot />);
    const input = screen.getByPlaceholderText(/type your question/i);
    fireEvent.change(input, { target: { value: 'Trigger error' } });
    fireEvent.submit(input.closest('form'));
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Something went wrong!');
    });
    // The user message should be removed after error
    expect(screen.queryByText('Trigger error')).not.toBeInTheDocument();
  });

  test('shows error and removes message on fetch exception', async () => {
    global.fetch = jest.fn(() => Promise.reject(new Error('Network down')));
    render(<Chatbot />);
    const input = screen.getByPlaceholderText(/type your question/i);
    fireEvent.change(input, { target: { value: 'Network fail' } });
    fireEvent.submit(input.closest('form'));
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Network down');
    });
    // The user message should be removed after error
    expect(screen.queryByText('Network fail')).not.toBeInTheDocument();
  });

  test('uses correct API url for local and production', () => {
    // This test is optional and only covers the API_CHAT logic (line 19)
    const originalHostname = window.location.hostname;
    const originalOrigin = window.location.origin;
    Object.defineProperty(window.location, 'hostname', { value: 'localhost', configurable: true });
    Object.defineProperty(window.location, 'protocol', { value: 'http:', configurable: true });
    expect(require('./Chatbot').API_CHAT).toMatch(/:8000/);
    Object.defineProperty(window.location, 'hostname', { value: 'prod.com', configurable: true });
    Object.defineProperty(window.location, 'origin', { value: 'https://prod.com', configurable: true });
    jest.resetModules();
    expect(require('./Chatbot').API_CHAT).toMatch(/\/api\/ai-chatbot\/chat\//);
    // Restore
    Object.defineProperty(window.location, 'hostname', { value: originalHostname, configurable: true });
    Object.defineProperty(window.location, 'origin', { value: originalOrigin, configurable: true });
  });
});

