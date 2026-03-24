const STORAGE_KEY = 'frontier_theme';

export function getStoredTheme() {
  return localStorage.getItem(STORAGE_KEY) || 'light';
}

export function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem(STORAGE_KEY, theme);
}

/** Apply theme to DOM only — does NOT overwrite stored preference. */
export function setThemeDom(theme) {
  document.documentElement.setAttribute('data-theme', theme);
}

export function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  applyTheme(next);
  return next;
}
