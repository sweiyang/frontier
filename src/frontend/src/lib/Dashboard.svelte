<script>
  import { onMount } from "svelte";
  import { flip } from "svelte/animate";
  import { scale } from "svelte/transition";
  import { cubicOut } from "svelte/easing";
  import { Search, SortAsc, Zap, ArrowRight, Activity, MessageSquare, Star, Users } from "lucide-svelte";
  import { authFetch } from "./utils.js";
  import { favorites } from "./favorites.js";

  let {
    currentUser = "",
    currentUserDisplayName = null,
    appName = "Frontier",
    onselectagent = () => {},
  } = $props();

  let search = $state("");
  let sortBy = $state("name-asc");
  let allAgents = $state([]);
  let isLoading = $state(true);
  let totalInteractions = $state(null);

  const AGENT_COLORS = ['#6366f1', '#e11d48', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];

  function getAgentColor(agent) {
    // Stable color derived from agent id so it doesn't change on re-render
    return AGENT_COLORS[agent.id % AGENT_COLORS.length];
  }

  const displayName = $derived(currentUserDisplayName || currentUser);

  const projectCount = $derived(new Set(allAgents.map(a => a.project_name).filter(Boolean)).size);

  onMount(async () => {
    try {
      const [agentsRes, statsRes] = await Promise.all([
        authFetch('/me/agents'),
        authFetch('/me/stats'),
      ]);
      if (agentsRes.ok) {
        const data = await agentsRes.json();
        allAgents = data.agents || [];
      }
      if (statsRes.ok) {
        const data = await statsRes.json();
        totalInteractions = data.total_interactions ?? null;
      }
    } catch (e) {
      console.error('Failed to load dashboard data:', e);
    }
    isLoading = false;
  });

  function formatCount(n) {
    if (n >= 1000) return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'k';
    return String(n);
  }

  const filteredAgents = $derived.by(() => {
    const q = search.toLowerCase().trim();
    let result = allAgents.filter((a) => {
      if (!q) return true;
      return (
        (a.name && a.name.toLowerCase().includes(q)) ||
        (a.description && a.description.toLowerCase().includes(q)) ||
        (a.project_name && a.project_name.toLowerCase().includes(q))
      );
    });

    result = [...result].sort((a, b) => {
      // Favorites always float to top
      const aFav = $favorites.includes(a.id) ? 0 : 1;
      const bFav = $favorites.includes(b.id) ? 0 : 1;
      if (aFav !== bFav) return aFav - bFav;

      switch (sortBy) {
        case "name-asc":
          return (a.name || "").localeCompare(b.name || "");
        case "name-desc":
          return (b.name || "").localeCompare(a.name || "");
        case "date":
          return (b.id || 0) - (a.id || 0);
        default:
          return 0;
      }
    });

    return result;
  });


  function handleAgentClick(agentId, projectName) {
    onselectagent({ detail: { agentId, projectName } });
  }

  function getAgentInitial(name) {
    if (!name) return "?";
    return name.charAt(0).toUpperCase();
  }
</script>

