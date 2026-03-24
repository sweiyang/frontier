<script>
  import { onMount } from "svelte";
  import { authFetch } from "./utils.js";
  import ProjectSettings from "./ProjectSettings.svelte";

  let { appName = "Frontier", isPlatformOwner = false, onback = () => {}, oncreateproject = () => {} } = $props();

  // State
  let projects = $state([]);
  let selectedProject = $state(null);
  let loading = $state(true);
  let activeSection = $state("agents"); // default to agents

  // Data-driven sidebar nav (extensible for future sections)
  const navSections = [
    { id: "agents", label: "Agents", icon: "agents" },
    { id: "builder", label: "Site Builder", icon: "layout" },
    { id: "approval", label: "Approval", icon: "check" },
    { id: "usage", label: "Usage", icon: "chart" },
    { id: "general", label: "General", icon: "settings" },
  ];

  onMount(async () => {
    await loadProjects();

    const handleForbidden = () => {
      selectedProject = null;
    };
    window.addEventListener("auth:forbidden", handleForbidden);

    return () => {
      window.removeEventListener("auth:forbidden", handleForbidden);
    };
  });

  async function loadProjects() {
    loading = true;
    try {
      const response = await authFetch("/projects/owned");
      if (response.ok) {
        const data = await response.json();
        projects = data.projects || [];
      }
    } catch (error) {
      console.error("Failed to load projects:", error);
    } finally {
      loading = false;
    }
  }

  const selectedProjectData = $derived(projects.find(p => p.project_name === selectedProject) || null);
  const siteBuilderEnabled = $derived(selectedProjectData?.site_builder_enabled !== false);

  function selectProject(projectName) {
    selectedProject = projectName;
    activeSection = "agents"; // Always start with agents
  }

  function backToProjects() {
    selectedProject = null;
  }

  function handleProjectSettingsBack() {
    // ProjectSettings' "back" means go back to project list
    selectedProject = null;
  }

  function getAgentCount(project) {
    return project.agent_count || 0;
  }
</script>

