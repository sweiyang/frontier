<script>
  import { onMount } from "svelte";
  import { authFetch, authPost } from "./utils.js";

  let {
    project,
    selectedAgentId = null,
    onselect = (agentId) => {},
    onagentschange = (agents) => {},
    compact = false,
  } = $props();

  // Agents state
  let agents = $state([]);
  let agentsLoading = $state(true);
  let showAgentForm = $state(false);
  let editingAgent = $state(null);
  let agentForm = $state({
    name: "",
    endpoint: "",
    connection_type: "http",
    is_default: false,
    extras: "",
    auth_type: "none",
    auth_credentials: "",
    auth_username: "",
    auth_password: "",
    graph_id: "",
    assistant_id: "",
    assistant_name: "",
    available_assistants: [],
    icon: "",
    openai_model: "",
    system_prompt: "",
    available_models: [],
  });

  let showCredentials = $state(false);
  let fetchingAssistants = $state(false);
  let fetchingModels = $state(false);

  // Version history state
  let showVersionHistory = $state(false);
  let versionHistoryAgent = $state(null);
  let versionHistory = $state([]);
  let versionHistoryLoading = $state(false);

  // Approval notification state
  let showApprovalNotification = $state(false);
  let approvalNotificationMessage = $state("");

  // Compact mode state
  let manageExpanded = $state(false);

  const connectionTypes = ["http", "langgraph", "openai"];
  const authTypes = [
    { value: "none", label: "None" },
    { value: "api_key", label: "API Key" },
    { value: "bearer", label: "Bearer Token" },
    { value: "basic", label: "Basic Auth" },
  ];

  onMount(async () => {
    await loadAgents();
  });

  async function loadAgents() {
    agentsLoading = true;
    try {
      const response = await authFetch(`/projects/${project}/agents`);
      if (response.ok) {
        const data = await response.json();
        agents = data.agents || [];
        onagentschange(agents);
      }
    } catch (error) {
      console.error("Failed to load agents:", error);
    } finally {
      agentsLoading = false;
    }
  }

  function duplicateAgent(agent) {
    openAgentForm(agent);
    editingAgent = null;
  }

  function openAgentForm(agent = null) {
    if (agent) {
      editingAgent = agent;
      const auth = agent.auth || {};
      const authType = auth.auth_type || "none";
      const credentials = auth.credentials || "";
      const extras = agent.extras || {};

      agentForm = {
        name: agent.name,
        endpoint: agent.endpoint,
        connection_type: agent.connection_type,
        is_default: agent.is_default || false,
        extras: agent.extras ? JSON.stringify(agent.extras, null, 2) : "",
        auth_type: authType,
        auth_credentials: typeof credentials === "string" ? credentials : "",
        auth_username:
          typeof credentials === "object" ? credentials.username || "" : "",
        auth_password:
          typeof credentials === "object" ? credentials.password || "" : "",
        graph_id: extras.graph_id || "",
        assistant_id: extras.assistant_id || "",
        assistant_name: agent.name || "",
        available_assistants: [],
        icon: agent.icon || "",
        openai_model: extras.model || "",
        system_prompt: extras.system_prompt || "",
        available_models: [],
      };
    } else {
      editingAgent = null;
      agentForm = {
        name: "",
        endpoint: "",
        connection_type: "http",
        is_default: false,
        extras: "",
        auth_type: "none",
        auth_credentials: "",
        auth_username: "",
        auth_password: "",
        graph_id: "",
        assistant_id: "",
        assistant_name: "",
        available_assistants: [],
        icon: "",
        openai_model: "",
        system_prompt: "",
        available_models: [],
      };
    }
    showAgentForm = true;
  }

  function closeAgentForm() {
    showAgentForm = false;
    editingAgent = null;
    agentForm = {
      name: "",
      endpoint: "",
      connection_type: "http",
      is_default: false,
      extras: "",
      auth_type: "none",
      auth_credentials: "",
      auth_username: "",
      auth_password: "",
      graph_id: "",
      assistant_id: "",
      assistant_name: "",
      available_assistants: [],
      icon: "",
      openai_model: "",
      system_prompt: "",
      available_models: [],
    };
    showCredentials = false;
    fetchingAssistants = false;
  }

  async function saveAgent() {
    let extras = null;
    if (agentForm.extras.trim()) {
      try {
        extras = JSON.parse(agentForm.extras);
      } catch (e) {
        alert("Invalid JSON in extras field");
        return;
      }
    }

    if (agentForm.connection_type === "langgraph") {
      extras = extras || {};
      extras["graph_id"] = agentForm.graph_id;

      if (!agentForm.assistant_name) {
        alert("Please select an assistant for the LangGraph connection");
        return;
      }

      const selectedAssistant = agentForm.available_assistants.find(
        (a) => a.name === agentForm.assistant_name,
      );
      if (selectedAssistant) {
        extras["assistant_id"] = selectedAssistant.assistant_id;
      } else if (agentForm.assistant_id) {
        extras["assistant_id"] = agentForm.assistant_id;
      }
    }

    if (agentForm.connection_type === "openai") {
      extras = extras || {};

      if (!agentForm.openai_model) {
        alert("Please select a model for the OpenAI connection");
        return;
      }
      extras["model"] = agentForm.openai_model;

      if (agentForm.system_prompt.trim()) {
        extras["system_prompt"] = agentForm.system_prompt.trim();
      }
    }

    let auth = null;
    if (agentForm.auth_type !== "none") {
      if (agentForm.auth_type === "basic") {
        auth = {
          auth_type: "basic",
          credentials: {
            username: agentForm.auth_username,
            password: agentForm.auth_password,
          },
        };
      } else {
        auth = {
          auth_type: agentForm.auth_type,
          credentials: agentForm.auth_credentials,
        };
      }
    }

    let agentName;
    if (agentForm.connection_type === "langgraph") {
      agentName = agentForm.assistant_name;
    } else if (agentForm.connection_type === "openai") {
      agentName = agentForm.name || agentForm.openai_model;
    } else {
      agentName = agentForm.name;
    }

    const payload = {
      name: agentName,
      endpoint: agentForm.endpoint,
      connection_type: agentForm.connection_type,
      is_default: agentForm.is_default,
      extras,
      auth,
      icon: agentForm.icon,
    };

    try {
      let response;
      if (editingAgent) {
        response = await authFetch(
          `/projects/${project}/agents/${editingAgent.id}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
          },
        );
      } else {
        response = await authPost(`/projects/${project}/agents`, payload);
      }

      if (response.ok) {
        const result = await response.json();

        if (result.status === "pending_approval") {
          showApprovalNotification = true;
          approvalNotificationMessage = result.message || "Your change request has been submitted and is pending approval.";
          setTimeout(() => {
            showApprovalNotification = false;
          }, 5000);
        }

        await loadAgents();
        closeAgentForm();
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to save agent");
      }
    } catch (error) {
      console.error("Failed to save agent:", error);
    }
  }

  async function fetchLangGraphAssistants() {
    if (!agentForm.endpoint) {
      alert("Please enter an endpoint URL first");
      return;
    }

    fetchingAssistants = true;
    try {
      let auth = null;
      if (agentForm.auth_type !== "none") {
        if (agentForm.auth_type === "basic") {
          auth = {
            auth_type: "basic",
            credentials: {
              username: agentForm.auth_username,
              password: agentForm.auth_password,
            },
          };
        } else {
          auth = {
            auth_type: agentForm.auth_type,
            credentials: agentForm.auth_credentials,
          };
        }
      }

      const response = await authPost("/langgraph/assistants", {
        endpoint: agentForm.endpoint,
        graph_id: agentForm.graph_id || null,
        auth: auth,
      });

      if (response.ok) {
        const data = await response.json();
        agentForm.available_assistants = data.assistants || [];
        if (agentForm.available_assistants.length === 0) {
          alert("No assistants found for this endpoint/graph");
        } else if (agentForm.available_assistants.length === 1) {
          agentForm.assistant_name = agentForm.available_assistants[0].name;
        }
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to fetch assistants");
        agentForm.available_assistants = [];
      }
    } catch (error) {
      console.error("Failed to fetch assistants:", error);
      alert("Failed to fetch assistants: " + error.message);
      agentForm.available_assistants = [];
    } finally {
      fetchingAssistants = false;
    }
  }

  async function fetchOpenAIModels() {
    if (!agentForm.endpoint) {
      alert("Please enter an endpoint URL first");
      return;
    }

    fetchingModels = true;
    try {
      let auth = null;
      if (agentForm.auth_type !== "none") {
        if (agentForm.auth_type === "basic") {
          auth = {
            auth_type: "basic",
            credentials: {
              username: agentForm.auth_username,
              password: agentForm.auth_password,
            },
          };
        } else {
          auth = {
            auth_type: agentForm.auth_type,
            credentials: agentForm.auth_credentials,
          };
        }
      }

      const response = await authPost("/openai/models", {
        endpoint: agentForm.endpoint,
        auth: auth,
      });

      if (response.ok) {
        const data = await response.json();
        agentForm.available_models = data.models || [];
        if (agentForm.available_models.length === 0) {
          alert("No models found for this endpoint");
        } else if (agentForm.available_models.length === 1) {
          agentForm.openai_model = agentForm.available_models[0].id;
        }
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to fetch models");
        agentForm.available_models = [];
      }
    } catch (error) {
      console.error("Failed to fetch models:", error);
      alert("Failed to fetch models: " + error.message);
      agentForm.available_models = [];
    } finally {
      fetchingModels = false;
    }
  }

  async function deleteAgent(agent) {
    if (!confirm(`Delete agent "${agent.name}"?`)) return;

    try {
      const response = await authFetch(
        `/projects/${project}/agents/${agent.id}`,
        {
          method: "DELETE",
        },
      );
      if (response.ok) {
        const result = await response.json();

        if (result.status === "pending_approval") {
          showApprovalNotification = true;
          approvalNotificationMessage = result.message || "Your delete request has been submitted and is pending approval.";
          setTimeout(() => {
            showApprovalNotification = false;
          }, 5000);
        }

        await loadAgents();
      }
    } catch (error) {
      console.error("Failed to delete agent:", error);
    }
  }

  async function openVersionHistory(agent) {
    versionHistoryAgent = agent;
    showVersionHistory = true;
    versionHistoryLoading = true;

    try {
      const response = await authFetch(`/projects/${project}/agents/${agent.id}/versions`);
      if (response.ok) {
        const data = await response.json();
        versionHistory = data.versions || [];
      } else {
        versionHistory = [];
      }
    } catch (error) {
      console.error("Failed to load version history:", error);
      versionHistory = [];
    } finally {
      versionHistoryLoading = false;
    }
  }

  function closeVersionHistory() {
    showVersionHistory = false;
    versionHistoryAgent = null;
    versionHistory = [];
  }

  async function rollbackToVersion(versionNumber) {
    if (!versionHistoryAgent) return;

    if (!confirm(`Rollback "${versionHistoryAgent.name}" to version ${versionNumber}?`)) return;

    try {
      const response = await authPost(
        `/projects/${project}/agents/${versionHistoryAgent.id}/rollback/${versionNumber}`,
        {}
      );

      if (response.ok) {
        const result = await response.json();

        if (result.status === "pending_approval") {
          showApprovalNotification = true;
          approvalNotificationMessage = result.message || "Rollback request submitted for approval.";
          setTimeout(() => {
            showApprovalNotification = false;
          }, 5000);
          closeVersionHistory();
        } else {
          await loadAgents();
          closeVersionHistory();
        }
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to rollback");
      }
    } catch (error) {
      console.error("Failed to rollback:", error);
      alert("Failed to rollback agent");
    }
  }

  function handleIconUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert("Please upload an image file");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      alert("Image size should be less than 5MB");
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      if (e.target && e.target.result && typeof e.target.result === "string") {
        agentForm.icon = e.target.result;
      }
    };
    reader.readAsDataURL(file);
  }
</script>

<div class="agent-manager" class:compact>
  {#if compact}
    <!-- Compact: Agent picker dropdown -->
    <div class="field">
      <label for="compact-agent-picker">Agent</label>
      <select
        id="compact-agent-picker"
        value={selectedAgentId ?? ""}
        onchange={(e) => onselect(e.currentTarget.value ? Number(e.currentTarget.value) : null)}
      >
        <option value="">Default agent</option>
        {#each agents as agent}
          <option value={agent.id}>{agent.name}</option>
        {/each}
      </select>
      {#if selectedAgentId && agents.length && !agents.find(a => a.id === selectedAgentId)}
        <span class="field-warning">Agent no longer exists</span>
      {/if}
    </div>

    <!-- Manage agents toggle -->
    <button
      type="button"
      class="manage-toggle"
      onclick={() => manageExpanded = !manageExpanded}
    >
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        {#if manageExpanded}
          <polyline points="18 15 12 9 6 15" />
        {:else}
          <polyline points="6 9 12 15 18 9" />
        {/if}
      </svg>
      Manage agents
    </button>

    {#if manageExpanded}
      {#if showAgentForm}
        <!-- Compact agent form -->
        <div class="compact-form-wrapper">
          <button class="btn-icon back-btn" onclick={closeAgentForm} title="Back to Agents">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
          </button>
          <span class="compact-form-title">{editingAgent ? "Edit" : "Add"} Agent</span>
        </div>

        <form
          class="agent-inline-form"
          onsubmit={(e) => { e.preventDefault(); saveAgent(); }}
        >
          {@render agentFormFields()}
        </form>
      {:else}
        <!-- Compact agent list as cards -->
        <div class="compact-agent-list">
          {#if agentsLoading}
            <div class="loading">Loading...</div>
          {:else if agents.length === 0}
            <div class="empty-state-compact">No agents configured.</div>
          {:else}
            {#each agents as agent}
              <div
                class="agent-card"
                class:selected={selectedAgentId === agent.id}
              >
                <div class="agent-card-main" onclick={() => onselect(agent.id)}>
                  <div class="agent-card-info">
                    {#if agent.icon}
                      <img src={agent.icon} alt="" class="agent-card-icon" />
                    {:else}
                      <div class="agent-card-icon-placeholder">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <circle cx="12" cy="12" r="10" />
                          <path d="M8 14s1.5 2 4 2 4-2 4-2" />
                          <line x1="9" y1="9" x2="9.01" y2="9" />
                          <line x1="15" y1="9" x2="15.01" y2="9" />
                        </svg>
                      </div>
                    {/if}
                    <div class="agent-card-text">
                      <span class="agent-card-name" title={agent.name}>{agent.name}</span>
                      <span class="badge badge-{agent.connection_type}">{agent.connection_type}</span>
                    </div>
                  </div>
                  <div class="agent-card-endpoint" title={agent.endpoint}>{agent.endpoint}</div>
                </div>
                <div class="agent-card-actions">
                  <button class="btn-icon" onclick={() => openAgentForm(agent)} title="Edit">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                    </svg>
                  </button>
                  <button class="btn-icon btn-danger" onclick={() => deleteAgent(agent)} title="Delete">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="3 6 5 6 21 6" />
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                    </svg>
                  </button>
                </div>
              </div>
            {/each}
          {/if}
          <button class="btn btn-primary btn-sm add-agent-btn" onclick={() => openAgentForm()}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Add Agent
          </button>
        </div>
      {/if}
    {/if}
  {:else}
    <!-- Full mode (ProjectSettings) -->
    {#if !showAgentForm}
      <div class="section-header">
        <h2>AI Agents</h2>
        <button class="btn btn-primary" onclick={() => openAgentForm()}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
          Add Agent
        </button>
      </div>

      {#if agentsLoading}
        <div class="loading">Loading agents...</div>
      {:else if agents.length === 0}
        <div class="empty-state">
          <p>No agents configured yet.</p>
          <p class="hint">
            Add an agent endpoint to connect AI services to this project.
          </p>
        </div>
      {:else}
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Endpoint</th>
                <th>Type</th>
                <th>Version</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {#each agents as agent}
                <tr>
                  <td class="cell-name">
                    {agent.name}
                    {#if agent.is_default}
                      <span class="badge badge-default">Default</span>
                    {/if}
                  </td>
                  <td class="cell-endpoint">
                    <code>{agent.endpoint}</code>
                  </td>
                  <td>
                    <span class="badge badge-{agent.connection_type}"
                      >{agent.connection_type}</span
                    >
                  </td>
                  <td>
                    <button
                      class="version-badge"
                      onclick={() => openVersionHistory(agent)}
                      title="View version history"
                    >
                      v{agent.current_version || 0}
                    </button>
                  </td>
                  <td class="cell-actions">
                    <button
                      class="btn-icon"
                      onclick={() => openAgentForm(agent)}
                      title="Edit"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                      </svg>
                    </button>
                    <button
                      class="btn-icon"
                      onclick={() => duplicateAgent(agent)}
                      title="Duplicate"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
                        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
                      </svg>
                    </button>
                    <button
                      class="btn-icon btn-danger"
                      onclick={() => deleteAgent(agent)}
                      title="Delete"
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="3 6 5 6 21 6" />
                        <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      </svg>
                    </button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/if}
    {:else}
      <!-- Inline Agent Form -->
      <div class="section-header">
        <div class="header-left">
          <button class="btn-icon back-btn" onclick={closeAgentForm} title="Back to Agents">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M19 12H5" />
              <polyline points="12 19 5 12 12 5" />
            </svg>
          </button>
          <h2>{editingAgent ? "Edit Agent" : "Add Agent"}</h2>
        </div>
      </div>

      <form
        class="agent-inline-form"
        onsubmit={(e) => { e.preventDefault(); saveAgent(); }}
      >
        {@render agentFormFields()}
      </form>
    {/if}
  {/if}
</div>

{#snippet agentFormFields()}
  <!-- Connection Type -->
  <div class="form-group">
    <label for="agent-type">Connection Type</label>
    <select id="agent-type" bind:value={agentForm.connection_type}>
      {#each connectionTypes as type}
        <option value={type}>{type.toUpperCase()}</option>
      {/each}
    </select>
  </div>

  <!-- Endpoint URL -->
  <div class="form-group">
    <label for="agent-endpoint">Endpoint URL</label>
    <input
      id="agent-endpoint"
      type="url"
      placeholder="e.g., https://api.example.com/agent"
      bind:value={agentForm.endpoint}
      required
    />
  </div>

  <!-- Icon Upload -->
  <div class="form-group">
    <label for="agent-icon">Icon (optional)</label>
    <div class="icon-upload-container">
      {#if agentForm.icon}
        <div class="icon-preview-wrapper">
          <img
            src={agentForm.icon}
            alt="Agent icon preview"
            class="icon-preview"
          />
          <button
            type="button"
            class="btn-icon btn-danger remove-icon-btn"
            onclick={() => (agentForm.icon = "")}
            title="Remove icon"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>
      {/if}
      <div class="file-input-wrapper">
        <input
          id="agent-icon"
          type="file"
          accept="image/*"
          onchange={handleIconUpload}
          class="file-input"
        />
        <div class="file-input-button">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
          <span>{agentForm.icon ? "Change Icon" : "Upload Icon"}</span>
        </div>
      </div>
    </div>
    <p class="form-hint">
      Upload an image (JPG, PNG, SVG) for the agent profile. Max 5MB.
    </p>
  </div>

  <!-- LangGraph-specific fields -->
  {#if agentForm.connection_type === "langgraph"}
    <div class="form-group">
      <label for="agent-graph-id">Graph ID</label>
      <input
        id="agent-graph-id"
        type="text"
        placeholder="e.g., my-graph"
        bind:value={agentForm.graph_id}
      />
      <p class="form-hint">
        The graph ID to filter assistants. Leave empty to list all.
      </p>
    </div>

    {@render authFields()}

    <!-- Fetch Assistants Button -->
    <div class="form-group">
      <button
        type="button"
        class="btn btn-secondary fetch-assistants-btn"
        onclick={fetchLangGraphAssistants}
        disabled={fetchingAssistants || !agentForm.endpoint}
      >
        {#if fetchingAssistants}
          <svg class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-linecap="round" />
          </svg>
          Fetching...
        {:else}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
          </svg>
          Fetch Assistants
        {/if}
      </button>
    </div>

    <!-- Assistant Selection Dropdown -->
    {#if agentForm.available_assistants.length > 0}
      <div class="form-group">
        <label for="agent-assistant">Select Assistant</label>
        <select id="agent-assistant" bind:value={agentForm.assistant_name} required>
          <option value="">-- Select an assistant --</option>
          {#each agentForm.available_assistants as assistant}
            <option value={assistant.name}>{assistant.name || assistant.assistant_id}</option>
          {/each}
        </select>
        <p class="form-hint">
          The selected assistant will be used for conversations.
        </p>
      </div>
    {/if}
  {:else if agentForm.connection_type === "openai"}
    <!-- OpenAI-specific fields -->
    {@render authFields()}

    <!-- Fetch Models Button -->
    <div class="form-group">
      <button
        type="button"
        class="btn btn-secondary fetch-assistants-btn"
        onclick={fetchOpenAIModels}
        disabled={fetchingModels || !agentForm.endpoint}
      >
        {#if fetchingModels}
          <svg class="spinner" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10" stroke-dasharray="32" stroke-linecap="round" />
          </svg>
          Fetching...
        {:else}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9" />
          </svg>
          Fetch Models
        {/if}
      </button>
    </div>

    <!-- Model Selection Dropdown -->
    {#if agentForm.available_models.length > 0}
      <div class="form-group">
        <label for="agent-model">Select Model</label>
        <select id="agent-model" bind:value={agentForm.openai_model} required>
          <option value="">-- Select a model --</option>
          {#each agentForm.available_models as model}
            <option value={model.id}>{model.name}</option>
          {/each}
        </select>
        <p class="form-hint">
          The selected model will be used for conversations.
        </p>
      </div>
    {/if}

    <!-- Agent Name -->
    <div class="form-group">
      <label for="agent-name">Name (optional)</label>
      <input
        id="agent-name"
        type="text"
        placeholder="Defaults to model name"
        bind:value={agentForm.name}
      />
      <p class="form-hint">
        A display name for this agent. Leave blank to use the model name.
      </p>
    </div>

    <!-- System Prompt -->
    <div class="form-group">
      <label for="agent-system-prompt">System Prompt (optional)</label>
      <textarea
        id="agent-system-prompt"
        placeholder="e.g., You are a helpful coding assistant..."
        bind:value={agentForm.system_prompt}
        rows="4"
      ></textarea>
      <p class="form-hint">
        A system message prepended to every conversation with this agent.
      </p>
    </div>
  {:else}
    <!-- HTTP-specific fields: Name -->
    <div class="form-group">
      <label for="agent-name">Name</label>
      <input
        id="agent-name"
        type="text"
        placeholder="e.g., Code Assistant"
        bind:value={agentForm.name}
        required
      />
    </div>

    {@render authFields()}
  {/if}

  <div class="form-group form-group-checkbox">
    <label class="checkbox-label">
      <input type="checkbox" bind:checked={agentForm.is_default} />
      <span class="checkbox-text">Set as default agent</span>
    </label>
    <p class="form-hint">
      The default agent will be used for new conversations in this project.
    </p>
  </div>
  <div class="form-group">
    <label for="agent-extras">Extras (JSON, optional)</label>
    <textarea
      id="agent-extras"
      placeholder={`{"api_key": "...", "model": "..."}`}
      bind:value={agentForm.extras}
      rows="4"
    ></textarea>
  </div>

  <div class="form-actions">
    <button type="button" class="btn btn-secondary" onclick={closeAgentForm}>Cancel</button>
    <button type="submit" class="btn btn-primary">
      {editingAgent ? "Update" : "Add"} Agent
    </button>
  </div>
{/snippet}

{#snippet authFields()}
  <div class="form-group">
    <label for="agent-auth">Authentication</label>
    <select id="agent-auth" bind:value={agentForm.auth_type}>
      {#each authTypes as type}
        <option value={type.value}>{type.label}</option>
      {/each}
    </select>
  </div>
  {#if agentForm.auth_type === "api_key" || agentForm.auth_type === "bearer"}
    <div class="form-group auth-field">
      <label for="agent-credentials"
        >{agentForm.auth_type === "api_key" ? "API Key" : "Token"}</label
      >
      <div class="password-input-wrapper">
        <input
          id="agent-credentials"
          type={showCredentials ? "text" : "password"}
          placeholder={agentForm.auth_type === "api_key" ? "Enter API key" : "Enter bearer token"}
          bind:value={agentForm.auth_credentials}
        />
        <button
          type="button"
          class="toggle-visibility"
          onclick={() => (showCredentials = !showCredentials)}
          title={showCredentials ? "Hide" : "Show"}
        >
          {#if showCredentials}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
          {:else}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          {/if}
        </button>
      </div>
    </div>
  {:else if agentForm.auth_type === "basic"}
    <div class="form-group auth-field">
      <label for="agent-username">Username</label>
      <input
        id="agent-username"
        type="text"
        placeholder="Username"
        bind:value={agentForm.auth_username}
      />
    </div>
    <div class="form-group auth-field">
      <label for="agent-password">Password</label>
      <div class="password-input-wrapper">
        <input
          id="agent-password"
          type={showCredentials ? "text" : "password"}
          placeholder="Password"
          bind:value={agentForm.auth_password}
        />
        <button
          type="button"
          class="toggle-visibility"
          onclick={() => (showCredentials = !showCredentials)}
          title={showCredentials ? "Hide" : "Show"}
        >
          {#if showCredentials}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24" />
              <line x1="1" y1="1" x2="23" y2="23" />
            </svg>
          {:else}
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          {/if}
        </button>
      </div>
    </div>
  {/if}
{/snippet}

<!-- Version History Modal -->
{#if showVersionHistory && versionHistoryAgent}
  <div class="modal-overlay" onclick={closeVersionHistory} onkeydown={(e) => e.key === 'Escape' && closeVersionHistory()} role="dialog" aria-modal="true" tabindex="-1">
    <div class="modal version-history-modal" onclick={(e) => e.stopPropagation()} role="document">
      <div class="modal-header">
        <h2>Version History: {versionHistoryAgent.name}</h2>
        <button class="close-btn" onclick={closeVersionHistory} aria-label="Close">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div class="modal-body">
        {#if versionHistoryLoading}
          <div class="loading-state">Loading version history...</div>
        {:else if versionHistory.length === 0}
          <div class="empty-state">
            <p>No version history available.</p>
            <p class="hint">Versions are created when agent configurations are modified.</p>
          </div>
        {:else}
          <div class="version-list">
            {#each versionHistory as version, index}
              <div class="version-item" class:current={index === 0}>
                <div class="version-header">
                  <div class="version-info">
                    <span class="version-number">v{version.version_number}</span>
                    {#if index === 0}
                      <span class="badge badge-current">Current</span>
                    {/if}
                  </div>
                  <div class="version-meta">
                    <span class="version-author">by {version.created_by_username || 'Unknown'}</span>
                    <span class="version-date">{new Date(version.created_at).toLocaleString()}</span>
                  </div>
                </div>
                <div class="version-snapshot">
                  <div class="snapshot-row">
                    <span class="snapshot-label">Endpoint:</span>
                    <code>{version.snapshot?.endpoint || '-'}</code>
                  </div>
                  <div class="snapshot-row">
                    <span class="snapshot-label">Type:</span>
                    <span class="badge badge-{version.snapshot?.connection_type}">{version.snapshot?.connection_type || '-'}</span>
                  </div>
                  {#if version.snapshot?.extras}
                    <div class="snapshot-row">
                      <span class="snapshot-label">Extras:</span>
                      <code class="extras-code">{JSON.stringify(version.snapshot.extras)}</code>
                    </div>
                  {/if}
                </div>
                {#if index > 0}
                  <div class="version-actions">
                    <button
                      class="btn btn-secondary btn-sm"
                      onclick={() => rollbackToVersion(version.version_number)}
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="1 4 1 10 7 10" />
                        <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                      </svg>
                      Rollback to this version
                    </button>
                  </div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<!-- Approval Notification Toast -->
{#if showApprovalNotification}
  <div class="approval-toast">
    <div class="approval-toast-content">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10" />
        <path d="M12 16v-4" />
        <path d="M12 8h.01" />
      </svg>
      <div class="approval-toast-text">
        <strong>Change Request Submitted</strong>
        <p>{approvalNotificationMessage}</p>
      </div>
      <button class="approval-toast-close" onclick={() => showApprovalNotification = false} aria-label="Close notification">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  </div>
{/if}

<style>
  .agent-manager {
    width: 100%;
  }

  /* ========== Shared styles ========== */
  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: var(--spacing-lg);
  }

  .section-header h2 {
    font-size: 1.1rem;
    font-weight: 600;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-md);
    font-weight: 500;
    font-size: 0.9rem;
    transition: all 0.2s ease;
  }

  .btn-primary {
    background-color: var(--primary-accent);
    color: white;
  }

  .btn-primary:hover {
    background-color: var(--primary-accent-hover);
  }

  .btn-secondary {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }

  .btn-secondary:hover {
    background-color: var(--bg-secondary);
  }

  .btn-sm {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: 0.85rem;
  }

  .btn-icon {
    padding: var(--spacing-xs);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    transition: all 0.2s ease;
  }

  .btn-icon:hover {
    background-color: rgba(0, 0, 0, 0.05);
    color: var(--text-primary);
  }

  .btn-icon.btn-danger:hover {
    background-color: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }

  .loading {
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
  }

  .empty-state {
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
  }

  .empty-state .hint {
    font-size: 0.9rem;
    margin-top: var(--spacing-xs);
    opacity: 0.7;
  }

  /* ========== Table (full mode) ========== */
  .table-container {
    overflow-x: auto;
  }

  .data-table {
    width: 100%;
    border-collapse: collapse;
  }

  .data-table th,
  .data-table td {
    padding: var(--spacing-sm) var(--spacing-md);
    text-align: left;
    border-bottom: 1px solid var(--border-color);
  }

  .data-table th {
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    color: var(--text-secondary);
    background-color: var(--bg-primary);
  }

  .data-table td {
    font-size: 0.95rem;
  }

  .data-table code {
    font-size: 0.85rem;
    padding: 2px 6px;
    background-color: var(--bg-primary);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
  }

  .cell-name {
    font-weight: 500;
  }

  .cell-endpoint {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .cell-actions {
    display: flex;
    gap: var(--spacing-xs);
  }

  /* ========== Badges ========== */
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .badge-http {
    background-color: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
  }

  .badge-langgraph {
    background-color: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }

  .badge-openai {
    background-color: rgba(139, 92, 246, 0.1);
    color: #8b5cf6;
  }

  .badge-default {
    background-color: rgba(245, 158, 11, 0.15);
    color: var(--primary-accent);
    margin-left: var(--spacing-xs);
  }

  .badge-current {
    background: var(--primary-accent);
    color: white;
  }

  /* ========== Form ========== */
  .form-group {
    margin-bottom: var(--spacing-md);
  }

  .compact .form-group {
    margin-bottom: 8px;
  }

  .form-group label {
    display: block;
    font-size: 0.9rem;
    font-weight: 500;
    margin-bottom: var(--spacing-xs);
  }

  .compact .form-group label {
    font-size: 0.8rem;
  }

  .form-group input,
  .form-group select,
  .form-group textarea {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background-color: var(--bg-primary);
    font-size: 0.95rem;
  }

  .compact .form-group input,
  .compact .form-group select,
  .compact .form-group textarea {
    font-size: 0.85rem;
    padding: 0.3rem 0.5rem;
  }

  .form-group input:focus,
  .form-group select:focus,
  .form-group textarea:focus {
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
  }

  .form-group textarea {
    resize: vertical;
    font-family: monospace;
    font-size: 0.85rem;
  }

  .form-group-checkbox {
    padding: var(--spacing-sm) 0;
  }

  .auth-field {
    padding-left: var(--spacing-md);
    border-left: 2px solid var(--primary-accent);
    margin-left: var(--spacing-xs);
    animation: slideIn 0.2s ease-out;
  }

  .password-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .password-input-wrapper input {
    width: 100%;
    padding-right: 44px;
  }

  .toggle-visibility {
    position: absolute;
    right: var(--spacing-sm);
    padding: var(--spacing-xs);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    background: transparent;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.2s ease;
  }

  .toggle-visibility:hover {
    color: var(--text-primary);
    background-color: var(--bg-secondary);
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    cursor: pointer;
    font-weight: normal;
  }

  .checkbox-label input[type="checkbox"] {
    width: 18px;
    height: 18px;
    accent-color: var(--primary-accent);
    cursor: pointer;
  }

  .checkbox-text {
    font-size: 0.95rem;
    font-weight: 500;
  }

  .form-hint {
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-top: var(--spacing-xs);
    margin-left: 26px;
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-xl);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-color);
  }

  .compact .form-actions {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-sm);
  }

  /* ========== Icon upload ========== */
  .icon-upload-container {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
    margin-bottom: var(--spacing-xs);
  }

  .icon-preview-wrapper {
    position: relative;
    width: 48px;
    height: 48px;
    border-radius: var(--radius-md);
    overflow: hidden;
    border: 1px solid var(--border-color);
  }

  .compact .icon-preview-wrapper {
    width: 32px;
    height: 32px;
  }

  .icon-preview {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .remove-icon-btn {
    position: absolute;
    top: 0;
    right: 0;
    width: 16px;
    height: 16px;
    background: rgba(0, 0, 0, 0.5);
    color: white;
    border-radius: 0 0 0 4px;
    padding: 0;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .remove-icon-btn:hover {
    background: rgba(220, 38, 38, 0.8);
  }

  .file-input-wrapper {
    position: relative;
    overflow: hidden;
    display: inline-block;
  }

  .file-input {
    position: absolute;
    left: 0;
    top: 0;
    opacity: 0;
    width: 100%;
    height: 100%;
    cursor: pointer;
  }

  .file-input-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    background-color: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    color: var(--text-primary);
    font-size: 0.9rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .file-input:hover + .file-input-button {
    background-color: var(--bg-secondary);
    border-color: var(--text-secondary);
  }

  .spinner {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .fetch-assistants-btn {
    width: 100%;
    justify-content: center;
  }

  /* ========== Version badge ========== */
  .version-badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .version-badge:hover {
    background: var(--primary-accent);
    color: white;
    border-color: var(--primary-accent);
  }

  /* ========== Modal ========== */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.15s ease-out;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
  }

  .modal {
    background-color: var(--bg-primary);
    border-radius: var(--radius-lg);
    width: 100%;
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: var(--shadow-lg);
    animation: slideUp 0.2s ease-out;
  }

  @keyframes slideUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--border-color);
  }

  .modal-header h2 {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 0;
  }

  .modal-body {
    padding: var(--spacing-lg);
  }

  .close-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-secondary);
    padding: var(--spacing-xs);
    border-radius: var(--radius-sm);
    transition: color 0.15s ease;
  }

  .close-btn:hover {
    color: var(--text-primary);
  }

  /* ========== Version history ========== */
  .version-history-modal {
    max-width: 700px;
    max-height: 80vh;
    overflow-y: auto;
  }

  .version-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .version-item {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
  }

  .version-item.current {
    border-color: var(--primary-accent);
    background: var(--color-primary-light, rgba(255, 165, 0, 0.05));
  }

  .version-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-sm);
  }

  .version-info {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .version-number {
    font-weight: 600;
    font-size: 1rem;
    color: var(--text-primary);
  }

  .version-meta {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 2px;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .version-snapshot {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    font-size: 0.85rem;
  }

  .snapshot-row {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .snapshot-label {
    font-weight: 500;
    color: var(--text-secondary);
    min-width: 70px;
  }

  .extras-code {
    font-size: 0.75rem;
    max-width: 400px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .version-actions {
    margin-top: var(--spacing-md);
    padding-top: var(--spacing-sm);
    border-top: 1px solid var(--border-color);
  }

  .loading-state {
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
  }

  /* ========== Approval toast ========== */
  .approval-toast {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 10000;
    animation: toastSlideIn 0.3s ease-out;
  }

  @keyframes toastSlideIn {
    from { transform: translateX(100%); opacity: 0; }
    to { transform: translateX(0); opacity: 1; }
  }

  .approval-toast-content {
    display: flex;
    align-items: flex-start;
    gap: var(--spacing-md);
    padding: var(--spacing-md) var(--spacing-lg);
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border: 1px solid #f59e0b;
    border-radius: var(--radius-lg);
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
    max-width: 400px;
  }

  .approval-toast-content > svg {
    color: #d97706;
    flex-shrink: 0;
    margin-top: 2px;
  }

  .approval-toast-text {
    flex: 1;
  }

  .approval-toast-text strong {
    display: block;
    color: #92400e;
    font-size: 0.95rem;
    margin-bottom: 4px;
  }

  .approval-toast-text p {
    color: #a16207;
    font-size: 0.875rem;
    margin: 0;
    line-height: 1.4;
  }

  .approval-toast-close {
    background: none;
    border: none;
    padding: 4px;
    cursor: pointer;
    color: #a16207;
    border-radius: var(--radius-sm);
    transition: background-color 0.15s ease;
    flex-shrink: 0;
  }

  .approval-toast-close:hover {
    background-color: rgba(0, 0, 0, 0.1);
  }

  @keyframes slideIn {
    from { opacity: 0; transform: translateX(-10px); }
    to { opacity: 1; transform: translateX(0); }
  }

  /* ========== Compact mode ========== */
  .compact .field {
    margin-bottom: 0.5rem;
  }

  .compact .field label {
    display: block;
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--text-secondary);
    margin-bottom: 0.2rem;
  }

  .compact .field select {
    width: 100%;
    padding: 0.3rem 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    background: var(--bg-primary);
  }

  .field-warning {
    display: block;
    margin-top: 0.25rem;
    font-size: 0.75rem;
    color: #dc2626;
  }

  .manage-toggle {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    width: 100%;
    padding: 0.4rem 0.5rem;
    margin-top: 0.5rem;
    border: none;
    background: none;
    color: var(--text-secondary);
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    border-radius: var(--radius-sm);
    transition: background-color 0.12s ease;
  }

  .manage-toggle:hover {
    background-color: rgba(0, 0, 0, 0.04);
    color: var(--text-primary);
  }

  .compact-agent-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    margin-top: 0.5rem;
  }

  .agent-card {
    display: flex;
    flex-direction: column;
    padding: 0.4rem 0.5rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    background: var(--bg-primary);
    transition: all 0.12s ease;
  }

  .agent-card:hover {
    background: rgba(0, 0, 0, 0.02);
  }

  .agent-card.selected {
    border-left: 3px solid var(--primary-accent);
  }

  .agent-card-main {
    cursor: pointer;
  }

  .agent-card-info {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .agent-card-icon {
    width: 24px;
    height: 24px;
    border-radius: var(--radius-sm);
    object-fit: cover;
    flex-shrink: 0;
  }

  .agent-card-icon-placeholder {
    width: 24px;
    height: 24px;
    border-radius: var(--radius-sm);
    background: var(--bg-secondary);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    color: var(--text-secondary);
  }

  .agent-card-text {
    display: flex;
    align-items: center;
    gap: 0.3rem;
    min-width: 0;
    flex: 1;
  }

  .agent-card-name {
    font-size: 0.85rem;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .agent-card-endpoint {
    font-size: 0.7rem;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    margin-top: 0.15rem;
    padding-left: 28px;
  }

  .agent-card-actions {
    display: flex;
    gap: 0.2rem;
    justify-content: flex-end;
    margin-top: 0.25rem;
  }

  .agent-card-actions .btn-icon {
    padding: 2px;
  }

  .add-agent-btn {
    width: 100%;
    justify-content: center;
    margin-top: 0.25rem;
  }

  .compact-form-wrapper {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    margin-top: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .compact-form-title {
    font-size: 0.85rem;
    font-weight: 600;
  }

  .empty-state-compact {
    padding: 0.75rem;
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.8rem;
  }
</style>
