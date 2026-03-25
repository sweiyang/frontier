<script>
  import { toasts, dismissToast } from './toast.js';

  function typeIcon(type) {
    switch (type) {
      case 'success': return '✓';
      case 'error':   return '✕';
      case 'warning': return '!';
      default:        return 'i';
    }
  }
</script>

{#if $toasts.length > 0}
  <div class="toast-container" aria-live="polite" aria-atomic="false">
    {#each $toasts as toast (toast.id)}
      <div class="toast toast-{toast.type}" role="alert">
        <span class="toast-icon">{typeIcon(toast.type)}</span>
        <span class="toast-message">{toast.message}</span>
        <button
          class="toast-close"
          onclick={() => dismissToast(toast.id)}
          aria-label="Dismiss"
        >✕</button>
      </div>
    {/each}
  </div>
{/if}

<style>
  .toast-container {
    position: fixed;
    bottom: 1.5rem;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    z-index: 9999;
    pointer-events: none;
    align-items: center;
  }

  .toast {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.6rem 1rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-lg);
    font-size: 0.875rem;
    font-family: var(--font-sans);
    color: var(--text-primary);
    pointer-events: all;
    min-width: 240px;
    max-width: 420px;
    animation: slideUp 0.15s ease-out;
  }

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .toast-icon {
    font-size: 0.75rem;
    font-weight: 700;
    width: 18px;
    height: 18px;
    border-radius: var(--radius-full);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .toast-success .toast-icon {
    background: #16a34a;
    color: #ffffff;
  }
  .toast-error .toast-icon {
    background: #dc2626;
    color: #ffffff;
  }
  .toast-warning .toast-icon {
    background: #d97706;
    color: #ffffff;
  }
  .toast-info .toast-icon {
    background: #3b82f6;
    color: #ffffff;
  }

  .toast-success { border-left: 3px solid #16a34a; }
  .toast-error   { border-left: 3px solid #dc2626; }
  .toast-warning { border-left: 3px solid #d97706; }
  .toast-info    { border-left: 3px solid #3b82f6; }

  .toast-message {
    flex: 1;
    line-height: 1.4;
  }

  .toast-close {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 0.75rem;
    padding: 0.1rem 0.2rem;
    border-radius: var(--radius-sm);
    flex-shrink: 0;
    transition: color 0.12s ease;
  }
  .toast-close:hover {
    color: var(--text-primary);
  }
</style>
