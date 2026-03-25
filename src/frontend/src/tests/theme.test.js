import { describe, it, expect, beforeEach } from 'vitest';

// ---------------------------------------------------------------------------
// localStorage mock
// ---------------------------------------------------------------------------

const localStorageMock = (() => {
  let store = {};
  return {
    getItem: (key) => (key in store ? store[key] : null),
    setItem: (key, value) => { store[key] = String(value); },
    removeItem: (key) => { delete store[key]; },
    clear: () => { store = {}; },
  };
})();

Object.defineProperty(global, 'localStorage', { value: localStorageMock, writable: true });

// Minimal document.documentElement stub if not present in jsdom
if (!document.documentElement.getAttribute) {
  document.documentElement.getAttribute = () => null;
}

const STORAGE_KEY = 'frontier_theme';

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('getStoredTheme', () => {
  beforeEach(() => localStorageMock.clear());

  it('returns "light" when no theme is stored', async () => {
    const { getStoredTheme } = await import('../lib/theme.js');
    expect(getStoredTheme()).toBe('light');
  });

  it('returns the stored theme value', async () => {
    localStorageMock.setItem(STORAGE_KEY, 'dark');
    const { getStoredTheme } = await import('../lib/theme.js');
    expect(getStoredTheme()).toBe('dark');
  });
});

describe('applyTheme', () => {
  beforeEach(() => localStorageMock.clear());

  it('sets data-theme attribute on documentElement', async () => {
    const { applyTheme } = await import('../lib/theme.js');
    applyTheme('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
  });

  it('persists the theme to localStorage', async () => {
    const { applyTheme } = await import('../lib/theme.js');
    applyTheme('dark');
    expect(localStorageMock.getItem(STORAGE_KEY)).toBe('dark');
  });

  it('can set theme back to light', async () => {
    const { applyTheme } = await import('../lib/theme.js');
    applyTheme('dark');
    applyTheme('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
    expect(localStorageMock.getItem(STORAGE_KEY)).toBe('light');
  });
});

describe('setThemeDom', () => {
  beforeEach(() => localStorageMock.clear());

  it('sets data-theme attribute without writing to localStorage', async () => {
    const { setThemeDom } = await import('../lib/theme.js');
    setThemeDom('dark');
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark');
    expect(localStorageMock.getItem(STORAGE_KEY)).toBeNull();
  });
});

describe('toggleTheme', () => {
  beforeEach(() => localStorageMock.clear());

  it('toggles from dark to light', async () => {
    const { applyTheme, toggleTheme } = await import('../lib/theme.js');
    applyTheme('dark');
    const next = toggleTheme();
    expect(next).toBe('light');
    expect(document.documentElement.getAttribute('data-theme')).toBe('light');
  });

  it('toggles from light to dark', async () => {
    const { applyTheme, toggleTheme } = await import('../lib/theme.js');
    applyTheme('light');
    const next = toggleTheme();
    expect(next).toBe('dark');
  });

  it('returns the new theme value', async () => {
    const { applyTheme, toggleTheme } = await import('../lib/theme.js');
    applyTheme('dark');
    const result = toggleTheme();
    expect(result).toBe('light');
  });

  it('persists the toggled theme to localStorage', async () => {
    const { applyTheme, toggleTheme } = await import('../lib/theme.js');
    applyTheme('dark');
    toggleTheme();
    expect(localStorageMock.getItem(STORAGE_KEY)).toBe('light');
  });
});
