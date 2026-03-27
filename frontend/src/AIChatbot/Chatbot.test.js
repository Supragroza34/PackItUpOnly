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

  test('does not submit empty or whitespace-only input', () => {
    global.fetch = jest.fn();
    render(<Chatbot />);
    const input = screen.getByPlaceholderText(/type your question/i);
    fireEvent.change(input, { target: { value: '   ' } });
    fireEvent.submit(input.closest('form'));
    expect(global.fetch).not.toHaveBeenCalled();
  });

  test('non-OK response uses detail when error missing', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: false,
        status: 422,
        json: () => Promise.resolve({ detail: 'Rate limited' }),
      })
    );
    render(<Chatbot />);
    const input = screen.getByPlaceholderText(/type your question/i);
    fireEvent.change(input, { target: { value: 'x' } });
    fireEvent.submit(input.closest('form'));
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Rate limited');
    });
  });

  test('non-OK response falls back to status code message', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: false,
        status: 503,
        json: () => Promise.resolve({}),
      })
    );
    render(<Chatbot />);
    const input = screen.getByPlaceholderText(/type your question/i);
    fireEvent.change(input, { target: { value: 'x' } });
    fireEvent.submit(input.closest('form'));
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent('Error 503');
    });
  });

  test('success without message uses empty assistant content', async () => {
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({}),
      })
    );
    render(<Chatbot />);
    const input = screen.getByPlaceholderText(/type your question/i);
    fireEvent.change(input, { target: { value: 'Hi' } });
    fireEvent.submit(input.closest('form'));
    await waitFor(() => {
      expect(document.querySelector('.ai-chatbot-msg-assistant')).toBeInTheDocument();
    });
    expect(document.querySelector('.ai-chatbot-msg-assistant')).toHaveTextContent('');
  });

  test('fetch rejection without message shows default service text', async () => {
    global.fetch = jest.fn(() => Promise.reject({}));
    render(<Chatbot />);
    const input = screen.getByPlaceholderText(/type your question/i);
    fireEvent.change(input, { target: { value: 'x' } });
    fireEvent.submit(input.closest('form'));
    await waitFor(() => {
      expect(screen.getByRole('alert')).toHaveTextContent(/could not reach the chat service/i);
    });
  });

  test('scrollToBottom skips when scrollIntoView is not a function', async () => {
    const orig = HTMLElement.prototype.scrollIntoView;
    // eslint-disable-next-line no-delete-var
    delete HTMLElement.prototype.scrollIntoView;
    global.fetch = jest.fn(() =>
      Promise.resolve({
        ok: true,
        status: 200,
        json: () => Promise.resolve({ message: { role: 'assistant', content: 'ok' } }),
      })
    );
    render(<Chatbot />);
    const input = screen.getByPlaceholderText(/type your question/i);
    fireEvent.change(input, { target: { value: 'Hi' } });
    fireEvent.submit(input.closest('form'));
    await waitFor(() => {
      expect(screen.getByText('ok')).toBeInTheDocument();
    });
    HTMLElement.prototype.scrollIntoView = orig;
  });
});

describe('getApiChatUrl (fresh module)', () => {
  const originalLocation = window.location;

  beforeEach(() => {
    jest.resetModules();
    jest.unmock('./Chatbot');
  });

  afterEach(() => {
    window.location = originalLocation;
  });

  test('returns localhost:8000 URL when hostname is localhost', () => {
    jest.isolateModules(() => {
      delete window.location;
      window.location = {
        hostname: 'localhost',
        protocol: 'http:',
        origin: 'http://localhost:3000',
      };
      const { getApiChatUrl } = require('./Chatbot');
      expect(getApiChatUrl()).toBe('http://localhost:8000/api/ai-chatbot/chat/');
    });
  });

  test('returns same-origin path when not local', () => {
    jest.isolateModules(() => {
      delete window.location;
      window.location = {
        hostname: 'app.example.com',
        protocol: 'https:',
        origin: 'https://app.example.com',
      };
      const { getApiChatUrl } = require('./Chatbot');
      expect(getApiChatUrl()).toBe('https://app.example.com/api/ai-chatbot/chat/');
    });
  });

  test('127.0.0.1 uses port 8000 API', () => {
    jest.isolateModules(() => {
      delete window.location;
      window.location = {
        hostname: '127.0.0.1',
        protocol: 'http:',
        origin: 'http://127.0.0.1:3000',
      };
      const { getApiChatUrl } = require('./Chatbot');
      expect(getApiChatUrl()).toBe('http://127.0.0.1:8000/api/ai-chatbot/chat/');
    });
  });
});

