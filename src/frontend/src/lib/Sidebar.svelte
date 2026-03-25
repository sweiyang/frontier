<script>
  import { onMount } from "svelte";
  import { slide, fade } from "svelte/transition";
  import { authFetch, authPost } from "./utils.js";
  import ContactUs from "./ContactUs.svelte";
  import {
    LayoutGrid,
    Plus,
    Search,
    Settings,
    HelpCircle,
    MessageSquare,
    ChevronDown,
    Sparkles,
    LogOut,
    Wrench,
    ShieldAlert,
    Star,
    Network,
    FolderOpen,
    Mail,
  } from "lucide-svelte";
  import { favorites } from "./favorites.js";

  let {
    currentUser = "User",
    currentUserDisplayName = null,
    currentConversationId = null,
    currentProject = null,
    currentRoute = "chat",
    appName = "Frontier",
    logoUrl = null,
    contact = {},
    faq = {},
    onlogout = () => {},
    onselectconversation = () => {},
    onnewconversation = () => {},
    onnavigate = () => {},
    onclearfilter = () => {},
    showChat = true,
    filterAgentId = null,
    isOpen = true,
    isPlatformOwner = false,
    isPlatformAdmin = false,
    hasWorkbenchAccess = false,
    onSelectAgent = () => {},
    activeAgentId = null,
    agents = [],
  } = $props();

  const displayName = $derived(currentUserDisplayName || currentUser);

  let conversations = $state([]);
  let globalSearch = $state("");
  let localSearch = $state("");
  let showContactModal = $state(false);
  let isDropdownOpen = $state(false);
  let isFavoritesOpen = $state(true);
  let searchFocusedIndex = $state(-1);

  // Check if any contact method is available
  const hasContactMethods = $derived(
    (contact?.email?.enabled && contact?.email?.address) ||
    (contact?.jira?.enabled && contact?.jira?.url)
  );

  const hasFaq = $derived(faq?.enabled && faq?.url);

  const favoriteAgents = $derived(agents.filter(a => a.is_site ? $favorites.includes(`site-${a.project_id}`) : $favorites.includes(a.id)));

  const activeAgent = $derived(activeAgentId != null ? agents.find(a => a.id === activeAgentId) || null : null);

  // Global search over conversation titles
  const globalResults = $derived(
    globalSearch.trim()
      ? conversations.filter(c => c.title?.toLowerCase().includes(globalSearch.toLowerCase()))
      : []
  );

  // Local chat history for the active agent
  const localChats = $derived(
    activeAgentId
      ? conversations.filter(c => c.agent_id === activeAgentId &&
          c.title?.toLowerCase().includes(localSearch.toLowerCase()))
      : []
  );

  export async function refreshConversations() {
    await loadConversations();
  }

  onMount(async () => {
    await loadConversations();

    const handleClickOutside = (event) => {
      if (!event.target.closest(".agent-dropdown-wrapper")) {
        isDropdownOpen = false;
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  });

  async function loadConversations() {
    if (!currentProject) return;
    try {
      let url = "/conversations";
      if (filterAgentId) url += `?agent_id=${filterAgentId}`;
      const response = await authFetch(url);
      if (response.ok) {
        const data = await response.json();
        conversations = data.conversations || [];
      }
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  }

  $effect(() => {
    filterAgentId;
    loadConversations();
  });

  async function createNewConversation() {
    try {
      const response = await authPost("/conversations", { agent_id: filterAgentId || activeAgentId });
      if (response.ok) {
        const data = await response.json();
        conversations = [data, ...conversations];
        onnewconversation({ detail: { conversationId: data.id } });
      }
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
  }

  function selectConversation(convId) {
    onselectconversation({ detail: { conversationId: convId } });
  }

  function handleWorkbench() {
    onnavigate({ detail: { route: "workbench" } });
  }

  function handleAdmin() {
    onnavigate({ detail: { route: "admin" } });
  }

  function handleArtefacts() {
    onnavigate({ detail: { route: "artefacts" } });
  }

  function handleSettings() {
    // navigate to workbench for settings
    onnavigate({ detail: { route: "workbench" } });
  }

  function handleContactUs() {
    showContactModal = true;
  }

  function handleHelp() {
    if (hasFaq) {
      window.open(faq.url, "_blank");
    }
  }

  function handleSelectAllAgents() {
    onnavigate({ detail: { route: "chat" } });
    onSelectAgent(null);
    onclearfilter();
  }
</script>

<aside class="sidebar" class:collapsed={!isOpen}>
  <!-- Header: logo + name -->
  <div class="sidebar-header">
    <div class="logo-icon">
      {#if logoUrl}
        <img src={logoUrl} alt={appName} style="width:100%;height:100%;object-fit:cover;border-radius:inherit;" />
      {:else}
        <Network size={22} color="white" />
      {/if}
    </div>
    {#if isOpen}
      <span class="brand-name" transition:fade={{ duration: 120 }}>{appName}</span>
    {/if}
  </div>

  <!-- Global navigation -->
  <div class="sidebar-nav" class:centered={!isOpen}>
    <!-- All Agents button -->
    <button
      class="nav-btn {!activeAgentId ? 'nav-btn-active' : ''}"
      class:icon-only={!isOpen}
      onclick={handleSelectAllAgents}
      title={!isOpen ? "All Agents" : ""}
    >
      <LayoutGrid size={isOpen ? 18 : 22} />
      {#if isOpen}<span>All Agents</span>{/if}
    </button>

    <!-- Favorites section -->
    {#if favoriteAgents.length > 0}
      <div class="favorites-section">
        {#if isOpen}
          <button
            class="section-header-btn"
            onclick={() => isFavoritesOpen = !isFavoritesOpen}
          >
            <span>Favorites</span>
            <ChevronDown size={12} class="chevron {isFavoritesOpen ? 'rotated' : ''}" />
          </button>
          {#if isFavoritesOpen}
            <div transition:slide={{ duration: 150 }}>
              {#each favoriteAgents as agent}
                <div class="agent-btn-row">
                  <button
                    class="agent-btn {activeAgentId === agent.id ? 'agent-btn-active' : ''}"
                    onclick={() => {
                      if (agent.is_site) {
                        window.history.pushState({}, "", `/${agent.project_name}`);
                        window.dispatchEvent(new PopStateEvent("popstate"));
                      } else {
                        onSelectAgent(agent.id, agent.project_name);
                      }
                    }}
                  >
                    <div class="agent-icon-sm" style="background: {agent.is_site ? '#10b981' : (agent._color || '#6366f1')}">
                      {#if agent.is_site}
                        <span style="font-size:10px;">🌐</span>
                      {:else if agent.icon}
                        <img src={agent.icon} alt="" />
                      {:else}
                        <span>{(agent.name || 'A').charAt(0).toUpperCase()}</span>
                      {/if}
                    </div>
                    <span class="agent-btn-name">{agent.name}</span>
                  </button>
                  <button
                    class="star-btn star-btn-active"
                    onclick={(e) => { e.stopPropagation(); favorites.toggle(agent.is_site ? `site-${agent.project_id}` : agent.id); }}
                    title="Remove from favorites"
                  >
                    <Star size={12} />
                  </button>
                </div>
              {/each}
            </div>
          {/if}
        {:else}
          <div class="favorites-icons">
            {#each favoriteAgents as agent}
              <button
                class="fav-icon-btn {activeAgentId === agent.id ? 'fav-icon-active' : ''}"
                onclick={() => onSelectAgent(agent.id, agent.project_name)}
                title={agent.name}
              >
                <div class="agent-icon-sm" style="background: {agent._color || '#6366f1'}">
                  {#if agent.icon}
                    <img src={agent.icon} alt="" />
                  {:else}
                    <span>{(agent.name || 'A').charAt(0).toUpperCase()}</span>
                  {/if}
                </div>
              </button>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Global search -->
    {#if isOpen && showChat}
      <div class="search-wrapper">
        <Search size={14} class="search-icon" />
        <input
          type="text"
          placeholder="Search all chats..."
          bind:value={globalSearch}
          class="search-input"
          aria-label="Search all chats"
          aria-controls="search-results-dropdown"
          aria-expanded={!!globalSearch}
          onkeydown={(e) => {
            if (!globalResults.length) return;
            if (e.key === 'ArrowDown') {
              e.preventDefault();
              searchFocusedIndex = (searchFocusedIndex + 1) % globalResults.length;
            } else if (e.key === 'ArrowUp') {
              e.preventDefault();
              searchFocusedIndex = (searchFocusedIndex - 1 + globalResults.length) % globalResults.length;
            } else if (e.key === 'Enter' && searchFocusedIndex >= 0) {
              e.preventDefault();
              const chat = globalResults[searchFocusedIndex];
              if (chat) { selectConversation(chat.id); globalSearch = ""; searchFocusedIndex = -1; }
            } else if (e.key === 'Escape') {
              globalSearch = "";
              searchFocusedIndex = -1;
            }
          }}
        />
        {#if globalSearch}
          <div id="search-results-dropdown" class="search-dropdown" role="listbox" aria-label="Search results" transition:slide={{ duration: 120 }}>
            <div class="search-results-label">Global Results</div>
            {#if globalResults.length > 0}
              {#each globalResults as chat, idx}
                <button
                  class="search-result-item"
                  class:focused={searchFocusedIndex === idx}
                  role="option"
                  aria-selected={searchFocusedIndex === idx}
                  onclick={() => { selectConversation(chat.id); globalSearch = ""; searchFocusedIndex = -1; }}
                >
                  <span class="search-result-title">{chat.title}</span>
                  <span class="search-result-meta">
                    <MessageSquare size={10} />
                    {chat.time || ""}
                  </span>
                </button>
              {/each}
            {:else}
              <div class="search-empty">No matching chats found.</div>
            {/if}
          </div>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Contextual area: active agent history -->
  <div class="sidebar-context" class:centered={!isOpen}>
    {#if activeAgent}
      <div class="context-section">
        {#if isOpen}
          <span class="context-label">Active</span>
        {/if}

        <!-- Agent selector dropdown -->
        <div class="agent-dropdown-wrapper">
          <button
            class="agent-selector {!isOpen ? 'icon-only-selector' : ''}"
            onclick={() => isOpen && (isDropdownOpen = !isDropdownOpen)}
            title={!isOpen ? activeAgent.name : ""}
            aria-haspopup="listbox"
            aria-expanded={isDropdownOpen}
            aria-label="Select agent"
          >
            <div class="agent-icon-md" style="background: {activeAgent._color || '#6366f1'}">
              {#if activeAgent.icon}
                <img src={activeAgent.icon} alt="" />
              {:else}
                <span>{(activeAgent.name || 'A').charAt(0).toUpperCase()}</span>
              {/if}
            </div>
            {#if isOpen}
              <span class="agent-selector-name">{activeAgent.name}</span>
              <ChevronDown size={14} class="chevron {isDropdownOpen ? 'rotated' : ''}" />
            {/if}
          </button>

          {#if isOpen && isDropdownOpen}
            <div class="agent-dropdown" role="listbox" aria-label="Available agents" transition:slide={{ duration: 120 }}>
              {#each agents as agent}
                <div class="dropdown-item-row" role="option" aria-selected={activeAgentId === agent.id}>
                  <button
                    class="dropdown-item {activeAgentId === agent.id ? 'dropdown-item-active' : ''}"
                    onclick={() => {
                      if (agent.is_site) {
                        window.history.pushState({}, "", `/${agent.project_name}`);
                        window.dispatchEvent(new PopStateEvent("popstate"));
                      } else {
                        onSelectAgent(agent.id, agent.project_name);
                      }
                      isDropdownOpen = false;
                    }}
                  >
                    <div class="agent-icon-sm" style="background: {agent.is_site ? '#10b981' : (agent._color || '#6366f1')}">
                      {#if agent.is_site}
                        <span style="font-size:10px;">🌐</span>
                      {:else if agent.icon}
                        <img src={agent.icon} alt="" />
                      {:else}
                        <span>{(agent.name || 'A').charAt(0).toUpperCase()}</span>
                      {/if}
                    </div>
                    <span>{agent.name}</span>
                    {#if agent.is_site}
                      <span class="sidebar-site-badge">Site</span>
                    {/if}
                  </button>
                </div>
              {/each}
            </div>
          {/if}
        </div>

        {#if isOpen && showChat}
          <!-- Chat history section -->
          <div class="history-header">
            <span class="context-label">History</span>
            <button class="icon-action-btn" onclick={createNewConversation} title="New chat">
              <Plus size={14} />
            </button>
          </div>

          <div class="search-wrapper search-wrapper-sm">
            <Search size={12} class="search-icon" />
            <input
              type="text"
              placeholder="Filter chats..."
              bind:value={localSearch}
              class="search-input"
            />
          </div>

          <div class="chat-history">
            {#if localChats.length > 0}
              {#each localChats.slice(0, 10) as chat}
                <button
                  class="history-item {currentConversationId === chat.id ? 'history-item-active' : ''}"
                  onclick={() => selectConversation(chat.id)}
                >
                  <div class="history-icon">
                    <MessageSquare size={14} />
                  </div>
                  <div class="history-info">
                    <span class="history-title">{chat.title || "New chat"}</span>
                    <span class="history-time">{chat.time || ""}</span>
                  </div>
                </button>
              {/each}
            {:else}
              <div class="history-empty">No history for this agent.</div>
            {/if}
          </div>
        {/if}
      </div>
    {:else}
      <!-- Empty state -->
      <div class="context-empty">
        <div class="empty-icon {!isOpen ? 'empty-icon-sm' : ''}">
          <Sparkles size={isOpen ? 28 : 18} />
        </div>
        {#if isOpen}
          <p class="empty-text">Select Agent<br />to Begin</p>
        {/if}
      </div>
    {/if}
  </div>

  <!-- Footer utilities -->
  <div class="sidebar-footer" class:footer-collapsed={!isOpen}>
    {#if hasWorkbenchAccess}
      <button
        class="footer-btn {!isOpen ? 'icon-only' : ''}"
        onclick={handleWorkbench}
        title={!isOpen ? "Workbench" : ""}
      >
        <ShieldAlert size={isOpen ? 18 : 22} />
        {#if isOpen}<span>Workbench</span>{/if}
      </button>
    {/if}
    {#if isPlatformAdmin}
      <button
        class="footer-btn {!isOpen ? 'icon-only' : ''}"
        onclick={handleAdmin}
        title={!isOpen ? "Admin" : ""}
      >
        <Wrench size={isOpen ? 18 : 22} />
        {#if isOpen}<span>Admin</span>{/if}
      </button>
    {/if}
    {#if hasContactMethods}
      <button
        class="footer-btn {!isOpen ? 'icon-only' : ''}"
        onclick={handleContactUs}
        title={!isOpen ? "Contact Us" : ""}
      >
        <Mail size={isOpen ? 18 : 22} />
        {#if isOpen}<span>Contact Us</span>{/if}
      </button>
    {/if}
    <button
      class="footer-btn {!isOpen ? 'icon-only' : ''}"
      onclick={handleSettings}
      title={!isOpen ? "Settings" : ""}
    >
      <Settings size={isOpen ? 18 : 22} />
      {#if isOpen}<span>Settings</span>{/if}
    </button>
    {#if hasFaq}
      <button
        class="footer-btn {!isOpen ? 'icon-only' : ''}"
        onclick={handleHelp}
        title={!isOpen ? "Help Centre" : ""}
      >
        <HelpCircle size={isOpen ? 18 : 22} />
        {#if isOpen}<span>Help Centre</span>{/if}
      </button>
    {/if}
  </div>
</aside>

{#if showContactModal}
  <ContactUs {contact} onclose={() => showContactModal = false} />
{/if}

<style>
  .sidebar {
    width: 280px;
    min-width: 280px;
    height: 100%;
    display: flex;
    flex-direction: column;
    background: var(--bg-primary);
    border-right: 1px solid var(--border-color);
    transition: width 0.3s ease, min-width 0.3s ease;
    overflow: hidden;
    z-index: 30;
  }

  .sidebar.collapsed {
    width: 80px;
    min-width: 80px;
  }

  @media (max-width: 768px) {
    .sidebar {
      display: none;
    }
  }

  /* Header */
  .sidebar-header {
    height: 80px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    padding: 0 1.5rem;
    gap: 0.75rem;
  }

  .sidebar.collapsed .sidebar-header {
    justify-content: center;
    padding: 0;
  }

  .logo-icon {
    width: 40px;
    height: 40px;
    min-width: 40px;
    background: var(--primary-accent);
    border-radius: var(--radius-xl);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(225, 29, 72, 0.2);
    overflow: hidden;
  }

  .brand-name {
    font-family: var(--font-display);
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
    white-space: nowrap;
    letter-spacing: -0.01em;
  }

  /* Navigation */
  .sidebar-nav {
    padding: 0.75rem 1rem 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    flex-shrink: 0;
  }

  .sidebar-nav.centered {
    align-items: center;
    padding: 0.75rem 0.5rem 0.5rem;
  }

  .nav-btn {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 0.6rem 1rem;
    border-radius: var(--radius-2xl);
    border: none;
    background: transparent;
    color: var(--text-muted);
    font-size: 0.875rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
    white-space: nowrap;
  }

  .nav-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .nav-btn-active {
    background: rgba(225, 29, 72, 0.1);
    color: #fb7185;
    border: 1px solid rgba(225, 29, 72, 0.2);
  }

  .nav-btn.icon-only {
    width: 48px;
    height: 48px;
    padding: 0;
    justify-content: center;
    border-radius: var(--radius-xl);
  }

  /* Favorites */
  .favorites-section {
    display: flex;
    flex-direction: column;
    gap: 2px;
    width: 100%;
  }

  .section-header-btn {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    padding: 0.4rem 1rem;
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-muted);
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.2em;
    transition: color 0.12s ease;
  }

  .section-header-btn:hover {
    color: var(--text-secondary);
  }

  .section-header-btn :global(.chevron) {
    transition: transform 0.3s ease;
  }

  .section-header-btn :global(.chevron.rotated) {
    transform: rotate(180deg);
  }

  .agent-btn {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    width: 100%;
    padding: 0.5rem 1rem;
    border-radius: var(--radius-xl);
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
  }

  .agent-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .agent-btn-active {
    background: rgba(225, 29, 72, 0.1);
    color: #fb7185;
    font-weight: 700;
  }

  .agent-btn-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: left;
  }

  .agent-btn-row {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    padding-right: 0.5rem;
  }

  .agent-btn-row .agent-btn {
    flex: 1;
    min-width: 0;
  }

  .favorites-icons {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    padding: 0.25rem 0;
  }

  .fav-icon-btn {
    padding: 0.6rem;
    border-radius: var(--radius-xl);
    border: none;
    background: transparent;
    cursor: pointer;
    transition: background 0.12s ease;
  }

  .fav-icon-btn:hover {
    background: var(--bg-hover);
  }

  .fav-icon-active {
    background: rgba(225, 29, 72, 0.1);
  }

  /* Agent icon sizes */
  .agent-icon-sm {
    width: 28px;
    height: 28px;
    min-width: 28px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    font-size: 0.75rem;
    font-weight: 700;
    color: white;
    background: var(--agent-color-1, #6366f1);
  }

  .agent-icon-sm img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .agent-icon-md {
    width: 34px;
    height: 34px;
    min-width: 34px;
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    font-size: 0.875rem;
    font-weight: 700;
    color: white;
    box-shadow: var(--shadow-sm);
    background: var(--agent-color-1, #6366f1);
  }

  .agent-icon-md img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  /* Search */
  .search-wrapper {
    position: relative;
    width: 100%;
  }

  .search-wrapper-sm {
    margin-top: 0.25rem;
  }

  .search-wrapper :global(.search-icon) {
    position: absolute;
    left: 0.875rem;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-muted);
    pointer-events: none;
  }

  .search-input {
    width: 100%;
    padding: 0.6rem 1rem 0.6rem 2.25rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-2xl);
    color: var(--text-primary);
    font-size: 0.8rem;
    font-weight: 500;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;
    font-family: inherit;
  }

  .search-input::placeholder {
    color: var(--text-muted);
  }

  .search-input:focus {
    outline: none;
    border-color: rgba(225, 29, 72, 0.3);
    box-shadow: 0 0 0 2px rgba(225, 29, 72, 0.05);
  }

  .search-dropdown {
    position: absolute;
    top: calc(100% + 8px);
    left: 0;
    right: 0;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-2xl);
    box-shadow: var(--shadow-lg);
    z-index: 50;
    max-height: 300px;
    overflow-y: auto;
    padding: 0.5rem 0;
  }

  .search-results-label {
    font-size: 10px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.2em;
    padding: 0.4rem 1rem;
  }

  .search-result-item {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    width: 100%;
    text-align: left;
    padding: 0.6rem 1rem;
    border: none;
    background: transparent;
    cursor: pointer;
    border-left: 3px solid transparent;
    transition: background 0.12s ease, border-color 0.12s ease;
  }

  .search-result-item:hover,
  .search-result-item.focused {
    background: var(--accent-glow);
    border-left-color: var(--primary-accent);
  }

  .search-result-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .search-result-meta {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 10px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .search-empty {
    padding: 1rem;
    text-align: center;
    font-size: 0.8rem;
    color: var(--text-muted);
    font-style: italic;
  }

  /* Contextual section */
  .sidebar-context {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem 1rem;
    min-height: 0;
  }

  .sidebar-context.centered {
    padding: 0.5rem;
    display: flex;
    align-items: flex-start;
    justify-content: center;
  }

  .sidebar-context::-webkit-scrollbar {
    width: 3px;
  }

  .sidebar-context::-webkit-scrollbar-track {
    background: transparent;
  }

  .sidebar-context::-webkit-scrollbar-thumb {
    background: var(--border-strong);
    border-radius: 2px;
  }

  .context-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .context-label {
    font-size: 10px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.2em;
    padding: 0 0.25rem;
  }

  /* Agent selector */
  .agent-dropdown-wrapper {
    position: relative;
  }

  .agent-selector {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    width: 100%;
    padding: 0.6rem 0.875rem;
    background: var(--bg-elevated);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-2xl);
    cursor: pointer;
    transition: border-color 0.15s ease;
  }

  .agent-selector:hover {
    border-color: rgba(225, 29, 72, 0.3);
  }

  .agent-selector.icon-only-selector {
    width: 48px;
    height: 48px;
    padding: 0;
    justify-content: center;
    border-radius: var(--radius-xl);
  }

  .agent-selector-name {
    flex: 1;
    font-size: 0.875rem;
    font-weight: 700;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: left;
  }

  .agent-selector :global(.chevron) {
    color: var(--text-muted);
    flex-shrink: 0;
    transition: transform 0.3s ease;
  }

  .agent-selector :global(.chevron.rotated) {
    transform: rotate(180deg);
  }

  .agent-dropdown {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    right: 0;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-2xl);
    box-shadow: var(--shadow-lg);
    z-index: 20;
    padding: 0.4rem 0;
    max-height: 250px;
    overflow-y: auto;
  }

  .dropdown-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    width: 100%;
    padding: 0.6rem 1rem;
    border: none;
    background: transparent;
    cursor: pointer;
    color: var(--text-secondary);
    font-size: 0.875rem;
    transition: background 0.12s ease, color 0.12s ease;
  }

  .dropdown-item:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .dropdown-item-active {
    background: rgba(225, 29, 72, 0.1);
    color: #fb7185;
    font-weight: 700;
  }

  .dropdown-item-row {
    display: flex;
    align-items: center;
  }

  .dropdown-item-row .dropdown-item {
    flex: 1;
    min-width: 0;
  }

  .sidebar-site-badge {
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: #10b981;
    background: rgba(16, 185, 129, 0.1);
    padding: 0.1rem 0.4rem;
    border-radius: var(--radius-full, 9999px);
    margin-left: auto;
  }

  .star-btn {
    flex-shrink: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    background: transparent;
    color: var(--text-muted);
    border-radius: var(--radius-sm);
    cursor: pointer;
    opacity: 0;
    transition: opacity 0.12s ease, color 0.12s ease, background 0.12s ease;
  }

  .agent-btn-row:hover .star-btn,
  .dropdown-item-row:hover .star-btn {
    opacity: 1;
  }

  .star-btn:hover {
    background: var(--bg-hover);
    color: var(--primary-accent);
  }

  .star-btn-active {
    opacity: 1;
    color: var(--primary-accent) !important;
  }

  .star-btn-active :global(svg) {
    fill: var(--primary-accent);
  }

  /* History */
  .history-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.25rem 0.25rem 0;
  }

  .icon-action-btn {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 6px;
    border: none;
    background: transparent;
    color: var(--primary-accent);
    cursor: pointer;
    transition: background 0.12s ease;
  }

  .icon-action-btn:hover {
    background: rgba(225, 29, 72, 0.1);
  }

  .chat-history {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin-top: 0.25rem;
  }

  .history-item {
    display: flex;
    align-items: flex-start;
    gap: 0.6rem;
    width: 100%;
    padding: 0.6rem 0.75rem;
    border-radius: var(--radius-2xl);
    border: 1px solid transparent;
    background: transparent;
    cursor: pointer;
    transition: background 0.12s ease, border-color 0.12s ease;
  }

  .history-item:hover {
    background: var(--bg-hover);
    border-color: var(--border-color);
  }

  .history-item-active {
    background: rgba(225, 29, 72, 0.08);
    border-color: rgba(225, 29, 72, 0.15);
  }

  .history-icon {
    width: 28px;
    height: 28px;
    min-width: 28px;
    border-radius: var(--radius-lg);
    background: var(--bg-hover);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    transition: background 0.12s ease, color 0.12s ease;
  }

  .history-item:hover .history-icon,
  .history-item-active .history-icon {
    background: rgba(225, 29, 72, 0.1);
    color: #fb7185;
  }

  .history-info {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
    min-width: 0;
    flex: 1;
  }

  .history-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: left;
    transition: color 0.12s ease;
  }

  .history-item:hover .history-title,
  .history-item-active .history-title {
    color: var(--text-primary);
  }

  .history-time {
    font-size: 10px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    text-align: left;
  }

  .history-empty {
    font-size: 0.8rem;
    color: var(--text-muted);
    text-align: center;
    padding: 2rem 0.5rem;
    background: var(--bg-elevated);
    border-radius: var(--radius-2xl);
    border: 2px dashed var(--border-color);
    font-style: italic;
  }

  /* Empty state */
  .context-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 120px;
    gap: 1rem;
  }

  .empty-icon {
    width: 56px;
    height: 56px;
    background: var(--bg-elevated);
    border-radius: var(--radius-2xl);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    opacity: 0.5;
  }

  .empty-icon-sm {
    width: 40px;
    height: 40px;
    border-radius: var(--radius-xl);
  }

  .empty-text {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
    text-align: center;
    line-height: 1.6;
  }

  /* Footer */
  .sidebar-footer {
    border-top: 1px solid var(--border-color);
    flex-shrink: 0;
    padding: 0.75rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .sidebar-footer.footer-collapsed {
    padding: 0.75rem 0.5rem;
    align-items: center;
  }

  .footer-btn {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    width: 100%;
    padding: 0.5rem 0.875rem;
    border-radius: var(--radius-xl);
    border: none;
    background: transparent;
    color: var(--text-muted);
    font-size: 0.875rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
    white-space: nowrap;
  }

  .footer-btn :global(svg) {
    color: var(--text-secondary);
    flex-shrink: 0;
  }

  .footer-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .footer-btn.icon-only {
    width: 44px;
    height: 44px;
    padding: 0;
    justify-content: center;
    border-radius: var(--radius-xl);
  }

  .footer-btn-admin {
    background: rgba(245, 158, 11, 0.05);
    border: 1px solid rgba(245, 158, 11, 0.15);
    color: #b45309;
    margin-bottom: 0.25rem;
  }

  .footer-btn-admin :global(svg) {
    color: #d97706;
  }

  .footer-btn-admin:hover {
    background: rgba(245, 158, 11, 0.1);
  }

  .footer-btn-logout:hover {
    color: #fb7185;
  }

  .footer-btn-logout:hover :global(svg) {
    color: #fb7185;
  }
</style>
