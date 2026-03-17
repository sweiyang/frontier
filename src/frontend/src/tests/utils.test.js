import { describe, it, expect, beforeEach, vi } from 'vitest';

// Mock localStorage
const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = String(value); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

// Mock sessionStorage
const sessionStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => store[key] || null,
    setItem: (key, value) => { store[key] = String(value); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(global, 'localStorage', { value: localStorageMock });
Object.defineProperty(global, 'sessionStorage', { value: sessionStorageMock });

describe('Token storage', () => {
  beforeEach(() => {
    localStorageMock.clear();
    sessionStorageMock.clear();
  });

  it('saveToken stores the token', async () => {
    const { saveToken, getToken } = await import('../lib/utils.js');
    saveToken('my-token');
    expect(getToken()).toBe('my-token');
  });

  it('clearToken removes the token', async () => {
    const { saveToken, clearToken, getToken } = await import('../lib/utils.js');
    saveToken('my-token');
    clearToken();
    expect(getToken()).toBeNull();
  });

  it('getToken returns null when not set', async () => {
    const { getToken } = await import('../lib/utils.js');
    expect(getToken()).toBeNull();
  });
});

describe('User storage', () => {
  beforeEach(() => {
    localStorageMock.clear();
    sessionStorageMock.clear();
  });

  it('saveUser stores user info', async () => {
    const { saveUser } = await import('../lib/utils.js');
    // Should not throw
    expect(() => saveUser({ username: 'alice', display_name: 'Alice' })).not.toThrow();
  });

  it('getUser retrieves stored user info', async () => {
    const { saveUser, getUser } = await import('../lib/utils.js');
    const user = { username: 'alice', user_id: '123' };
    saveUser(user);
    const retrieved = getUser();
    expect(retrieved).toEqual(user);
  });

  it('getUser returns null when not set', async () => {
    const { getUser } = await import('../lib/utils.js');
    expect(getUser()).toBeNull();
  });

  it('clearToken also clears user', async () => {
    const { saveToken, saveUser, clearToken, getToken, getUser } = await import('../lib/utils.js');
    saveToken('token');
    saveUser({ username: 'alice' });
    clearToken();
    expect(getToken()).toBeNull();
    expect(getUser()).toBeNull();
  });
});

describe('Authentication status', () => {
  beforeEach(() => {
    localStorageMock.clear();
    sessionStorageMock.clear();
  });

  it('isAuthenticated returns false when no token', async () => {
    const { isAuthenticated } = await import('../lib/utils.js');
    expect(isAuthenticated()).toBe(false);
  });

  it('isAuthenticated returns true when token is set', async () => {
    const { saveToken, isAuthenticated } = await import('../lib/utils.js');
    saveToken('my-token');
    expect(isAuthenticated()).toBe(true);
  });
});

describe('Project context', () => {
  beforeEach(() => {
    localStorageMock.clear();
    sessionStorageMock.clear();
  });

  it('setCurrentProject and getCurrentProject roundtrip', async () => {
    const { setCurrentProject, getCurrentProject } = await import('../lib/utils.js');
    setCurrentProject('my-project');
    expect(getCurrentProject()).toBe('my-project');
  });

  it('setCurrentProject null clears the project', async () => {
    const { setCurrentProject, getCurrentProject } = await import('../lib/utils.js');
    setCurrentProject('my-project');
    setCurrentProject(null);
    expect(getCurrentProject()).toBeNull();
  });

  it('getCurrentProject retrieves from sessionStorage if not cached', async () => {
    const { getCurrentProject } = await import('../lib/utils.js');
    sessionStorageMock.setItem('conduit_current_project', 'stored-project');
    expect(getCurrentProject()).toBe('stored-project');
  });
});
