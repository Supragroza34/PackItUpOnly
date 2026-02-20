// Jest DOM provides custom matchers for asserting on DOM nodes
import '@testing-library/jest-dom';

// Mock window.alert
global.alert = jest.fn();
