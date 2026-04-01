<script>
  import { onMount } from "svelte";
  import "./app.css";
  import Sidebar from "./lib/Sidebar.svelte";
  import TopBar from "./lib/TopBar.svelte";
  import Dashboard from "./lib/Dashboard.svelte";
  import ChatArea from "./lib/ChatArea.svelte";
  import Login from "./lib/Login.svelte";
  import CreateProject from "./lib/CreateProject.svelte";
  import Workbench from "./lib/Workbench.svelte";
  import AdminPanel from "./lib/AdminPanel.svelte";
  import Artefacts from "./lib/Artefacts.svelte";
  import SplashScreen from "./lib/SplashScreen.svelte";
  import SiteRenderer from "./lib/SiteRenderer.svelte";
  import SiteBuilder from "./lib/SiteBuilder.svelte";
  import Toast from "./lib/Toast.svelte";
  import {
    saveToken,
    saveUser,
    getToken,
    clearToken,
    authFetch,
    setCurrentProject,
    getCurrentProject,
    getAppConfig,
  } from "./lib/utils.js";
  import { getStoredTheme, applyTheme, setThemeDom, toggleTheme } from "./lib/theme.js";

  let isAuthenticated = $state(false);
  let currentUser = $state(null);
  let currentUserDisplayName = $state(null);
  let currentUserEmail = $state(null);
  let currentConversationId = $state(null);
  let conversationKey = $state(0);
  let currentRoute = $state("chat"); // 'chat' | 'create_project' | 'workbench' | 'admin' | 'artefacts'
  let isLoading = $state(true); // Show loading while checking token
  let showSplash = $state(false); // Splash screen disabled
  let splashFadeOut = $state(false);
  let currentProject = $state(null); // Project from URL path
  let sidebarRef = $state(null); // Reference to Sidebar for refreshing conversations
  let appName = $state("Frontier AI"); // App name from config, default to "Frontier AI"
  let splashText = $state("Welcome to Frontier"); // Splash text from config
  let footnote = $state(""); // Footnote from config
  let contactConfig = $state({}); // Contact configuration from API
  let faqConfig = $state({}); // FAQ configuration from API
  let logoUrl = $state(null); // Logo URL from config
  let chatAreaRef = $state(null);
  let sidebarOpen = $state(true);
  let currentTheme = $state('light');
  let isPlatformOwner = $state(false);
  let isPlatformAdmin = $state(false);
  let hasWorkbenchAccess = $state(false);
  let preSelectedAgentId = $state(null);
  let selectedAgentId = $state(null);
  let activeAgentId = $state(null); // Agent selected from Dashboard
  let activeAgentName = $state(null);
  let projectAgents = $state([]); // Agents for current project
  let allAgents = $state([]); // All agents across all projects (for Sidebar)
  let projectNotFoundName = $state(null); // Holds the name of a project that wasn't found
  let projectFallbackTarget = $state(null); // The default project to redirect to after dismissing
  let projectUnauthorizedName = $state(null); // Holds the name of a project user is not authorized to access
  let projectSite = $state(null); // Site config for current project (if any)
  let projectSiteLoading = $state(false); // True while fetching project dashboard to avoid ChatArea flash
  let sitePagePath = $state("/"); // Current page path within the site
  let viewMode = $state("site"); // "site" | "chat" — current active view
  let projectDefaultView = $state("site"); // Admin-configured default view
  let projectViewLocked = $state(false); // Admin lock preventing view switching
  let panelElementsByConv = $state({}); // Persists panel elements per conversation
  let projectDisableStorage = $state(false); // Whether current project has message storage disabled
  let projectDescription = $state(null); // Description for current project

  const hasBothViews = $derived(
    projectSite?.pages?.length > 0 && projectAgents.some(a => !a.is_site)
  );
  const showViewSwitcher = $derived(hasBothViews && !projectViewLocked);
  const siteHasFullscreen = $derived(
    projectSite?.pages?.some(pg => (pg.components ?? []).some(c => c.fullscreen || c.type === "hero_form")) ?? false
  );
  const showSiteFullscreen = $derived(
    viewMode === "site" && siteHasFullscreen && projectSite?.pages?.length > 0
  );

  /**
   * Extract project name and route from URL path.
   * URL format: /{project_name}, /{project_name}/site-builder, or workbench
   */
  function parseUrl() {
    const path = window.location.pathname;
    const segments = path.split("/").filter(Boolean);

    let project = null;
    let route = "chat";
    let pagePath = "/";

    // Decode segments in case any are percent-encoded
    const decoded = segments.map(s => { try { return decodeURIComponent(s); } catch { return s; } });

    if (decoded.length > 0) {
      if (decoded[0] === "workbench") {
        route = "workbench";
      } else if (decoded[0] === "admin") {
        route = "admin";
      } else if (decoded.length >= 2 && decoded[1] === "site-builder") {
        project = decoded[0];
        route = "site_builder";
      } else {
        project = decoded[0];
        // Everything after the project name is the page path
        if (decoded.length > 1) {
          pagePath = "/" + decoded.slice(1).join("/");
        }
      }
    }

    return { project, route, pagePath };
  }

  function getProjectFromUrl() {
    return parseUrl().project;
  }

  async function validateAndFallbackProject(projectName, defaultProject) {
    if (!projectName) return;
    try {
      const response = await authFetch(`/projects/${encodeURIComponent(projectName)}`);
      if (response.status === 404) {
        projectNotFoundName = projectName;
        projectFallbackTarget =
          defaultProject && defaultProject !== projectName
            ? defaultProject
            : null;
      } else if (response.status === 403) {
        projectUnauthorizedName = projectName;
        projectFallbackTarget =
          defaultProject && defaultProject !== projectName
            ? defaultProject
            : null;
      }
    } catch (e) {
      console.error("Failed to validate project:", e);
    }
  }

  function dismissProjectNotFound() {
    const fallback = projectFallbackTarget;
    projectNotFoundName = null;
    projectFallbackTarget = null;

    if (fallback) {
      currentProject = fallback;
      setCurrentProject(fallback);
      window.history.replaceState({}, "", `/${fallback}`);
    } else {
      currentProject = null;
      setCurrentProject(null);
      window.history.replaceState({}, "", "/");
    }
    currentConversationId = null;
    conversationKey++;
    if (sidebarRef?.refreshConversations) {
      sidebarRef.refreshConversations();
    }
  }

  function dismissProjectUnauthorized() {
    const fallback = projectFallbackTarget;
    projectUnauthorizedName = null;
    projectFallbackTarget = null;

    // If on workbench, stay there — Workbench resets its own selectedProject via auth:forbidden
    if (currentRoute === "workbench") {
      return;
    }

    if (fallback) {
      currentProject = fallback;
      setCurrentProject(fallback);
      window.history.replaceState({}, "", `/${fallback}`);
    } else {
      currentProject = null;
      setCurrentProject(null);
      window.history.replaceState({}, "", "/");
    }
    currentConversationId = null;
    conversationKey++;
    if (sidebarRef?.refreshConversations) {
      sidebarRef.refreshConversations();
    }
  }

  onMount(() => {
    let handlePopState;
    let handleAuthLogout;
    let handleAuthForbidden;

    // Always start light (default theme)
    setThemeDom('light');
    currentTheme = 'light';

    (async () => {
      const splashStartTime = Date.now();
    const MINIMUM_SPLASH_DURATION = 2000; // 2 seconds minimum

    // Fetch app configuration first
    let appConfigData = {};
    try {
      appConfigData = await getAppConfig();
      appName = appConfigData.app_name || "Frontier AI";
      splashText = appConfigData.splash_text || "Welcome to Frontier";
      footnote = appConfigData.footnote || "";
      contactConfig = appConfigData.contact || {};
      faqConfig = appConfigData.faq || {};
      logoUrl = appConfigData.logo_url || null;
      // Update document title
      document.title = appName;
    } catch (e) {
      console.error("Failed to load app config:", e);
      // Keep defaults
    }

    // Extract project and route from URL
    const { project: projectFromUrl, route: routeFromUrl, pagePath: pagePathFromUrl } = parseUrl();
    sitePagePath = pagePathFromUrl;
    if (projectFromUrl) {
      currentProject = projectFromUrl;
      setCurrentProject(projectFromUrl);
    }
    if (routeFromUrl) {
      currentRoute = routeFromUrl;
    }

    // Listen for URL changes (for SPA navigation)
    handlePopState = () => {
      const { project, route, pagePath } = parseUrl();

      // When navigating to home or a different project, clear stale agent state
      // so Dashboard renders instead of a stale ChatArea.
      if (project !== currentProject) {
        activeAgentId = null;
        activeAgentName = null;
        selectedAgentId = null;
        preSelectedAgentId = null;
        currentConversationId = null;
      }

      currentProject = project;
      setCurrentProject(project);
      currentRoute = route;
      sitePagePath = pagePath;
    };
    window.addEventListener("popstate", handlePopState);

    // Check for existing token and restore session
    const token = getToken();
    if (token) {
      try {
        const response = await authFetch("/me");
        if (response.ok) {
          const data = await response.json();
          currentUser = data.username;
          currentUserDisplayName = data.display_name || null;
          currentUserEmail = data.email || null;
          isPlatformOwner = data.is_platform_owner || false;
          isPlatformAdmin = data.is_platform_admin || false;
          hasWorkbenchAccess = data.has_workbench_access || false;
          isAuthenticated = true;
          // Now that we're authenticated, apply the user's stored theme preference
          const storedTheme = getStoredTheme();
          applyTheme(storedTheme);
          currentTheme = storedTheme;
          loadAllAgents();
        } else {
          // Token is invalid, clear it
          clearToken();
        }
      } catch (e) {
        // Network error or other issue
        clearToken();
      }
    }

    // Validate that the project exists on the backend (only if navigated to a specific project URL)
    if (isAuthenticated && currentProject) {
      const defaultProjectName = appConfigData.default_project && String(appConfigData.default_project).trim();
      await validateAndFallbackProject(currentProject, defaultProjectName);
    }

    isLoading = false;
    })();

    // Listen for auth:logout events (when token expires)
    handleAuthLogout = () => {
      isAuthenticated = false;
      currentUser = null;
      currentUserDisplayName = null;
      currentUserEmail = null;
      currentConversationId = null;
      currentRoute = "chat";
      setThemeDom('light');
      currentTheme = 'light';
    };
    window.addEventListener("auth:logout", handleAuthLogout);

    // Listen for auth:forbidden events (when user lacks permission)
    handleAuthForbidden = async (event) => {
      const { project } = event.detail;
      if (project && !projectUnauthorizedName) {
        projectUnauthorizedName = project;
        // Try to get a fallback project
        try {
          const config = await getAppConfig();
          const defaultProj = config["default_project"] && String(config["default_project"]).trim();
          projectFallbackTarget = defaultProj && defaultProj !== project ? defaultProj : null;
        } catch {
          projectFallbackTarget = null;
        }
      }
    };
    window.addEventListener("auth:forbidden", handleAuthForbidden);

    return () => {
      if (handleAuthLogout) window.removeEventListener("auth:logout", handleAuthLogout);
      if (handleAuthForbidden) window.removeEventListener("auth:forbidden", handleAuthForbidden);
      if (handlePopState) window.removeEventListener("popstate", handlePopState);
    };
  });

  async function handleLogin(event) {
    const { username, access_token, display_name } = event.detail;
    // Save token and user info
    saveToken(access_token);
    saveUser({ username, display_name });

    // Fetch authoritative user info from /me now that the token is saved
    try {
      const meResponse = await authFetch("/me");
      if (meResponse.ok) {
        const meData = await meResponse.json();
        currentUser = meData.username;
        currentUserDisplayName = meData.display_name || display_name || null;
        currentUserEmail = meData.email || null;
        isPlatformOwner = meData.is_platform_owner || false;
        isPlatformAdmin = meData.is_platform_admin || false;
        hasWorkbenchAccess = meData.has_workbench_access || false;
      } else {
        currentUser = username;
        currentUserDisplayName = display_name || null;
      }
    } catch {
      currentUser = username;
      currentUserDisplayName = display_name || null;
    }

    const { project: projectFromUrl, pagePath: pagePathFromLogin } = parseUrl();
    sitePagePath = pagePathFromLogin;

    // Validate if the user navigated directly to a project URL
    if (projectFromUrl) {
      currentProject = projectFromUrl;
      setCurrentProject(projectFromUrl);
      await validateAndFallbackProject(projectFromUrl, null);
    }

    isAuthenticated = true;
    // Apply the user's stored theme preference now that they've logged in
    const theme = getStoredTheme();
    applyTheme(theme);
    currentTheme = theme;
    loadAllAgents();
  }

  async function handleLogout() {
    try {
      await authFetch("/logout", { method: "POST" });
    } catch (e) {
      // Ignore logout errors
    }
    clearToken();
    isAuthenticated = false;
    currentUser = null;
    currentUserDisplayName = null;
    currentUserEmail = null;
    isPlatformOwner = false;
    isPlatformAdmin = false;
    hasWorkbenchAccess = false;
    currentConversationId = null;
    currentRoute = "chat";
    applyTheme('light');
    currentTheme = 'light';
  }

  function handleSelectConversation(event) {
    currentConversationId = event.detail.conversationId;
    conversationKey++; // Force ChatArea to reload
  }

  function handleNewConversation(event) {
    currentConversationId = event.detail.conversationId;
    conversationKey++;
  }

  function handleNavigate(event) {
    currentRoute = event.detail.route;
    if (event.detail.route === "workbench") {
      window.history.pushState({}, "", "/workbench");
    } else if (event.detail.route === "admin") {
      window.history.pushState({}, "", "/admin");
    }
  }

  function handleConversationCreated(event) {
    // A new conversation was created in ChatArea, update the current ID
    currentConversationId = event.detail.conversationId;
    // Refresh sidebar to show the new conversation
    if (sidebarRef?.refreshConversations) {
      sidebarRef.refreshConversations();
    }
  }

  async function handleMessageSent(event) {
    // Refresh sidebar to update conversation titles (they update after first message)
    if (sidebarRef?.refreshConversations) {
      await sidebarRef.refreshConversations();
    }
  }

  function handleCreateProject(event) {
    // Project created successfully, return to workbench
    currentRoute = "workbench";
  }

  function handleCancelCreateProject() {
    currentRoute = "workbench";
  }

  function handleBackFromWorkbench() {
    currentRoute = "chat";
    if (currentProject) {
      window.history.pushState({}, "", `/${currentProject}`);
    } else {
      window.history.pushState({}, "", "/");
    }
  }

  function handleViewSite(event) {
    const projectName = event.detail?.projectName;
    if (!projectName) return;
    currentProject = projectName;
    setCurrentProject(projectName);
    sitePagePath = "/";
    viewMode = "site";
    activeAgentId = null;
    window.history.pushState({}, "", `/${encodeURIComponent(projectName)}`);
    loadProjectSite(projectName);
  }

  function handleBackFromAdmin() {
    currentRoute = "chat";
    if (currentProject) {
      window.history.pushState({}, "", `/${currentProject}`);
    } else {
      window.history.pushState({}, "", "/");
    }
  }

  function handleOpenArtefact(projectName, agentId = null) {
    currentProject = projectName;
    setCurrentProject(projectName);
    window.history.pushState({}, "", `/${projectName}`);
    preSelectedAgentId = agentId;
    projectSite = null; // Clear stale site from previous project
    currentRoute = "chat";
    currentConversationId = null;
    conversationKey++;
  }
  function handleAgentChange(event) {
    selectedAgentId = event.detail.agentId;
    activeAgentId = event.detail.agentId;
    const agent = projectAgents.find(a => a.id === event.detail.agentId);
    activeAgentName = agent?.name || null;
  }

  function handleClearAgentFilter() {
    selectedAgentId = null;
  }

  function handleSelectAgent(agentId, projectName = null) {
    if (!agentId) {
      // Navigate home — clear project context and show all-agents Dashboard
      activeAgentId = null;
      activeAgentName = null;
      selectedAgentId = null;
      preSelectedAgentId = null;
      currentConversationId = null;
      currentProject = null;
      setCurrentProject(null);
      window.history.pushState({}, "", "/");
      viewMode = projectDefaultView;
      conversationKey++;
      return;
    }
    // Set project context if provided (e.g. agent selected from global home Dashboard)
    if (projectName && projectName !== currentProject) {
      currentProject = projectName;
      setCurrentProject(projectName);
      sitePagePath = "/";
      projectSiteLoading = true;
      window.history.pushState({}, "", `/${projectName}`);
    }
    const agent = projectAgents.find(a => a.id === agentId);
    activeAgentId = agentId;
    activeAgentName = agent?.name || projectName || null;
    selectedAgentId = agentId;
    preSelectedAgentId = agentId;
    currentConversationId = null;
    conversationKey++;

    // Auto-switch to chat when selecting an agent (if unlocked)
    if (hasBothViews && !projectViewLocked) {
      viewMode = "chat";
    }
  }

  function handleToggleViewMode(mode) {
    viewMode = mode;
    if (mode === "chat" && !activeAgentId) {
      const firstAgent = projectAgents.find(a => !a.is_site);
      if (firstAgent) {
        activeAgentId = firstAgent.id;
        activeAgentName = firstAgent.name;
        selectedAgentId = firstAgent.id;
        preSelectedAgentId = firstAgent.id;
      }
    }
  }

  async function loadProjectAgents(projectName) {
    if (!projectName) { projectAgents = []; return; }
    try {
      const res = await authFetch(`/projects/${encodeURIComponent(projectName)}/agents`);
      if (res.ok) {
        const data = await res.json();
        const AGENT_COLORS = ['#6366f1', '#e11d48', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];
        projectAgents = (data.agents || []).map((a, i) => ({
          ...a,
          _color: AGENT_COLORS[i % AGENT_COLORS.length],
        }));
      }
    } catch {}
  }

  async function loadAllAgents() {
    try {
      const res = await authFetch('/me/agents');
      if (res.ok) {
        const data = await res.json();
        const AGENT_COLORS = ['#6366f1', '#e11d48', '#f59e0b', '#10b981', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316'];
        allAgents = (data.agents || []).map((a, i) => ({
          ...a,
          _color: AGENT_COLORS[i % AGENT_COLORS.length],
        }));
      }
    } catch {}
  }

  function refreshProjectSettings() {
    if (!currentProject) return;
    authFetch(`/projects/${encodeURIComponent(currentProject)}`)
      .then(r => r.ok ? r.json() : null)
      .then(d => {
        projectDisableStorage = d?.disable_message_storage ?? false;
        projectDescription = d?.description || null;
        projectDefaultView = d?.default_view || "site";
        projectViewLocked = d?.view_locked ?? false;
        viewMode = d?.default_view || "site";
      })
      .catch(() => { projectDisableStorage = false; projectDescription = null; projectDefaultView = "site"; projectViewLocked = false; viewMode = "site"; });
  }

  $effect(() => {
    if (isAuthenticated && currentProject) {
      loadProjectAgents(currentProject);
      refreshProjectSettings();
    } else {
      projectAgents = [];
      projectDisableStorage = false;
      projectDescription = null;
    }
  });

  function handleLayoutChange(event) {
    const { collapseSidebar } = event.detail;
    if (collapseSidebar === true) sidebarOpen = false;
  }

  function toggleSidebar() {
    sidebarOpen = !sidebarOpen;
  }

  function handleToggleTheme() {
    currentTheme = toggleTheme();
  }

  function handleResetChat() {
    currentConversationId = null;
    conversationKey++;
  }

  function handleElementsChange(elements) {
    if (currentConversationId) {
      panelElementsByConv = { ...panelElementsByConv, [currentConversationId]: elements };
    }
  }

  async function loadProjectSite(projectName) {
    if (!projectName) {
      projectSite = null;
      projectSiteLoading = false;
      return;
    }
    projectSiteLoading = true;
    try {
      const response = await authFetch(
        `/projects/${encodeURIComponent(projectName)}/dashboard`,
      );
      if (!response.ok) {
        projectSite = null;
        return;
      }
      const data = await response.json();
      projectSite = data.site || null;
    } catch (e) {
      console.error("Failed to load project site:", e);
      projectSite = null;
    } finally {
      projectSiteLoading = false;
    }
  }

  $effect(() => {
    if (isAuthenticated && currentProject && currentRoute === "chat") {
      loadProjectSite(currentProject);
    } else {
      projectSite = null;
      projectSiteLoading = false;
    }
  });
</script>

{#if projectNotFoundName}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_noninteractive_element_interactions -->
  <div class="popup-overlay" role="dialog" tabindex="-1" onclick={dismissProjectNotFound}>
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div class="popup-card" role="presentation" onclick={(e) => e.stopPropagation()}>
      <div class="popup-icon">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
      </div>
      <h2 class="popup-title">Project not found</h2>
      <p class="popup-message">
        The project <strong>{projectNotFoundName}</strong> does not exist.
        {#if projectFallbackTarget}
          You will be redirected to <strong>{projectFallbackTarget}</strong>.
        {/if}
      </p>
      <button class="popup-btn" onclick={dismissProjectNotFound}>OK</button>
    </div>
  </div>
{/if}

{#if projectUnauthorizedName}
  <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_noninteractive_element_interactions -->
  <div class="popup-overlay" role="dialog" tabindex="-1" onclick={dismissProjectUnauthorized}>
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <div class="popup-card" role="presentation" onclick={(e) => e.stopPropagation()}>
      <div class="popup-icon popup-icon-unauthorized">
        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
        </svg>
      </div>
      <h2 class="popup-title">Access denied</h2>
      <p class="popup-message">
        You do not have access to the project <strong>{projectUnauthorizedName}</strong>.
        {#if projectFallbackTarget}
          You will be redirected to <strong>{projectFallbackTarget}</strong>.
        {/if}
      </p>
      <button class="popup-btn" onclick={dismissProjectUnauthorized}>OK</button>
    </div>
  </div>
{/if}

{#if showSplash}
  <SplashScreen text={splashText} fadeOut={splashFadeOut} />
{/if}

{#if !isLoading && !showSplash}
  {#if isAuthenticated}
    {#if currentRoute === "create_project"}
      <CreateProject
        {appName}
        oncreate={handleCreateProject}
        oncancel={handleCancelCreateProject}
      />
    {:else if currentRoute === "admin" && isPlatformAdmin}
      <AdminPanel
        {appName}
        onback={handleBackFromAdmin}
      />
    {:else if currentRoute === "workbench"}
      <Workbench
        {appName}
        {isPlatformOwner}
        onback={handleBackFromWorkbench}
        oncreateproject={() => currentRoute = "create_project"}
        onsettingssaved={refreshProjectSettings}
      />
    {:else if currentRoute === "site_builder" && currentProject}
      <div class="site-builder-fullpage">
        <header class="site-builder-fullpage-header">
          <a
            href="/{currentProject}"
            class="site-builder-back"
            onclick={(e) => {
              e.preventDefault();
              window.history.pushState({}, "", `/${currentProject}`);
              window.dispatchEvent(new PopStateEvent("popstate"));
            }}
          >← Back to project</a>
          <span class="site-builder-fullpage-title">Site Builder</span>
        </header>
        <div class="site-builder-fullpage-body">
          <SiteBuilder project={currentProject} fullPage={true} ondelete={() => {
            window.history.pushState({}, "", `/${currentProject}`);
            window.dispatchEvent(new PopStateEvent("popstate"));
          }} />
        </div>
      </div>
    {:else if showSiteFullscreen}
      <div class="site-fullscreen-overlay">
        <button class="site-fullscreen-back" onclick={() => { viewMode = "chat"; currentProject = null; setCurrentProject(null); window.history.replaceState({}, "", "/"); }} title="Back to Frontier">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><polyline points="12 19 5 12 12 5"/></svg>
          <span>Frontier</span>
        </button>
        <SiteRenderer
          site={projectSite}
          project={currentProject}
          user={{ username: currentUser, display_name: currentUserDisplayName, email: currentUserEmail }}
          pagePath={sitePagePath}
        />
      </div>
    {:else}
      <div class="app-container">
        <!-- Sidebar -->
        <Sidebar
          bind:this={sidebarRef}
          {currentUser}
          {currentUserDisplayName}
          {currentConversationId}
          {currentProject}
          {currentRoute}
          {appName}
          contact={contactConfig}
          faq={faqConfig}
          filterAgentId={selectedAgentId}
          onclearfilter={handleClearAgentFilter}
          showChat={!projectDisableStorage && (viewMode === "chat" || !projectSite || !projectSite.pages?.length || projectSite.pages.some(pg => (pg.components ?? []).some(c => c.type === "chat_window")))}
          onlogout={handleLogout}
          onselectconversation={handleSelectConversation}
          onnewconversation={handleNewConversation}
          onnavigate={handleNavigate}
          isOpen={sidebarOpen}
          {isPlatformOwner}
          {isPlatformAdmin}
          {hasWorkbenchAccess}
          agents={allAgents}
          {activeAgentId}
          onSelectAgent={handleSelectAgent}
          onSwitchToSite={() => { viewMode = "site"; }}
        />

        <!-- Main area: TopBar + content -->
        <div class="main-area">
          <TopBar
            {appName}
            {activeAgentName}
            {currentUser}
            {currentUserDisplayName}
            {currentTheme}
            {projectDescription}
            ontoggleSidebar={toggleSidebar}
            onnavigatehome={() => handleSelectAgent(null)}
            onlogout={handleLogout}
            ontoggletTheme={handleToggleTheme}
            {showViewSwitcher}
            {viewMode}
            onToggleViewMode={handleToggleViewMode}
          />

          <div class="main-content">
            {#if currentRoute === "artefacts"}
              <Artefacts
                onback={() => { currentRoute = "chat"; }}
                onopen={(pn, aid) => handleOpenArtefact(pn, aid)}
              />
            {:else if projectSiteLoading}
              <div class="project-loading">
                <div class="project-loading-spinner"></div>
              </div>
            {:else if projectSite && projectSite.pages && projectSite.pages.length > 0 && viewMode === "site"}
              <SiteRenderer
                site={projectSite}
                project={currentProject}
                user={{ username: currentUser, display_name: currentUserDisplayName, email: currentUserEmail }}
                pagePath={sitePagePath}
              />
            {:else if activeAgentId}
              {#key conversationKey}
                <ChatArea
                  bind:this={chatAreaRef}
                  {currentUser}
                  {currentUserDisplayName}
                  conversationId={currentConversationId}
                  project={currentProject}
                  {footnote}
                  preSelectedAgentId={activeAgentId}
                  onconversationcreated={handleConversationCreated}
                  onmessagesent={handleMessageSent}
                  onnewchat={handleResetChat}
                  onlayoutchange={handleLayoutChange}
                  onagentchange={handleAgentChange}
                  initialElements={panelElementsByConv[currentConversationId] || []}
                  onelementschange={handleElementsChange}
                />
              {/key}
            {:else}
              <Dashboard
                {currentUser}
                {currentUserDisplayName}
                {appName}
                onselectagent={(e) => handleSelectAgent(e.detail.agentId, e.detail.projectName)}
                onviewsite={handleViewSite}
              />
            {/if}
          </div>
        </div>
      </div>
    {/if}
  {:else}
    <Login {appName} onlogin={handleLogin} {currentTheme} ontoggletTheme={handleToggleTheme} contact={contactConfig} />
  {/if}
{/if}

<Toast />

<style>
  .site-fullscreen-overlay {
    position: fixed;
    inset: 0;
    z-index: 9999;
    background: var(--bg-primary);
    overflow: auto;
  }

  .site-fullscreen-back {
    position: fixed;
    top: 12px;
    left: 12px;
    z-index: 10000;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px 6px 10px;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: var(--radius-full);
    font-family: var(--font-sans);
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
    opacity: 0.6;
  }

  .site-fullscreen-back:hover {
    background: rgba(255, 255, 255, 0.95);
    color: var(--text-primary);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    opacity: 1;
  }

  .site-builder-fullpage {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    background: var(--bg-primary);
    overflow: hidden;
  }

  .site-builder-fullpage-header {
    flex-shrink: 0;
    height: 48px;
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    padding: 0 var(--spacing-lg);
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-primary);
  }

  .site-builder-back {
    font-size: 0.875rem;
    color: var(--text-secondary);
    text-decoration: none;
    transition: color 0.12s ease;
  }

  .site-builder-back:hover {
    color: var(--primary-accent);
  }

  .site-builder-fullpage-title {
    font-family: var(--font-display);
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .site-builder-fullpage-body {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }

  .site-builder-fullpage-body :global(.site-builder) {
    height: 100%;
    padding: var(--spacing-md);
  }

  .site-builder-fullpage-body :global(.site-builder .builder-body) {
    flex: 1;
    min-height: 0;
  }

  .site-builder-fullpage-body :global(.site-builder .canvas-column) {
    min-width: 0;
  }

  .site-builder-fullpage-body :global(.site-builder .site-canvas) {
    width: 100%;
    max-width: 1400px;
    min-height: calc(100vh - 180px);
    height: 100%;
  }

  .app-container {
    display: flex;
    height: 100vh;
    background-color: var(--bg-primary);
    overflow: hidden;
  }

  .main-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    min-width: 0;
    border-left: 1px solid var(--border-color);
  }

  .main-content {
    flex: 1;
    display: flex;
    overflow: hidden;
  }

  .popup-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: popupFadeIn 0.2s ease-out;
  }

  .popup-card {
    background: var(--bg-primary, #fff);
    border-radius: 16px;
    padding: 2rem 2.5rem;
    max-width: 400px;
    width: 90%;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
    animation: popupSlideIn 0.25s ease-out;
  }

  .popup-icon {
    color: #e67e22;
    margin-bottom: 0.75rem;
  }

  .popup-icon-unauthorized {
    color: #e74c3c;
  }

  .popup-title {
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary, #111);
    margin: 0 0 0.5rem;
  }

  .popup-message {
    font-size: 0.95rem;
    color: var(--text-secondary, #666);
    margin: 0 0 1.5rem;
    line-height: 1.5;
  }

  .popup-message strong {
    color: var(--text-primary, #111);
  }

  .popup-btn {
    padding: 0.6rem 2rem;
    border-radius: 8px;
    background: var(--text-primary, #111);
    color: var(--bg-primary, #fff);
    font-size: 0.95rem;
    font-weight: 500;
    border: none;
    cursor: pointer;
    transition: opacity 0.15s;
  }

  .popup-btn:hover {
    opacity: 0.85;
  }

  @keyframes popupFadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  @keyframes popupSlideIn {
    from { opacity: 0; transform: scale(0.95) translateY(8px); }
    to { opacity: 1; transform: scale(1) translateY(0); }
  }

  .project-loading {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-primary);
  }

  .project-loading-spinner {
    width: 32px;
    height: 32px;
    border: 3px solid var(--border-color);
    border-top-color: var(--primary-accent);
    border-radius: 50%;
    animation: project-spin 0.8s linear infinite;
  }

  @keyframes project-spin {
    to { transform: rotate(360deg); }
  }
</style>