<div class="workbench-container">
  <!-- Header -->
  <header class="workbench-header">
    <div class="header-left">
      {#if selectedProject}
        <button class="back-btn" onclick={backToProjects}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M19 12H5" />
            <polyline points="12 19 5 12 12 5" />
          </svg>
          <span>Projects</span>
        </button>
        <span class="breadcrumb-sep">/</span>
        <span class="breadcrumb-project">{selectedProject}</span>
      {/if}
    </div>
    <div class="header-right">
      <div class="workbench-badge">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        <span>Workbench</span>
      </div>
    </div>
  </header>

  <!-- Content -->
  <div class="workbench-body">
    {#if !selectedProject}
      <!-- Project Picker View -->
      <div class="project-picker">
        <div class="picker-header">
          <div class="picker-title-area">
            <div>
              <h2 class="picker-title">Your Projects</h2>
              <p class="picker-subtitle">Select a project to manage its agents and configuration</p>
            </div>
            {#if projects.length > 0}
              <button class="create-project-btn" onclick={(e) => oncreateproject(e)}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19" />
                  <line x1="5" y1="12" x2="19" y2="12" />
                </svg>
                <span>Create Project</span>
              </button>
            {/if}
          </div>
        </div>

        {#if loading}
          <div class="picker-loading">
            <div class="spinner"></div>
            <span>Loading projects...</span>
          </div>
        {:else if projects.length === 0}
          <div class="picker-empty">
            <div class="empty-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
              </svg>
            </div>
            <h3>No projects yet</h3>
            <p>Create a project to get started with your AI agents</p>
            <button class="create-project-btn empty-state-btn" onclick={(e) => oncreateproject(e)}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              <span>Create Project</span>
            </button>
          </div>
        {:else}
          <div class="project-grid">
            {#each projects as project}
              <div
                class="project-card"
                role="button"
                tabindex="0"
                onclick={() => selectProject(project.project_name)}
                onkeydown={(e) => { if (e.key === 'Enter' || e.key === ' ') selectProject(project.project_name); }}
              >
                <div class="card-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
                  </svg>
                </div>
                <div class="card-content">
                  <span class="card-name">{project.project_name}</span>
                  <span class="card-meta">
                    {#if project.agent_count !== undefined}
                      {project.agent_count} agent{project.agent_count !== 1 ? 's' : ''}
                    {:else}
                      Project
                    {/if}
                  </span>
                </div>
                {#if project.has_dashboard}
                  <button
                    class="card-site-btn"
                    title="View site"
                    onclick={(e) => {
                      e.stopPropagation();
                      window.history.pushState({}, "", `/${project.project_name}`);
                      window.dispatchEvent(new PopStateEvent("popstate"));
                    }}
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                      <polyline points="15 3 21 3 21 9" />
                      <line x1="10" y1="14" x2="21" y2="3" />
                    </svg>
                    View Site
                  </button>
                {/if}
                <div class="card-arrow">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    {:else}
      <!-- Project Workspace View -->
      <div class="workspace">
        <nav class="workspace-nav">
          <div class="nav-label">Configure</div>
          {#each navSections.filter(s => s.id !== 'builder' || siteBuilderEnabled) as section}
            <button
              class="nav-item"
              class:active={activeSection === section.id}
              onclick={() => {
                if (section.id === "builder") {
                  window.history.pushState({}, "", `/${selectedProject}/site-builder`);
                  window.dispatchEvent(new PopStateEvent("popstate"));
                } else {
                  activeSection = section.id;
                }
              }}
            >
              {#if section.icon === "agents"}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <circle cx="8.5" cy="8.5" r="1.5" />
                  <polyline points="21 15 16 10 5 21" />
                </svg>
              {:else if section.icon === "users"}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                  <circle cx="9" cy="7" r="4" />
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                  <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                </svg>
              {:else if section.icon === "settings"}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.74v-.52a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              {:else if section.icon === "chart"}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="12" y1="20" x2="12" y2="10" />
                  <line x1="18" y1="20" x2="18" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="16" />
                </svg>
              {:else if section.icon === "check"}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 11l3 3L22 4" />
                  <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
                </svg>
              {:else if section.icon === "layout"}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                  <line x1="3" y1="9" x2="21" y2="9" />
                  <line x1="9" y1="21" x2="9" y2="9" />
                </svg>
              {/if}
              <span>{section.label}</span>
              {#if section.id === "agents"}
                <span class="nav-indicator">●</span>
              {/if}
            </button>
          {/each}
        </nav>

        <div class="workspace-content">
          <ProjectSettings
            project={selectedProject}
            onback={handleProjectSettingsBack}
            initialTab={activeSection}
            hideHeader={true}
            {isPlatformOwner}
          />
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .workbench-container {
    width: 100%;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--bg-primary);
  }

  /* Header */
  .workbench-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.5rem;
    border-bottom: 1px solid var(--border-color);
    background-color: var(--bg-primary);
    flex-shrink: 0;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .back-btn {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.4rem 0.75rem;
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-weight: 500;
    transition: all 0.15s ease;
  }

  .back-btn:hover {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
  }

  .breadcrumb-sep {
    color: var(--border-color);
    font-size: 1.1rem;
  }

  .breadcrumb-project {
    font-weight: 600;
    color: var(--text-primary);
    font-size: 0.95rem;
  }

  .header-right {
    display: flex;
    align-items: center;
  }

  .workbench-badge {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.75rem;
    background-color: var(--bg-secondary);
    border-radius: var(--radius-full);
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  /* Body */
  .workbench-body {
    flex: 1;
    overflow-y: auto;
    display: flex;
  }

  /* Project Picker */
  .project-picker {
    width: 100%;
    max-width: 800px;
    margin: 0 auto;
    padding: 3rem 1.5rem;
  }

  .picker-header {
    margin-bottom: 2rem;
  }

  .picker-title-area {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
  }

  .create-project-btn {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background-color: var(--primary-accent);
    color: white;
    border: none;
    border-radius: var(--radius-md);
    font-size: 0.95rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .create-project-btn:hover {
    background-color: var(--primary-accent-hover);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px var(--accent-glow);
  }

  .empty-state-btn {
    margin: 1.5rem auto 0;
  }

  .picker-title {
    font-family: var(--font-display);
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  .picker-subtitle {
    font-size: 0.95rem;
    color: var(--text-secondary);
  }

  .picker-loading {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.75rem;
    padding: 3rem;
    color: var(--text-secondary);
  }

  .spinner {
    width: 20px;
    height: 20px;
    border: 2px solid var(--border-color);
    border-top-color: var(--primary-accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .picker-empty {
    text-align: center;
    padding: 3rem 1.5rem;
    color: var(--text-secondary);
  }

  .empty-icon {
    margin-bottom: 1rem;
    opacity: 0.4;
  }

  .picker-empty h3 {
    font-size: 1.15rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  .picker-empty p {
    font-size: 0.9rem;
    margin: 0;
  }

  /* Project Grid */
  .project-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 0.75rem;
  }

  .project-card {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem 1.25rem;
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    text-align: left;
    transition: all 0.2s ease;
    cursor: pointer;
  }

  .project-card:hover {
    border-color: var(--primary-accent);
    box-shadow: 0 2px 12px var(--accent-glow);
    transform: translateY(-1px);
  }

  .card-icon {
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: var(--accent-glow);
    border-radius: var(--radius-md);
    color: var(--primary-accent);
    flex-shrink: 0;
  }

  .card-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .card-name {
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--text-primary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .card-meta {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: 0.1rem;
  }

  .card-site-btn {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    font-size: 0.75rem;
    font-weight: 500;
    padding: 0.25rem 0.6rem;
    border-radius: var(--radius-full);
    background: var(--accent-glow);
    color: var(--primary-accent);
    border: 1px solid rgba(225, 29, 72, 0.25);
    cursor: pointer;
    flex-shrink: 0;
    transition: all 0.15s ease;
  }

  .card-site-btn:hover {
    background: rgba(225, 29, 72, 0.18);
    border-color: rgba(225, 29, 72, 0.4);
  }

  .card-arrow {
    color: var(--text-secondary);
    opacity: 0.4;
    flex-shrink: 0;
    transition: opacity 0.15s ease;
  }

  .project-card:hover .card-arrow {
    opacity: 0.8;
  }

  /* Workspace */
  .workspace {
    display: flex;
    width: 100%;
    height: 100%;
  }

  .workspace-nav {
    width: 200px;
    min-width: 200px;
    padding: 1.25rem 0.75rem;
    border-right: 1px solid var(--border-color);
    background-color: var(--bg-secondary);
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .nav-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-secondary);
    padding: 0 0.75rem;
    margin-bottom: 0.5rem;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.55rem 0.75rem;
    border-radius: var(--radius-md);
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-secondary);
    transition: all 0.15s ease;
    text-align: left;
    width: 100%;
  }

  .nav-item:hover {
    background-color: var(--bg-hover);
    color: var(--text-primary);
  }

  .nav-item.active {
    background-color: var(--accent-glow);
    color: var(--primary-accent);
    font-weight: 600;
  }

  .nav-item svg {
    flex-shrink: 0;
  }

  .nav-indicator {
    margin-left: auto;
    font-size: 0.5rem;
    color: inherit;
    opacity: 0.6;
  }

  .workspace-content {
    flex: 1;
    overflow-y: auto;
    min-width: 0;
  }

  /* Override ProjectSettings styles when embedded */
  .workspace-content :global(.settings-container) {
    min-height: 0;
  }

  .workspace-content :global(.settings-header) {
    display: none;
  }

  .workspace-content :global(.tabs) {
    display: none;
  }

  @media (max-width: 768px) {
    .workspace {
      flex-direction: column;
    }

    .workspace-nav {
      width: 100%;
      min-width: unset;
      flex-direction: row;
      border-right: none;
      border-bottom: 1px solid var(--border-color);
      padding: 0.5rem;
      overflow-x: auto;
      gap: 0.25rem;
    }

    .nav-label {
      display: none;
    }

    .nav-item {
      white-space: nowrap;
    }
  }
</style>
