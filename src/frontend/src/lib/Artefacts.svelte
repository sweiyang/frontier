<script>
  import { authFetch } from "./utils.js";
  import { onMount } from "svelte";

  let { onback = () => {}, onopen = () => {} } = $props();

  let artefacts = $state([]);
  let isLoading = $state(true);
  let error = $state(null);
  let searchQuery = $state("");

  onMount(async () => {
    await loadArtefacts();
  });

  async function loadArtefacts() {
    isLoading = true;
    error = null;
    try {
      const res = await authFetch("/artefacts");
      if (res.ok) {
        const data = await res.json();
        artefacts = data.artefacts || [];
      } else {
        error = "Failed to load artefacts.";
      }
    } catch (e) {
      error = "Network error. Please try again.";
    } finally {
      isLoading = false;
    }
  }

  const filtered = $derived(
    artefacts.filter((a) =>
      a.project_name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  function visibilityLabel(v) {
    if (v === "public") return "Public";
    if (v === "org") return "Organisation";
    return "Private";
  }

  function visibilityColor(v) {
    if (v === "public") return "#16a34a";
    if (v === "org") return "#2563eb";
    return "#6b7280";
  }
</script>

<div class="artefacts-page">
  <div class="artefacts-header">
    <button class="back-btn" onclick={onback}>
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="15 18 9 12 15 6"></polyline>
      </svg>
      Back
    </button>
    <div class="header-content">
      <h1 class="page-title">Artefacts</h1>
      <p class="page-subtitle">Shared chatbots available to your organisation</p>
    </div>
  </div>

  <div class="artefacts-body">
    <div class="search-bar-wrap">
      <svg class="search-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <input
        class="search-input"
        type="text"
        placeholder="Search artefacts..."
        bind:value={searchQuery}
      />
    </div>

    {#if isLoading}
      <div class="state-box">
        <div class="spinner"></div>
        <p>Loading artefacts…</p>
      </div>
    {:else if error}
      <div class="state-box error">
        <p>{error}</p>
        <button class="retry-btn" onclick={loadArtefacts}>Retry</button>
      </div>
    {:else if filtered.length === 0}
      <div class="state-box">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
        </svg>
        <p>{searchQuery ? "No artefacts match your search." : "No artefacts available yet."}</p>
      </div>
    {:else}
      <div class="artefacts-grid">
        {#each filtered as artefact}
          <div class="artefact-card" role="button" tabindex="0"
            onclick={() => onopen(artefact.project_name)}
            onkeydown={(e) => e.key === "Enter" && onopen(artefact.project_name)}
          >
            <div class="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
              </svg>
            </div>
            <div class="card-body">
              <div class="card-name">{artefact.project_name}</div>
              <div class="card-meta">
                <span class="visibility-badge" style="color: {visibilityColor(artefact.artefact_visibility)}; background: {visibilityColor(artefact.artefact_visibility)}18;">
                  {visibilityLabel(artefact.artefact_visibility)}
                </span>
              </div>
            </div>
            <div class="card-arrow">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .artefacts-page {
    display: flex;
    flex-direction: column;
    height: 100vh;
    background: var(--bg-primary, #fff);
    font-family: 'Inter', sans-serif;
  }

  .artefacts-header {
    flex-shrink: 0;
    padding: 1.25rem 2rem;
    border-bottom: 1px solid var(--border-color, #e5e5e5);
    display: flex;
    align-items: center;
    gap: 1.5rem;
    background: var(--bg-primary, #fff);
  }

  .back-btn {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.45rem 0.9rem;
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: 8px;
    background: transparent;
    color: var(--text-secondary, #6b6b6b);
    font-size: 0.875rem;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
    white-space: nowrap;
  }

  .back-btn:hover {
    background: var(--bg-secondary, #f9f9fa);
    color: var(--text-primary, #0f0f0f);
  }

  .header-content {
    flex: 1;
  }

  .page-title {
    font-family: 'Outfit', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--text-primary, #0f0f0f);
    margin: 0 0 0.2rem;
  }

  .page-subtitle {
    font-size: 0.875rem;
    color: var(--text-secondary, #6b6b6b);
    margin: 0;
  }

  .artefacts-body {
    flex: 1;
    overflow-y: auto;
    padding: 2rem;
    max-width: 900px;
    width: 100%;
    margin: 0 auto;
    box-sizing: border-box;
  }

  .search-bar-wrap {
    position: relative;
    margin-bottom: 1.5rem;
  }

  .search-icon {
    position: absolute;
    left: 0.85rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-secondary, #6b6b6b);
    pointer-events: none;
  }

  .search-input {
    width: 100%;
    padding: 0.65rem 1rem 0.65rem 2.5rem;
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: 10px;
    font-size: 0.9rem;
    background: var(--bg-secondary, #f9f9fa);
    color: var(--text-primary, #0f0f0f);
    box-sizing: border-box;
    transition: border-color 0.15s, box-shadow 0.15s;
  }

  .search-input:focus {
    outline: none;
    border-color: #f59e0b;
    box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.12);
  }

  .state-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 4rem 2rem;
    color: var(--text-secondary, #6b6b6b);
    font-size: 0.9rem;
    text-align: center;
  }

  .state-box.error {
    color: #dc2626;
  }

  .retry-btn {
    padding: 0.5rem 1.5rem;
    border: 1px solid #dc2626;
    border-radius: 8px;
    background: transparent;
    color: #dc2626;
    font-size: 0.875rem;
    cursor: pointer;
  }

  .spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-color, #e5e5e5);
    border-top-color: #f59e0b;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .artefacts-grid {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .artefact-card {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 1.25rem;
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: 12px;
    background: var(--bg-primary, #fff);
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
  }

  .artefact-card:hover {
    background: var(--bg-secondary, #f9f9fa);
    border-color: #f59e0b;
    box-shadow: 0 2px 8px rgba(245, 158, 11, 0.08);
  }

  .card-icon {
    width: 44px;
    height: 44px;
    background: #fef3c7;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #d97706;
    flex-shrink: 0;
  }

  .card-body {
    flex: 1;
    min-width: 0;
  }

  .card-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-primary, #0f0f0f);
    margin-bottom: 0.3rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .card-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .visibility-badge {
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.2rem 0.6rem;
    border-radius: 99px;
  }

  .card-arrow {
    color: var(--text-secondary, #6b6b6b);
    flex-shrink: 0;
  }
</style>
