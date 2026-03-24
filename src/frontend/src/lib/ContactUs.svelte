<script>
  /**
   * ContactUs component - displays contact options from configuration.
   * @prop {Object} contact - Contact configuration from API
   * @prop {Function} onclose - Callback when modal is closed
   */
  let { contact = {}, onclose = () => {} } = $props();

  function handleBackdropClick(event) {
    if (event.target === event.currentTarget) {
      onclose();
    }
  }

  function handleKeydown(event) {
    if (event.key === "Escape") {
      onclose();
    }
  }

  function openEmail() {
    if (contact.email?.enabled && contact.email?.address) {
      const subject = encodeURIComponent(contact.email.subject_prefix || "[Support]");
      window.open(`mailto:${contact.email.address}?subject=${subject}`, "_blank");
    }
  }

  function openJira() {
    if (contact.jira?.enabled && contact.jira?.url) {
      window.open(contact.jira.url, "_blank");
    }
  }

  // Check if any contact method is available
  const hasContactMethods = $derived(
    (contact.email?.enabled && contact.email?.address) ||
    (contact.jira?.enabled && contact.jira?.url)
  );
</script>

<svelte:window on:keydown={handleKeydown} />

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="modal-backdrop" onclick={handleBackdropClick}>
  <div class="modal-content">
    <div class="modal-header">
      <h2>Contact Us</h2>
      <button class="close-button" onclick={onclose} aria-label="Close">
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>

    <div class="modal-body">
      {#if hasContactMethods}
        <p class="intro-text">Need help? Choose how you'd like to reach us:</p>

        <div class="contact-options">
          {#if contact.email?.enabled && contact.email?.address}
            <button class="contact-option" onclick={openEmail}>
              <div class="option-icon email-icon">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                  <polyline points="22,6 12,13 2,6" />
                </svg>
              </div>
              <div class="option-content">
                <span class="option-title">Send Email</span>
                <span class="option-description">{contact.email.address}</span>
              </div>
              <svg
                class="arrow-icon"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          {/if}

          {#if contact.jira?.enabled && contact.jira?.url}
            <button class="contact-option" onclick={openJira}>
              <div class="option-icon jira-icon">
                <svg
                  width="24"
                  height="24"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="12" y1="18" x2="12" y2="12" />
                  <line x1="9" y1="15" x2="15" y2="15" />
                </svg>
              </div>
              <div class="option-content">
                <span class="option-title">{contact.jira.button_text || "Create Support Ticket"}</span>
                <span class="option-description">Open a ticket in our support system</span>
              </div>
              <svg
                class="arrow-icon"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <polyline points="9 18 15 12 9 6" />
              </svg>
            </button>
          {/if}
        </div>
      {:else}
        <div class="no-contact">
          <svg
            width="48"
            height="48"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="1.5"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <p>No contact methods have been configured.</p>
          <p class="hint">Please contact your system administrator.</p>
        </div>
      {/if}
    </div>
  </div>
</div>

<style>
  .modal-backdrop {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
    backdrop-filter: blur(4px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.2s ease-out;
  }

  @keyframes fadeIn {
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .modal-content {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg, 12px);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
    width: 90%;
    max-width: 450px;
    max-height: 90vh;
    overflow: hidden;
    animation: slideUp 0.3s ease-out;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: var(--spacing-lg, 1.5rem);
    border-bottom: 1px solid var(--border-color);
  }

  .modal-header h2 {
    margin: 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .close-button {
    padding: var(--spacing-xs, 0.25rem);
    border-radius: var(--radius-md, 8px);
    color: var(--text-secondary);
    transition: all 0.2s ease;
  }

  .close-button:hover {
    background-color: rgba(255, 255, 255, 0.06);
    color: var(--text-primary);
  }

  .modal-body {
    padding: var(--spacing-lg, 1.5rem);
  }

  .intro-text {
    margin: 0 0 var(--spacing-lg, 1.5rem) 0;
    color: var(--text-secondary);
    font-size: 0.95rem;
  }

  .contact-options {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md, 1rem);
  }

  .contact-option {
    display: flex;
    align-items: center;
    gap: var(--spacing-md, 1rem);
    padding: var(--spacing-md, 1rem);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md, 8px);
    background-color: var(--bg-secondary, #f9fafb);
    transition: all 0.2s ease;
    text-align: left;
    width: 100%;
  }

  .contact-option:hover {
    border-color: var(--primary-accent);
    background-color: var(--accent-glow);
    transform: translateY(-1px);
  }

  .option-icon {
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md, 8px);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .email-icon {
    background-color: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }

  .jira-icon {
    background-color: rgba(99, 102, 241, 0.1);
    color: #6366f1;
  }

  .option-content {
    flex: 1;
    min-width: 0;
  }

  .option-title {
    display: block;
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 2px;
  }

  .option-description {
    display: block;
    font-size: 0.85rem;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .arrow-icon {
    color: var(--text-muted, #999);
    flex-shrink: 0;
  }

  .no-contact {
    text-align: center;
    padding: var(--spacing-xl, 2rem) 0;
    color: var(--text-secondary);
  }

  .no-contact svg {
    margin-bottom: var(--spacing-md, 1rem);
    color: var(--text-muted, #999);
  }

  .no-contact p {
    margin: 0;
  }

  .no-contact .hint {
    font-size: 0.85rem;
    margin-top: var(--spacing-xs, 0.25rem);
    color: var(--text-muted, #999);
  }
</style>
