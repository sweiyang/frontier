<script>
  import { onMount } from "svelte";
  import "./app.css";
  import Sidebar from "./lib/Sidebar.svelte";
  import ChatArea from "./lib/ChatArea.svelte";
  import Login from "./lib/Login.svelte";
  import CreateProject from "./lib/CreateProject.svelte";
  import ProjectSettings from "./lib/ProjectSettings.svelte";
  import SplashScreen from "./lib/SplashScreen.svelte";
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
  let currentConversationId = $state(null);
  let conversationKey = $state(0);
  let currentRoute = $state("chat"); // 'chat' | 'create_project' | 'profile' | 'settings'
  let isLoading = $state(true); // Show loading while checking token
  let showSplash = $state(true); // Show splash screen initially
  let splashFadeOut = $state(false); // Control splash screen fade out animation
  let currentProject = $state(null); // Project from URL path
  let sidebarRef = $state(null); // Reference to Sidebar for refreshing conversations
  let appName = $state("Conduit"); // App name from config, default to "Conduit"
  let splashText = $state("Welcome to Conduit"); // Splash text from config
  let footnote = $state(""); // Footnote from config
  let contactConfig = $state({}); // Contact configuration from API
  let faqConfig = $state({}); // FAQ configuration from API
  let logoUrl = $state(null); // Logo URL from config
  let chatAreaRef = $state(null);
  let sidebarCollapsed = $state(false);
  let projectNotFoundName = $state(null); // Holds the name of a project that wasn't found
  let projectFallbackTarget = $state(null); // The default project to redirect to after dismissing

  /**
   * Extract project name and route from URL path.
   * URL format: /{project_name} or /{project_name}/settings
   */
  function parseUrl() {
    const path = window.location.pathname;
    const segments = path.split("/").filter(Boolean);

    let project = null;
    let route = "chat";

    if (segments.length > 0) {
      project = segments[0];
      // Check if second segment is 'settings'
      if (segments.length > 1 && segments[1] === "settings") {
        route = "settings";
      }
    }

    return { project, route };
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

  onMount(async () => {
    const splashStartTime = Date.now();
    const MINIMUM_SPLASH_DURATION = 2000; // 2 seconds minimum

    // Fetch app configuration first
    let appConfigData = {};
    try {
      appConfigData = await getAppConfig();
      appName = appConfigData.app_name || "Conduit";
      splashText = appConfigData.splash_text || "Welcome to Conduit";
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
    const { project: projectFromUrl, route: routeFromUrl } = parseUrl();
    if (projectFromUrl) {
      currentProject = projectFromUrl;
      setCurrentProject(projectFromUrl);
    }
    if (routeFromUrl) {
      currentRoute = routeFromUrl;
    }

    // Listen for URL changes (for SPA navigation)
    const handlePopState = () => {
      const { project, route } = parseUrl();
      currentProject = project;
      setCurrentProject(project);
      currentRoute = route;
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
    if (!projectFromUrl && defaultProjectName && isAuthenticated) {
      currentProject = defaultProjectName;
      setCurrentProject(defaultProjectName);
      window.history.replaceState({}, "", `/${defaultProjectName}`);
    }

    // Validate that the project exists on the backend
    if (isAuthenticated && currentProject) {
      await validateAndFallbackProject(currentProject, defaultProjectName);
    }

    isLoading = false;

    // Ensure splash screen shows for at least 2 seconds
    const elapsedTime = Date.now() - splashStartTime;
    const remainingTime = Math.max(0, MINIMUM_SPLASH_DURATION - elapsedTime);

    setTimeout(() => {
      // Start fade out animation
      splashFadeOut = true;
      // Remove splash screen after fade animation completes
      setTimeout(() => {
        showSplash = false;
      }, 500); // Match the CSS transition duration
    }, remainingTime);

    // Listen for auth:logout events (when token expires)
    const handleAuthLogout = () => {
      isAuthenticated = false;
      currentUser = null;
      currentConversationId = null;
      currentRoute = "chat";
    };
    window.addEventListener("auth:logout", handleAuthLogout);

    return () => {
      window.removeEventListener("auth:logout", handleAuthLogout);
      window.removeEventListener("popstate", handlePopState);
    };
  });

  async function handleLogin(event) {
    const { username, access_token } = event.detail;
    // Save token and user info
    saveToken(access_token);
    saveUser({ username });

    // Fetch authoritative user info from /me now that the token is saved
    try {
      const meResponse = await authFetch("/me");
      if (meResponse.ok) {
        const meData = await meResponse.json();
        currentUser = meData.username;
      } else {
        currentUser = username;
      }
    } catch {
      currentUser = username;
    }

    // Resolve the project BEFORE setting isAuthenticated so that
    // the Sidebar mounts with the project context already available
    // (authFetch sends X-Project header based on getCurrentProject()).
    const projectFromUrl = getProjectFromUrl();
    let defaultProjectName = null;
    try {
      const config = await getAppConfig();
      defaultProjectName =
        config.default_project && String(config.default_project).trim();
    } catch (e) {
      console.error("Failed to load config after login:", e);
    }

    if (!projectFromUrl && defaultProjectName) {
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
    // Project created successfully, navigate back to chat
    currentRoute = "chat";
  }

  function handleCancelCreateProject() {
    currentRoute = "chat";
  }

  function handleBackFromSettings() {
    currentRoute = "chat";
    // Update URL to remove /settings
    if (currentProject) {
      window.history.pushState({}, "", `/${currentProject}`);
    } else {
      window.history.pushState({}, "", "/");
    }
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
    {:else if currentRoute === "settings" && currentProject}
      <ProjectSettings
        project={currentProject}
        onback={handleBackFromSettings}
      />
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
                {currentConversationId}
                {currentProject}
                {appName}
                {logoUrl}
                contact={contactConfig}
                faq={faqConfig}
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
          {#key conversationKey}
            <ChatArea
              bind:this={chatAreaRef}
              {currentUser}
              conversationId={currentConversationId}
              project={currentProject}
              {footnote}
              onconversationcreated={handleConversationCreated}
              onmessagesent={handleMessageSent}
              onnewchat={handleResetChat}
              onlayoutchange={handleLayoutChange}
            />
          {/key}
        </div>
      </div>
    {/if}
  {:else}
    <Login {appName} onlogin={handleLogin} />
  {/if}
{/if}

<style>
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
