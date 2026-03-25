import { writable } from 'svelte/store';

export const toasts = writable([]);

let _counter = 0;

/**
 * Show a toast notification.
 * @param {string} message
 * @param {'info'|'success'|'error'|'warning'} type
 * @param {number} duration ms before auto-dismiss (0 = never)
 */
export function showToast(message, type = 'info', duration = 4000) {
  const id = ++_counter;
  toasts.update(t => [...t, { id, message, type }]);
  if (duration > 0) {
    setTimeout(() => dismissToast(id), duration);
  }
}

export function dismissToast(id) {
  toasts.update(t => t.filter(toast => toast.id !== id));
}
