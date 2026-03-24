<script>
  import { Menu, ChevronRight, Bell, UserCircle, LogOut, Sun, Moon } from "lucide-svelte";

  let {
    appName = "Frontier",
    activeAgentName = null,
    currentUser = "",
    currentUserDisplayName = null,
    currentTheme = "dark",
    projectDescription = null,
    ontoggleSidebar = () => {},
    onnavigatehome = () => {},
    onlogout = () => {},
    ontoggletTheme = () => {},
  } = $props();

  const displayName = $derived(currentUserDisplayName || currentUser);
</script>

<div class="topbar">
  <!-- Left: hamburger + breadcrumbs -->
  <div class="topbar-left">
    <button class="icon-btn" onclick={ontoggleSidebar} title="Toggle sidebar">
      <Menu size={20} />
    </button>

    <nav class="breadcrumbs">
      <button class="crumb crumb-link" onclick={onnavigatehome}>
        {appName}
      </button>
      <ChevronRight size={14} class="chevron" />
      <button
        class="crumb {activeAgentName ? 'crumb-link' : 'crumb-active'}"
        onclick={onnavigatehome}
      >
        Agents
      </button>
      {#if activeAgentName}
        <ChevronRight size={14} class="chevron" />
        <span class="crumb-pill">{activeAgentName}</span>
      {/if}
    </nav>
  </div>

  <!-- Right: notifications + user + logout -->
  <div class="topbar-right">
    <button class="icon-btn theme-btn" onclick={ontoggletTheme} title="Toggle theme">
      {#if currentTheme === 'dark'}
        <Sun size={18} />
      {:else}
        <Moon size={18} />
      {/if}
    </button>

    <button class="icon-btn bell-btn" title="Notifications">
      <Bell size={20} />
      <span class="notification-dot"></span>
    </button>

    <div class="divider"></div>

    <div class="user-profile">
      <div class="user-info">
        <span class="user-name">{displayName}</span>
        {#if projectDescription}
          <span class="user-role">{projectDescription}</span>
        {/if}
      </div>
      <div class="avatar">
        <UserCircle size={22} />
      </div>
    </div>

    <button class="icon-btn logout-btn" onclick={onlogout} title="Sign out">
      <LogOut size={20} />
    </button>
  </div>
</div>

<style>
  .topbar {
    height: 80px;
    flex-shrink: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 2rem;
    background: var(--bg-primary);
    border-bottom: 1px solid var(--border-color);
    z-index: 20;
  }

  .topbar-left {
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .topbar-right {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  /* Icon button base */
  .icon-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: var(--radius-xl);
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: background 0.15s ease, color 0.15s ease;
  }

  .icon-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  /* Bell with notification dot */
  .bell-btn {
    position: relative;
  }

  .notification-dot {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 8px;
    height: 8px;
    background: var(--primary-accent);
    border-radius: 50%;
    border: 2px solid var(--bg-primary);
  }

  /* Logout hover is rose */
  .logout-btn:hover {
    background: rgba(225, 29, 72, 0.1);
    color: #fb7185;
  }

  /* Breadcrumbs */
  .breadcrumbs {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .crumb {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0;
    transition: color 0.15s ease;
  }

  .crumb-link {
    color: var(--text-secondary);
  }

  .crumb-link:hover {
    color: var(--primary-accent-hover);
  }

  .crumb-active {
    color: var(--text-primary);
  }

  .crumb-pill {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #fb7185;
    background: rgba(225, 29, 72, 0.1);
    border: 1px solid rgba(225, 29, 72, 0.2);
    padding: 3px 10px;
    border-radius: var(--radius-full);
  }

  .breadcrumbs :global(.chevron) {
    color: var(--border-strong);
    flex-shrink: 0;
  }

  /* Divider */
  .divider {
    width: 1px;
    height: 32px;
    background: var(--border-color);
    margin: 0 0.5rem;
  }

  /* User profile */
  .user-profile {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0 0.5rem;
    cursor: pointer;
  }

  .user-info {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
  }

  .user-name {
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1.2;
  }

  .user-role {
    font-size: 10px;
    font-weight: 700;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }

  .avatar {
    width: 40px;
    height: 40px;
    border-radius: var(--radius-2xl);
    background: var(--bg-hover);
    border: 1px solid var(--border-strong);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    transition: border-color 0.15s ease, background 0.15s ease;
  }

  .user-profile:hover .avatar {
    border-color: rgba(99, 102, 241, 0.3);
    background: rgba(99, 102, 241, 0.1);
    color: #818cf8;
  }

  @media (max-width: 640px) {
    .user-info {
      display: none;
    }
    .breadcrumbs .crumb-pill {
      display: none;
    }
  }
</style>
