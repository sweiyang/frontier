import { writable } from 'svelte/store';

const STORAGE_KEY = 'frontier_favorite_agents';

function createFavoritesStore() {
  const initial = (() => {
    try {
      return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    } catch {
      return [];
    }
  })();

  const { subscribe, set, update } = writable(initial);

  return {
    subscribe,
    toggle(id) {
      update(ids => {
        const next = ids.includes(id) ? ids.filter(i => i !== id) : [...ids, id];
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        return next;
      });
    },
    isFavorite(ids, id) {
      return ids.includes(id);
    },
  };
}

export const favorites = createFavoritesStore();
