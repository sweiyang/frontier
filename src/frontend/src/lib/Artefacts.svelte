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
      a.agent_name.toLowerCase().includes(searchQuery.toLowerCase())
    )
  );

  const pastelColors = [
    "#fef3c7", "#dbeafe", "#d1fae5", "#fce7f3", "#e0e7ff",
    "#fef9c3", "#cffafe", "#ede9fe", "#fed7aa", "#d9f99d",
  ];

  function getColor(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) hash = name.charCodeAt(i) + ((hash << 5) - hash);
    return pastelColors[Math.abs(hash) % pastelColors.length];
  }
</script>

<div class="artefacts-page">
  <div class="artefacts-header">
    <div class="header-content">
      <h1 class="page-title">Artifacts</h1>
      <p class="page-subtitle">Shared agents available to your organisation</p>
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
        placeholder="Search artifacts..."
        bind:value={searchQuery}
      />
    </div>

    {#if isLoading}
      <div class="state-box">
        <div class="spinner"></div>
        <p>Loading artifacts…</p>
      </div>
    {:else if error}
      <div class="state-box error">
        <p>{error}</p>
        <button class="retry-btn" onclick={loadArtefacts}>Retry</button>
      </div>
    {:else if filtered.length === 0}
      <div class="state-box">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--text-muted)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="7" height="7" rx="1"></rect>
          <rect x="14" y="3" width="7" height="7" rx="1"></rect>
          <rect x="3" y="14" width="7" height="7" rx="1"></rect>
          <rect x="14" y="14" width="7" height="7" rx="1"></rect>
        </svg>
        <p>{searchQuery ? "No artifacts match your search." : "No artifacts available yet."}</p>
      </div>
    {:else}
      <div class="artefacts-grid">
        {#each filtered as artefact}
          <div class="artefact-card" role="button" tabindex="0"
            onclick={() => onopen(artefact.project_name, artefact.agent_id)}
            onkeydown={(e) => e.key === "Enter" && onopen(artefact.project_name, artefact.agent_id)}
          >
            <div class="card-icon-area" style="background: {getColor(artefact.agent_name)}">
              {#if artefact.icon}
                <img src={artefact.icon} alt="" class="card-icon-img" />
              {:else}
                <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--primary-accent)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2a4 4 0 0 1 4 4v1a4 4 0 0 1-8 0V6a4 4 0 0 1 4-4z"></path>
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path>
                </svg>
              {/if}
            </div>
            <div class="card-body">
              <div class="card-name">{artefact.agent_name}</div>
              <div class="card-meta">
                <span class="card-project">{artefact.project_name}</span>
                {#if artefact.connection_type}
                  <span class="card-type">{artefact.connection_type}</span>
                {:else if artefact.site_builder_enabled}
                  <span class="card-type">site</span>
                {/if}
              </div>
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
    height: 100%;
    width: 100%;
    flex: 1;
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
    width: 100%;
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
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
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
    border-top-color: var(--primary-accent);
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .artefacts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1rem;
  }

  .artefact-card {
    display: flex;
    flex-direction: column;
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: 12px;
    background: var(--bg-primary, #fff);
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;
    overflow: hidden;
  }

  .artefact-card:hover {
    border-color: var(--primary-accent);
    box-shadow: 0 2px 8px var(--accent-glow);
  }

  .card-icon-area {
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .card-icon-img {
    width: 48px;
    height: 48px;
    object-fit: cover;
    border-radius: 10px;
  }

  .card-body {
    padding: 0.75rem 1rem;
  }

  .card-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-primary, #0f0f0f);
    margin-bottom: 0.2rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .card-meta {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    min-width: 0;
  }

  .card-project {
    font-size: 0.8rem;
    color: var(--text-secondary, #6b6b6b);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .card-type {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    padding: 1px 6px;
    border-radius: var(--radius-full, 9999px);
    background: var(--bg-secondary, #f9f9fa);
    color: var(--text-secondary, #6b6b6b);
    white-space: nowrap;
  }
</style>
