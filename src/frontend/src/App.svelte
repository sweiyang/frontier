<script>
  import { onMount } from "svelte";
  import "./app.css";
  import Sidebar from "./lib/Sidebar.svelte";
  import ChatArea from "./lib/ChatArea.svelte";
  import Login from "./lib/Login.svelte";
  import CreateProject from "./lib/CreateProject.svelte";
  import Workbench from "./lib/Workbench.svelte";
  import Artefacts from "./lib/Artefacts.svelte";
  import SplashScreen from "./lib/SplashScreen.svelte";
  import SiteRenderer from "./lib/SiteRenderer.svelte";
  import SiteBuilder from "./lib/SiteBuilder.svelte";
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

  let isAuthenticated = $state(false);
  let currentUser = $state(null);
  let currentUserDisplayName = $state(null);
  let currentConversationId = $state(null);
  let conversationKey = $state(0);
  let currentRoute = $state("chat"); // 'chat' | 'create_project' | 'workbench' | 'artefacts'
  let isLoading = $state(true); // Show loading while checking token
  let showSplash = $state(false); // Splash screen disabled
  let splashFadeOut = $state(false);
  let currentProject = $state(null); // Project from URL path
  let sidebarRef = $state(null); // Reference to Sidebar for refreshing conversations
  let appName = $state("Frontier"); // App name from config, default to "Frontier"
  let splashText = $state("Welcome to Frontier"); // Splash text from config
  let footnote = $state(""); // Footnote from config
  let contactConfig = $state({}); // Contact configuration from API
  let faqConfig = $state({}); // FAQ configuration from API
  let logoUrl = $state(null); // Logo URL from config
  let chatAreaRef = $state(null);
  let sidebarCollapsed = $state(true);
  let isPlatformOwner = $state(false);
  let preSelectedAgentId = $state(null);
  let selectedAgentId = $state(null);
  let projectNotFoundName = $state(null); // Holds the name of a project that wasn't found
  let projectFallbackTarget = $state(null); // The default project to redirect to after dismissing
  let projectUnauthorizedName = $state(null); // Holds the name of a project user is not authorized to access
  let projectSite = $state(null); // Site config for current project (if any)
  let sitePagePath = $state("/"); // Current page path within the site
  let panelElementsByConv = $state({}); // Persists panel elements per conversation

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

    (async () => {
      const splashStartTime = Date.now();
    const MINIMUM_SPLASH_DURATION = 2000; // 2 seconds minimum

    // Fetch app configuration first
    let appConfigData = {};
    try {
      appConfigData = await getAppConfig();
      appName = appConfigData.app_name || "Frontier";
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
          isPlatformOwner = data.is_platform_owner || false;
          isAuthenticated = true;
        } else {
          // Token is invalid, clear it
          clearToken();
        }
      } catch (e) {
        // Network error or other issue
        clearToken();
      }
    }

    // When user is logged in and lands on "/", redirect to default project if configured
    const defaultProjectName =
      appConfigData.default_project &&
      String(appConfigData.default_project).trim();
    if (!projectFromUrl && routeFromUrl === "chat" && defaultProjectName && isAuthenticated) {
      currentProject = defaultProjectName;
      setCurrentProject(defaultProjectName);
      window.history.replaceState({}, "", `/${defaultProjectName}`);
    }

    // Validate that the project exists on the backend
    if (isAuthenticated && currentProject) {
      await validateAndFallbackProject(currentProject, defaultProjectName);
    }

    isLoading = false;
    })();

    // Listen for auth:logout events (when token expires)
    handleAuthLogout = () => {
      isAuthenticated = false;
      currentUser = null;
      currentUserDisplayName = null;
      currentConversationId = null;
      currentRoute = "chat";
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
        isPlatformOwner = meData.is_platform_owner || false;
      } else {
        currentUser = username;
        currentUserDisplayName = display_name || null;
      }
    } catch {
      currentUser = username;
      currentUserDisplayName = display_name || null;
    }

    // Resolve the project BEFORE setting isAuthenticated so that
    // the Sidebar mounts with the project context already available
    // (authFetch sends X-Project header based on getCurrentProject()).
    const { project: projectFromUrl, route: routeFromUrl, pagePath: pagePathFromLogin } = parseUrl();
    sitePagePath = pagePathFromLogin;
    let defaultProjectName = null;
    try {
      const config = await getAppConfig();
      defaultProjectName =
        config["default_project"] && String(config["default_project"]).trim();
    } catch (e) {
      console.error("Failed to load config after login:", e);
    }

    if (!projectFromUrl && routeFromUrl === "chat" && defaultProjectName) {
      currentProject = defaultProjectName;
      setCurrentProject(defaultProjectName);
      window.history.replaceState({}, "", `/${defaultProjectName}`);
    }

    // Validate the resolved project exists
    if (currentProject) {
      await validateAndFallbackProject(currentProject, defaultProjectName);
    }

    isAuthenticated = true;
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
    isPlatformOwner = false;
    currentConversationId = null;
    currentRoute = "chat";
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
  }

  function handleClearAgentFilter() {
    selectedAgentId = null;
  }

  function handleLayoutChange(event) {
    const { collapseSidebar } = event.detail;
    sidebarCollapsed = collapseSidebar === true;
  }

  function toggleSidebar() {
    sidebarCollapsed = !sidebarCollapsed;
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
      return;
    }
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
    }
  }

  $effect(() => {
    if (isAuthenticated && currentProject && currentRoute === "chat") {
      loadProjectSite(currentProject);
    } else {
      projectSite = null;
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
    {:else if currentRoute === "workbench"}
      <Workbench
        {appName}
        {isPlatformOwner}
        onback={handleBackFromWorkbench}
        oncreateproject={() => currentRoute = "create_project"}
      />
    {:else if currentRoute === "artefacts"}
      <Artefacts
        onback={() => { currentRoute = "chat"; }}
        onopen={handleOpenArtefact}
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
          <SiteBuilder project={currentProject} fullPage={true} />
        </div>
      </div>
    {:else}
      <div class="app-container">
        <div class="sidebar-area" class:collapsed={sidebarCollapsed}>
          {#if sidebarCollapsed}
            <div class="sidebar-collapsed-strip">
              <button class="sidebar-expand-btn" onclick={toggleSidebar} title="Show sidebar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2"></rect>
                  <line x1="9" y1="3" x2="9" y2="21"></line>
                </svg>
              </button>
            </div>
          {:else}
            <div class="sidebar-inner">
              <Sidebar
                bind:this={sidebarRef}
                {currentUser}
                {currentUserDisplayName}
                {currentConversationId}
                {currentProject}
                {currentRoute}
                {appName}
                {logoUrl}
                contact={contactConfig}
                faq={faqConfig}
                filterAgentId={selectedAgentId}
                onclearfilter={handleClearAgentFilter}
                showChat={!projectSite || !projectSite.pages?.length || projectSite.pages.some(pg => (pg.components ?? []).some(c => c.type === "chat_window"))}
                onlogout={handleLogout}
                onselectconversation={handleSelectConversation}
                onnewconversation={handleNewConversation}
                onnavigate={handleNavigate}
              />
              <button class="sidebar-collapse-btn" onclick={toggleSidebar} title="Hide sidebar">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <rect x="3" y="3" width="18" height="18" rx="2"></rect>
                  <line x1="9" y1="3" x2="9" y2="21"></line>
                </svg>
              </button>
            </div>
          {/if}
        </div>
        <div class="main-content">
          {#if currentRoute === "artefacts"}
            <Artefacts
              onback={() => { currentRoute = "chat"; }}
              onopen={(pn, aid) => handleOpenArtefact(pn, aid)}
            />
          {:else if projectSite && projectSite.pages && projectSite.pages.length > 0}
            <SiteRenderer
              site={projectSite}
              project={currentProject}
              user={{ username: currentUser, display_name: currentUserDisplayName }}
              pagePath={sitePagePath}
            />
          {:else}
            {#key conversationKey}
              <ChatArea
                bind:this={chatAreaRef}
                {currentUser}
                {currentUserDisplayName}
                conversationId={currentConversationId}
                project={currentProject}
                {footnote}
                {preSelectedAgentId}
                onconversationcreated={handleConversationCreated}
                onmessagesent={handleMessageSent}
                onnewchat={handleResetChat}
                onlayoutchange={handleLayoutChange}
                onagentchange={handleAgentChange}
                initialElements={panelElementsByConv[currentConversationId] || []}
                onelementschange={handleElementsChange}
              />
            {/key}
          {/if}
        </div>
      </div>
    {/if}
  {:else}
    <Login {appName} onlogin={handleLogin} />
  {/if}
{/if}

<style>
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
  }

  .sidebar-area {
    flex-shrink: 0;
    display: flex;
    transition: width 0.2s ease;
  }

  .sidebar-area:not(.collapsed) {
    width: 260px;
  }

  .sidebar-area.collapsed {
    width: 44px;
  }

  .sidebar-inner {
    width: 260px;
    display: flex;
    position: relative;
  }

  .sidebar-collapse-btn {
    position: absolute;
    top: 0.65rem;
    right: 0.5rem;
    z-index: 10;
    width: 30px;
    height: 30px;
    border-radius: 8px;
    border: none;
    background: transparent;
    color: var(--text-secondary, #888);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
  }

  .sidebar-collapse-btn:hover {
    background: rgba(0, 0, 0, 0.05);
    color: var(--text-primary, #333);
  }

  .sidebar-collapsed-strip {
    width: 44px;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 0.65rem;
    background-color: var(--sidebar-bg, var(--bg-secondary));
    border-right: 1px solid var(--border-color, #e8e8e8);
  }

  .sidebar-expand-btn {
    width: 30px;
    height: 30px;
    border-radius: 8px;
    border: none;
    background: transparent;
    color: var(--text-secondary, #888);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
  }

  .sidebar-expand-btn:hover {
    background: rgba(0, 0, 0, 0.05);
    color: var(--text-primary, #333);
  }

  @media (max-width: 768px) {
    .sidebar-area {
      display: none;
    }
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
</style>
