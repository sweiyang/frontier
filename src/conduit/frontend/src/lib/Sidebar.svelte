<script>
  import { onMount } from "svelte";
  import { authFetch, authPost } from "./utils.js";

  let {
    currentUser = "User",
    currentConversationId = null,
    currentProject = null,
    appName = "Conduit",
    onlogout = () => {},
    onselectconversation = () => {},
    onnewconversation = () => {},
    onnavigate = () => {},
  } = $props();

  let conversations = $state([]);
  let ownedProjects = $state([]);
  let isDropdownOpen = $state(false);

  // Expose refresh function for parent to call
  export async function refreshConversations() {
    await loadConversations();
  }

  onMount(async () => {
    await loadConversations();
    await loadOwnedProjects();

    // Close dropdown when clicking outside
    const handleClickOutside = (event) => {
      if (!event.target.closest(".user-section")) {
        isDropdownOpen = false;
      }
    };
    document.addEventListener("click", handleClickOutside);

    return () => {
      document.removeEventListener("click", handleClickOutside);
    };
  });

  function toggleDropdown() {
    isDropdownOpen = !isDropdownOpen;
  }

  function handleProfile() {
    isDropdownOpen = false;
    onnavigate({ detail: { route: "profile" } });
  }

  function handleCreateProject() {
    isDropdownOpen = false;
    onnavigate({ detail: { route: "create_project" } });
  }

  async function loadConversations() {
    try {
      const response = await authFetch("/conversations");
      if (response.ok) {
        const data = await response.json();
        conversations = data.conversations || [];
      }
    } catch (error) {
      console.error("Failed to load conversations:", error);
    }
  }

  async function loadOwnedProjects() {
    try {
      const response = await authFetch("/projects/owned");
      if (response.ok) {
        const data = await response.json();
        ownedProjects = data.projects || [];
      }
    } catch (error) {
      console.error("Failed to load owned projects:", error);
    }
  }

  function handleProjectAdmin(projectName) {
    isDropdownOpen = false;
    window.location.href = `/${projectName}`;
  }

  function handleProjectSettings(event, projectName) {
    event.stopPropagation();
    isDropdownOpen = false;
    window.location.href = `/${projectName}/settings`;
  }

  async function createNewConversation() {
    try {
      const response = await authPost("/conversations", {});
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

  function getInitial(name) {
    return name ? name.charAt(0).toUpperCase() : "U";
  }
</script>

<aside class="sidebar">
  <div class="logo-section">
    <div class="logo-left">
      <span class="logo-text">{appName}</span>
      {#if currentProject}
        <span class="project-badge">/ {currentProject}</span>
      {/if}
    </div>
    <button class="edit-icon-button" title="New Chat" onclick={createNewConversation}>
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
      </svg>
    </button>
  </div>

  <nav class="nav-links">
    <div class="conversations-list">
      {#each conversations as conv}
        <button
          class="nav-item conversation-item"
          class:active={currentConversationId === conv.id}
          onclick={() => selectConversation(conv.id)}
        >
          <span class="conv-title">{conv.title}</span>
        </button>
      {/each}
    </div>
  </nav>

  <div class="user-section">
    <button class="user-profile" onclick={toggleDropdown}>
      <div class="avatar">{getInitial(currentUser)}</div>
      <div class="username">{currentUser}</div>
    </button>

    {#if isDropdownOpen}
      <div class="user-dropdown">
        <button class="dropdown-item" onclick={handleProfile}>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
            <circle cx="12" cy="7" r="4" />
          </svg>
          <span>Profile</span>
        </button>
        <button class="dropdown-item" onclick={handleCreateProject}>
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
            />
            <line x1="12" y1="11" x2="12" y2="17" />
            <line x1="9" y1="14" x2="15" y2="14" />
          </svg>
          <span>Create project</span>
        </button>
        {#if ownedProjects.length > 0}
          <div class="dropdown-divider"></div>
          <div class="dropdown-section-label">Your Projects</div>
          {#each ownedProjects as project}
            <div class="dropdown-item-row">
              <button
                class="dropdown-item"
                onclick={() => handleProjectAdmin(project.project_name)}
              >
                <svg
                  width="16"
                  height="16"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path
                    d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"
                  />
                </svg>
                <span>{project.project_name}</span>
              </button>
              <button
                class="settings-button"
                onclick={(e) => handleProjectSettings(e, project.project_name)}
                title="Project settings"
              >
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <circle cx="12" cy="12" r="3" />
                  <path
                    d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
                  />
                </svg>
              </button>
            </div>
          {/each}
        {/if}
      </div>
    {/if}

    <button class="logout-button" onclick={onlogout} title="Sign out">
      <svg
        width="18"
        height="18"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
        <polyline points="16 17 21 12 16 7" />
        <line x1="21" y1="12" x2="9" y2="12" />
      </svg>
    </button>
  </div>
</aside>

<style>
  .sidebar {
    width: 260px;
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    padding: var(--spacing-md);
    height: 100%;
  }

  .logo-section {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-xl);
    font-weight: 600;
    font-size: 1.1rem;
    padding-left: var(--spacing-xs);
  }

  .logo-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    flex-wrap: wrap;
    flex: 1;
    min-width: 0;
  }

  .edit-icon-button {
    padding: var(--spacing-xs);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .edit-icon-button:hover {
    background-color: rgba(0, 0, 0, 0.04);
    color: var(--text-primary);
  }

  .project-badge {
    font-size: 0.85rem;
    font-weight: 500;
    color: var(--primary-accent, #6366f1);
    background: rgba(99, 102, 241, 0.1);
    padding: 2px 8px;
    border-radius: 4px;
  }

  .nav-links {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    overflow: hidden;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    transition: all 0.2s ease;
    font-size: 0.95rem;
    text-align: left;
    width: 100%;
  }

  .nav-item:hover,
  .nav-item.active {
    background-color: rgba(0, 0, 0, 0.04);
    color: var(--text-primary);
  }

  .conversations-list {
    flex: 1;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .conversation-item {
    border: none;
  }

  .conv-title {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    flex: 1;
  }

  .user-profile {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm);
    margin-top: auto;
    border-radius: var(--radius-md);
  }

  .user-profile:hover {
    background-color: rgba(0, 0, 0, 0.04);
  }

  .avatar {
    width: 28px;
    height: 28px;
    background-color: var(--primary-accent);
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .user-section {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: auto;
    padding: var(--spacing-xs);
    border-radius: var(--radius-md);
    position: relative;
  }

  .user-dropdown {
    position: absolute;
    bottom: 100%;
    left: 0;
    right: 0;
    margin-bottom: var(--spacing-xs);
    background-color: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    animation: slideUp 0.15s ease-out;
    z-index: 100;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .dropdown-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    color: var(--text-secondary);
    font-size: 0.9rem;
    transition: all 0.15s ease;
    text-align: left;
  }

  .dropdown-item:hover {
    background-color: rgba(0, 0, 0, 0.04);
    color: var(--text-primary);
  }

  .dropdown-item svg {
    flex-shrink: 0;
  }

  .dropdown-divider {
    height: 1px;
    background-color: var(--border-color);
    margin: var(--spacing-xs) 0;
  }

  .dropdown-section-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-muted, #999);
    padding: var(--spacing-xs) var(--spacing-md);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .dropdown-item-row {
    display: flex;
    align-items: center;
  }

  .dropdown-item-row .dropdown-item {
    flex: 1;
    min-width: 0;
  }

  .dropdown-item-row .dropdown-item span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .settings-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    color: var(--text-secondary);
    font-size: 0.9rem;
    transition: all 0.15s ease;
    text-align: left;
    flex-shrink: 0;
  }

  .settings-button:hover {
    background-color: rgba(0, 0, 0, 0.04);
    color: var(--text-primary);
  }

  .logout-button {
    padding: var(--spacing-sm);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    transition: all 0.2s ease;
  }

  .logout-button:hover {
    background-color: rgba(0, 0, 0, 0.04);
    color: var(--text-primary);
  }
</style>
