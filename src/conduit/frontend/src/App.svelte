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
  let contactConfig = $state({}); // Contact configuration from API

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

  onMount(async () => {
    const splashStartTime = Date.now();
    const MINIMUM_SPLASH_DURATION = 2000; // 2 seconds minimum

    // Fetch app configuration first
    try {
      const config = await getAppConfig();
      appName = config.app_name || "Conduit";
      splashText = config.splash_text || "Welcome to Conduit";
      contactConfig = config.contact || {};
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

  function handleLogin(event) {
    const { username, access_token } = event.detail;
    // Save token and user info
    saveToken(access_token);
    saveUser({ username });
    currentUser = username;
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
  function handleResetChat() {
    currentConversationId = null;
    conversationKey++;
  }
</script>

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
      <ProjectSettings project={currentProject} onback={handleBackFromSettings} />
    {:else}
      <div class="app-container">
        <Sidebar
          bind:this={sidebarRef}
          {currentUser}
          {currentConversationId}
          {currentProject}
          {appName}
          contact={contactConfig}
          onlogout={handleLogout}
          onselectconversation={handleSelectConversation}
          onnewconversation={handleNewConversation}
          onnavigate={handleNavigate}
        />
        {#key conversationKey}
          <ChatArea
            {currentUser}
            conversationId={currentConversationId}
            project={currentProject}
            onconversationcreated={handleConversationCreated}
            onmessagesent={handleMessageSent}
            onnewchat={handleResetChat}
          />
        {/key}
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
</style>
