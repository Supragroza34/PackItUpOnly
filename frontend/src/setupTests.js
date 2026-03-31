// Jest DOM provides custom matchers for asserting on DOM nodes
import '@testing-library/jest-dom';

// Mock window.alert
global.alert = jest.fn();

// Suppress React Router v7 future flag warnings
const originalWarn = console.warn;
console.warn = (...args) => {
  if (typeof args[0] === "string" && args[0].includes("React Router Future Flag Warning")) return;
  if (typeof args[0] === "string" && args[0].includes("ImmutableStateInvariantMiddleware")) return;
  originalWarn(...args);
};

// Suppress known noisy console.error patterns that are not test failures
const originalError = console.error;
console.error = (...args) => {
  const msg = typeof args[0] === "string" ? args[0] : "";
  if (msg.includes("Not implemented: navigation")) return;
  if (msg.includes("was not wrapped in act(...)")) return;
  if (msg.includes("Dashboard fetch error")) return;
  if (msg.includes("PDF download error")) return;
  if (msg.includes("validateDOMNesting")) return;
  originalError(...args);
};
