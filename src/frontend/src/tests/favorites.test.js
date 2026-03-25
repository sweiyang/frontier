import { describe, it, expect, beforeEach } from 'vitest';
import { get } from 'svelte/store';

// ---------------------------------------------------------------------------
// localStorage mock (shared with utils.test.js setup)
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

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STORAGE_KEY = 'frontier_favorite_agents';

function getFreshStore() {
  // Re-import to pick up fresh localStorage state (module is cached, so we
  // manipulate the exported store directly instead).
  localStorageMock.clear();
  // Reset the store to empty by forcing localStorage to be empty before import.
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('favorites store', () => {
  let favorites;

  beforeEach(async () => {
    localStorageMock.clear();
    // Re-create the store with empty localStorage
    const mod = await import('../lib/favorites.js');
    favorites = mod.favorites;
    // Reset to empty state via toggle trick: toggle off any IDs currently stored
    const current = get(favorites);
    current.forEach((id) => favorites.toggle(id));
  });

  it('starts empty when localStorage has no saved favorites', () => {
    const ids = get(favorites);
    expect(ids).toEqual([]);
  });

  it('toggle adds an id that is not present', () => {
    favorites.toggle(42);
    expect(get(favorites)).toContain(42);
  });

  it('toggle removes an id that is already present', () => {
    favorites.toggle(42);
    favorites.toggle(42);
    expect(get(favorites)).not.toContain(42);
  });

  it('can add multiple distinct favorites', () => {
    favorites.toggle(1);
    favorites.toggle(2);
    favorites.toggle(3);
    const ids = get(favorites);
    expect(ids).toContain(1);
    expect(ids).toContain(2);
    expect(ids).toContain(3);
  });

  it('toggle persists to localStorage', () => {
    favorites.toggle(99);
    const stored = JSON.parse(localStorageMock.getItem(STORAGE_KEY));
    expect(stored).toContain(99);
  });

  it('toggle remove also updates localStorage', () => {
    favorites.toggle(99);
    favorites.toggle(99);
    const stored = JSON.parse(localStorageMock.getItem(STORAGE_KEY));
    expect(stored).not.toContain(99);
  });

  it('isFavorite returns true for a favorited id', () => {
    const ids = [1, 2, 3];
    expect(favorites.isFavorite(ids, 2)).toBe(true);
  });

  it('isFavorite returns false for a non-favorited id', () => {
    const ids = [1, 2, 3];
    expect(favorites.isFavorite(ids, 99)).toBe(false);
  });

  it('isFavorite returns false for empty list', () => {
    expect(favorites.isFavorite([], 1)).toBe(false);
  });
});
