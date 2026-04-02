<script>
  import { onMount } from "svelte";
  import { Menu, ChevronRight, UserCircle, LogOut, Sun, Moon, Bell, Megaphone } from "lucide-svelte";

  let {
    appName = "Frontier AI",
    activeAgentName = null,
    currentUser = "",
    currentUserDisplayName = null,
    currentTheme = "dark",
    projectDescription = null,
    ontoggleSidebar = () => {},
    onnavigatehome = () => {},
    onlogout = () => {},
    ontoggletTheme = () => {},
    showViewSwitcher = false,
    viewMode = "site",
    onToggleViewMode = () => {},
    banners = [],
    bannersDismissed = false,
    onrestorebanners = () => {},
  } = $props();

  const displayName = $derived(currentUserDisplayName || currentUser);
  let notifPanelOpen = $state(false);

  function toggleNotifPanel() {
    notifPanelOpen = !notifPanelOpen;
  }

  function handleRestore() {
    onrestorebanners();
    notifPanelOpen = false;
  }

  onMount(() => {
    const handleClickOutside = (e) => {
      if (notifPanelOpen && !e.target.closest(".notif-wrapper")) {
        notifPanelOpen = false;
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  });
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

    {#if showViewSwitcher}
      <div class="view-switcher">
        <button
          class="view-switch-btn {viewMode === 'site' ? 'active' : ''}"
          onclick={() => onToggleViewMode('site')}
        >
          Site
        </button>
        <button
          class="view-switch-btn {viewMode === 'chat' ? 'active' : ''}"
          onclick={() => onToggleViewMode('chat')}
        >
          Chat
        </button>
      </div>
    {/if}
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

    {#if banners.length > 0}
      <div class="notif-wrapper">
        <button class="icon-btn bell-btn" onclick={toggleNotifPanel} title="Announcements">
          <Bell size={20} />
          {#if bannersDismissed}
            <span class="notif-dot"></span>
          {/if}
        </button>

        {#if notifPanelOpen}
          <div class="notif-panel">
            <div class="notif-header">
              <span class="notif-title">Announcements</span>
              <span class="notif-count">{banners.length}</span>
            </div>
            <div class="notif-list">
              {#each banners as banner}
                <button class="notif-item" onclick={handleRestore}>
                  <div class="notif-item-icon" style="background: {banner.tag_color || '#ED1C24'}15; color: {banner.tag_color || '#ED1C24'};">
                    <Megaphone size={14} />
                  </div>
                  <div class="notif-item-body">
                    <span class="notif-item-tag" style="color: {banner.tag_color || '#ED1C24'};">{banner.tag}</span>
                    <span class="notif-item-message">{banner.message}</span>
                  </div>
                </button>
              {/each}
            </div>
            {#if bannersDismissed}
              <div class="notif-footer">
                <button class="notif-restore-btn" onclick={handleRestore}>Show announcements</button>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/if}

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

  /* Bell + notification panel */
  .notif-wrapper {
    position: relative;
  }

  .bell-btn {
    position: relative;
  }

  .notif-dot {
    position: absolute;
    top: 8px;
    right: 8px;
    width: 8px;
    height: 8px;
    background: #ED1C24;
    border-radius: 50%;
    border: 2px solid var(--bg-primary);
  }

  .notif-panel {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    width: 360px;
    max-height: 400px;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    z-index: 100;
    overflow: hidden;
    animation: panelSlideDown 0.15s ease-out;
  }

  @keyframes panelSlideDown {
    from { opacity: 0; transform: translateY(-4px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .notif-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-color);
  }

  .notif-title {
    font-size: 0.8125rem;
    font-weight: 700;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .notif-count {
    font-size: 0.6875rem;
    font-weight: 700;
    background: var(--bg-secondary);
    color: var(--text-secondary);
    padding: 0.1rem 0.4rem;
    border-radius: var(--radius-full);
  }

  .notif-list {
    overflow-y: auto;
    max-height: 300px;
  }

  .notif-item {
    display: flex;
    align-items: flex-start;
    gap: 0.625rem;
    width: 100%;
    padding: 0.75rem 1rem;
    border: none;
    background: transparent;
    cursor: pointer;
    text-align: left;
    transition: background 0.12s ease;
  }

  .notif-item:hover {
    background: var(--bg-hover, rgba(0, 0, 0, 0.04));
  }

  .notif-item + .notif-item {
    border-top: 1px solid var(--border-color);
  }

  .notif-item-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    flex-shrink: 0;
    margin-top: 1px;
  }

  .notif-item-body {
    flex: 1;
    min-width: 0;
  }

  .notif-item-tag {
    font-size: 0.5625rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    display: block;
    margin-bottom: 0.125rem;
  }

  .notif-item-message {
    font-size: 0.8125rem;
    font-weight: 400;
    color: var(--text-primary);
    line-height: 1.4;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .notif-footer {
    padding: 0.5rem 1rem;
    border-top: 1px solid var(--border-color);
  }

  .notif-restore-btn {
    width: 100%;
    padding: 0.4rem 0;
    border: none;
    background: transparent;
    color: #ED1C24;
    font-size: 0.8125rem;
    font-weight: 600;
    cursor: pointer;
    border-radius: var(--radius-sm);
    transition: background 0.12s ease;
  }

  .notif-restore-btn:hover {
    background: rgba(237, 28, 36, 0.05);
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

  .view-switcher {
    display: flex;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-full);
    padding: 2px;
    margin-left: 1rem;
  }

  .view-switch-btn {
    font-family: var(--font-sans);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    padding: 4px 14px;
    border: none;
    border-radius: var(--radius-full);
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .view-switch-btn:hover {
    color: var(--text-primary);
  }

  .view-switch-btn.active {
    background: var(--bg-primary);
    color: var(--text-primary);
    box-shadow: var(--shadow-sm);
  }

  @media (max-width: 1280px) {
    .topbar {
      height: 64px;
      padding: 0 1.5rem;
    }
    .icon-btn {
      width: 36px;
      height: 36px;
    }
    .avatar {
      width: 36px;
      height: 36px;
    }
    .divider {
      height: 28px;
    }
  }

  @media (max-width: 1024px) {
    .topbar {
      height: 56px;
      padding: 0 1rem;
    }
    .topbar-left {
      gap: 0.5rem;
    }
    .crumb {
      font-size: 10px;
    }
    .icon-btn {
      width: 32px;
      height: 32px;
    }
    .avatar {
      width: 32px;
      height: 32px;
    }
    .divider {
      height: 24px;
      margin: 0 0.25rem;
    }
    .user-name {
      font-size: 0.7rem;
    }
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