<div class="dashboard-container">
  <div class="bg-decoration"></div>

  <div class="dashboard-content">
    <!-- Header -->
    <div class="dashboard-header">
      <div class="header-left">
        <div class="header-label">
          <Activity size={14} />
          <span>Agent Command Center</span>
        </div>
        <h1 class="header-title">{appName} Agents Hub</h1>
        <p class="header-subtitle">
          Discover and interact with AI agents across your organization.
          Select an agent below to start a conversation.
        </p>
      </div>
      <div class="header-stats">
        <div class="stat-card">
          <div class="stat-icon">
            <Zap size={18} />
          </div>
          <div class="stat-info">
            <span class="stat-value">{allAgents.length}</span>
            <span class="stat-label">Available Agents</span>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon interaction-icon">
            <MessageSquare size={18} />
          </div>
          <div class="stat-info">
            <span class="stat-value">{totalInteractions !== null ? formatCount(totalInteractions) : '—'}</span>
            <span class="stat-label">Interactions</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Search & Sort -->
    <div class="search-sort-bar">
      <div class="search-wrapper">
        <div class="search-icon-wrap">
          <Search size={20} />
        </div>
        <input
          class="search-input"
          type="text"
          placeholder="Search agents by name or description..."
          bind:value={search}
        />
      </div>
      <div class="sort-wrapper">
        <SortAsc size={16} />
        <select class="sort-select" bind:value={sortBy}>
          <option value="name-asc">Name A-Z</option>
          <option value="name-desc">Name Z-A</option>
          <option value="date">Newest First</option>
        </select>
      </div>
    </div>

    <!-- Agent Grid -->
    {#if isLoading}
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <p>Loading agents...</p>
      </div>
    {:else if filteredAgents.length > 0}
      <div class="agent-grid">
        {#each filteredAgents as agent (agent.id)}
          <div
            class="agent-card"
            role="button"
            tabindex="0"
            animate:flip={{ duration: 350, easing: cubicOut }}
            in:scale={{ duration: 200, start: 0.92, easing: cubicOut }}
            onclick={() => handleAgentClick(agent.id, agent.project_name)}
            onkeydown={(e) => e.key === 'Enter' && handleAgentClick(agent.id, agent.project_name)}
          >
            <div class="card-top">
              <div
                class="agent-icon"
                style="background-color: {agent._color || getAgentColor(agent)}"
              >
                {#if agent.icon && (agent.icon.startsWith('http') || agent.icon.startsWith('data:'))}
                  <img src={agent.icon} alt={agent.name} class="agent-icon-img" />
                {:else}
                  <span class="agent-initial">{getAgentInitial(agent.name)}</span>
                {/if}
              </div>
              <div class="card-top-right">
                <button
                  class="start-conversation-btn"
                  onclick={(e) => { e.stopPropagation(); handleAgentClick(agent.id, agent.project_name); }}
                >
                  <span class="btn-dot"></span>
                  Start conversation
                  <ArrowRight size={14} />
                </button>
                <button
                  class="card-star {$favorites.includes(agent.id) ? 'card-star-active' : ''}"
                  onclick={(e) => { e.stopPropagation(); favorites.toggle(agent.id); }}
                  title="{$favorites.includes(agent.id) ? 'Remove from favorites' : 'Add to favorites'}"
                >
                  <Star size={22} />
                </button>
              </div>
            </div>

            <div class="card-body">
              <h3 class="agent-name">{agent.name}</h3>

              <p class="agent-description">
                {agent.description || "No description available."}
              </p>
            </div>

            <div class="card-footer">
              <div class="card-stat-box">
                <div class="stat-box-icon stat-box-icon-users">
                  <Users size={16} />
                </div>
                <div class="stat-box-info">
                  <span class="stat-box-value">{formatCount(agent.active_users || 0)}</span>
                  <span class="stat-box-label">Active users</span>
                </div>
              </div>
              <div class="card-stat-box">
                <div class="stat-box-icon stat-box-icon-conversations">
                  <MessageSquare size={16} />
                </div>
                <div class="stat-box-info">
                  <span class="stat-box-value">{formatCount(agent.interactions || 0)}</span>
                  <span class="stat-box-label">Interactions</span>
                </div>
              </div>
            </div>
          </div>
        {/each}
      </div>
    {:else}
      <div class="empty-state">
        <Search size={48} />
        <h3>No agents found</h3>
        <p>
          {#if search}
            No agents match "{search}". Try adjusting your search.
          {:else}
            There are no agents available at this time.
          {/if}
        </p>
      </div>
    {/if}
  </div>
</div>

<style>
  .dashboard-container {
    position: relative;
    width: 100%;
    height: 100%;
    overflow-y: auto;
    overflow-x: hidden;
    background: var(--bg-primary, #020617);
    font-family: var(--font-sans, 'Inter', sans-serif);
  }

  .bg-decoration {
    position: absolute;
    top: -120px;
    right: -120px;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(225, 29, 72, 0.12) 0%, transparent 70%);
    border-radius: 50%;
    filter: blur(80px);
    pointer-events: none;
    z-index: 0;
  }

  .dashboard-content {
    position: relative;
    z-index: 1;
    max-width: 1200px;
    margin: 0 auto;
    padding: 3rem 2rem 4rem;
  }

  /* Header */
  .dashboard-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 2rem;
    margin-bottom: 2.5rem;
  }

  .header-left {
    flex: 1;
    min-width: 0;
  }

  .header-label {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    color: var(--primary-accent, #e11d48);
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.75rem;
  }

  .header-title {
    font-family: var(--font-display, 'Outfit', sans-serif);
    font-size: 2.25rem;
    font-weight: 700;
    color: var(--text-primary, #e2e8f0);
    margin: 0 0 0.75rem 0;
    line-height: 1.2;
  }

  .header-subtitle {
    font-size: 0.95rem;
    color: var(--text-secondary, #94a3b8);
    line-height: 1.6;
    margin: 0;
    max-width: 520px;
  }

  .header-stats {
    display: flex;
    gap: 1rem;
    flex-shrink: 0;
  }

  .stat-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: var(--bg-secondary, var(--bg-elevated));
    border: 1px solid var(--border-color, var(--bg-hover));
    border-radius: var(--radius-xl, 1rem);
    padding: 1rem 1.25rem;
    min-width: 150px;
  }

  .stat-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius-lg, 0.75rem);
    background: rgba(99, 102, 241, 0.15);
    color: #6366f1;
    flex-shrink: 0;
  }

  .interaction-icon {
    background: rgba(225, 29, 72, 0.15);
    color: var(--primary-accent, #e11d48);
  }

  .stat-info {
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }

  .stat-value {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--text-primary, #e2e8f0);
    font-family: var(--font-display, 'Outfit', sans-serif);
  }

  .stat-label {
    font-size: 0.7rem;
    color: var(--text-muted, #64748b);
    text-transform: uppercase;
    letter-spacing: 0.04em;
    font-weight: 500;
  }

  /* Search & Sort */
  .search-sort-bar {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 2rem;
  }

  .search-wrapper {
    position: relative;
    flex: 1;
  }

  .search-icon-wrap {
    position: absolute;
    left: 1.25rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted, #64748b);
    display: flex;
    align-items: center;
    pointer-events: none;
  }

  .search-input {
    width: 100%;
    padding: 1rem 1rem 1rem 3.5rem;
    font-size: 0.95rem;
    font-family: var(--font-sans, 'Inter', sans-serif);
    color: var(--text-primary, #e2e8f0);
    background: var(--bg-secondary, var(--bg-elevated));
    border: 1px solid var(--border-color, var(--bg-hover));
    border-radius: 1rem;
    outline: none;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    box-sizing: border-box;
  }

  .search-input::placeholder {
    color: var(--text-muted, #64748b);
  }

  .search-input:focus {
    border-color: var(--primary-accent, #e11d48);
    box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.1);
  }

  .sort-wrapper {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.85rem 1rem;
    background: var(--bg-secondary, var(--bg-elevated));
    border: 1px solid var(--border-color, var(--bg-hover));
    border-radius: 1rem;
    color: var(--text-secondary, #94a3b8);
    flex-shrink: 0;
  }

  .sort-select {
    background: transparent;
    border: none;
    color: var(--text-secondary, #94a3b8);
    font-size: 0.85rem;
    font-family: var(--font-sans, 'Inter', sans-serif);
    outline: none;
    cursor: pointer;
    padding-right: 0.5rem;
  }

  .sort-select option {
    background: var(--bg-secondary, var(--bg-elevated));
    color: var(--text-primary, #e2e8f0);
  }

  /* Start conversation button */
  .start-conversation-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.5rem 1rem;
    background: var(--primary-accent, #e11d48);
    color: #ffffff;
    border: none;
    border-radius: var(--radius-full, 9999px);
    font-size: 0.8rem;
    font-weight: 600;
    font-family: var(--font-sans, 'Inter', sans-serif);
    cursor: pointer;
    transition: background 0.15s ease, transform 0.1s ease;
    white-space: nowrap;
  }

  .start-conversation-btn:hover {
    background: var(--primary-accent-hover, #d97706);
    transform: translateY(-1px);
  }

  .btn-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.5);
    flex-shrink: 0;
  }

  /* Star button on cards */
  .card-star {
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    color: #cbd5e1;
    cursor: pointer;
    padding: 0.25rem;
    border-radius: var(--radius-md);
    transition: color 0.15s ease, transform 0.1s ease;
  }

  .card-star :global(svg) {
    fill: none;
    transition: fill 0.15s ease, color 0.15s ease;
  }

  .card-star:hover {
    color: #f59e0b;
  }

  .card-star:active {
    transform: scale(1.25);
  }

  .card-star-active {
    color: #f59e0b;
  }

  .card-star-active :global(svg) {
    fill: currentColor;
  }

  /* Agent Grid */
  .agent-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1.5rem;
  }

  @media (max-width: 1024px) {
    .agent-grid {
      grid-template-columns: repeat(2, 1fr);
    }
    .dashboard-header {
      flex-direction: column;
    }
    .header-stats {
      width: 100%;
    }
  }

  @media (max-width: 640px) {
    .agent-grid {
      grid-template-columns: 1fr;
    }
    .dashboard-content {
      padding: 2rem 1rem 3rem;
    }
    .header-title {
      font-size: 1.75rem;
    }
    .search-sort-bar {
      flex-direction: column;
      align-items: stretch;
    }
    .header-stats {
      flex-direction: column;
    }
  }

  /* Agent Card */
  .agent-card {
    display: flex;
    flex-direction: column;
    background: var(--bg-card, var(--bg-secondary));
    border: 1px solid var(--border-color);
    border-radius: var(--radius-3xl, 1.5rem);
    padding: 2rem;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    text-align: left;
    font-family: var(--font-sans, 'Inter', sans-serif);
    color: inherit;
    outline: none;
    width: 100%;
    position: relative;
  }

  .agent-card:hover {
    transform: translateY(-6px);
    box-shadow: 0 20px 40px -12px rgba(225, 29, 72, 0.12), 0 8px 24px -8px rgba(0, 0, 0, 0.15);
  }

  .agent-card:hover .agent-icon {
    transform: scale(1.08);
  }

  .agent-card:focus-visible {
    box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.3);
  }

  .card-top {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 2rem;
  }

  .card-top-right {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .agent-icon {
    width: 56px;
    height: 56px;
    border-radius: var(--radius-xl, 1rem);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: transform 0.5s ease;
    overflow: hidden;
    box-shadow: var(--shadow-md);
  }

  .agent-icon-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .agent-initial {
    font-size: 1.35rem;
    font-weight: 700;
    color: #ffffff;
    font-family: var(--font-display, 'Outfit', sans-serif);
  }

  .loading-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 5rem 2rem;
    gap: 1rem;
    color: var(--text-muted, #64748b);
    font-size: 0.9rem;
  }

  .loading-spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-color, #e5e5e5);
    border-top-color: var(--primary-accent, #e11d48);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .card-body {
    flex: 1;
    margin-bottom: 1.5rem;
  }

  .agent-name {
    font-family: var(--font-display, 'Outfit', sans-serif);
    font-size: 1.35rem;
    font-weight: 700;
    color: var(--text-primary, #0f0f0f);
    margin: 0 0 0.25rem 0;
    line-height: 1.3;
  }


  .agent-description {
    font-size: 0.875rem;
    color: var(--text-secondary, #6b6b6b);
    line-height: 1.5;
    margin: 0;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  /* Card footer stats */
  .card-footer {
    display: flex;
    gap: 0.75rem;
    margin-top: auto;
    padding-top: 1.25rem;
    border-top: 1px solid var(--border-color, #e5e5e5);
  }

  .card-stat-box {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.75rem;
    background: var(--bg-secondary, #f9f9fa);
    border-radius: var(--radius-lg, 0.75rem);
  }

  .stat-box-icon {
    width: 36px;
    height: 36px;
    border-radius: var(--radius-md, 0.5rem);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .stat-box-icon-users {
    background: rgba(16, 185, 129, 0.12);
    color: #10b981;
  }

  .stat-box-icon-conversations {
    background: rgba(59, 130, 246, 0.12);
    color: #3b82f6;
  }

  .stat-box-info {
    display: flex;
    flex-direction: column;
    gap: 0;
  }

  .stat-box-value {
    font-size: 1.1rem;
    font-weight: 700;
    color: var(--text-primary, #0f0f0f);
    font-family: var(--font-display, 'Outfit', sans-serif);
    line-height: 1.2;
  }

  .stat-box-label {
    font-size: 0.7rem;
    color: var(--text-secondary, #6b6b6b);
    font-weight: 400;
  }

  /* Empty State */
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-muted, #64748b);
  }

  .empty-state h3 {
    font-family: var(--font-display, 'Outfit', sans-serif);
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-secondary, #94a3b8);
    margin: 1.25rem 0 0.5rem;
  }

  .empty-state p {
    font-size: 0.9rem;
    color: var(--text-muted, #64748b);
    margin: 0;
    max-width: 360px;
    line-height: 1.5;
  }
</style>
