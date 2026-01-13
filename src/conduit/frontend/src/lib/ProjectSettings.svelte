<script>
  import { onMount } from "svelte";
  import { authFetch, authPost } from "./auth.js";

  let {
    project = "",
    onback = () => {},
  } = $props();

  // Tab state
  let activeTab = $state("agents"); // "agents" | "rbac"

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
  });

  // AD Groups state
  let adGroups = $state([]);
  let groupsLoading = $state(true);
  let ldapSearchQuery = $state("");
  let ldapSearchResults = $state([]);
  let ldapSearching = $state(false);
  let showGroupForm = $state(false);
  let selectedGroup = $state(null);
  let groupRole = $state("member");

  const connectionTypes = ["http", "websocket", "grpc"];

  onMount(async () => {
    await Promise.all([loadAgents(), loadADGroups()]);
  });

  // ==========================================================================
  // Agents Functions
  // ==========================================================================

  async function loadAgents() {
    agentsLoading = true;
    try {
      const response = await authFetch(`/projects/${project}/agents`);
      if (response.ok) {
        const data = await response.json();
        agents = data.agents || [];
      }
    } catch (error) {
      console.error("Failed to load agents:", error);
    } finally {
      agentsLoading = false;
    }
  }

  function openAgentForm(agent = null) {
    if (agent) {
      editingAgent = agent;
      agentForm = {
        name: agent.name,
        endpoint: agent.endpoint,
        connection_type: agent.connection_type,
        is_default: agent.is_default || false,
        extras: agent.extras ? JSON.stringify(agent.extras, null, 2) : "",
      };
    } else {
      editingAgent = null;
      agentForm = { name: "", endpoint: "", connection_type: "http", is_default: false, extras: "" };
    }
    showAgentForm = true;
  }

  function closeAgentForm() {
    showAgentForm = false;
    editingAgent = null;
    agentForm = { name: "", endpoint: "", connection_type: "http", is_default: false, extras: "" };
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

    const payload = {
      name: agentForm.name,
      endpoint: agentForm.endpoint,
      connection_type: agentForm.connection_type,
      is_default: agentForm.is_default,
      extras,
    };

    try {
      let response;
      if (editingAgent) {
        response = await authFetch(`/projects/${project}/agents/${editingAgent.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
      } else {
        response = await authPost(`/projects/${project}/agents`, payload);
      }

      if (response.ok) {
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

  async function deleteAgent(agent) {
    if (!confirm(`Delete agent "${agent.name}"?`)) return;

    try {
      const response = await authFetch(`/projects/${project}/agents/${agent.id}`, {
        method: "DELETE",
      });
      if (response.ok) {
        await loadAgents();
      }
    } catch (error) {
      console.error("Failed to delete agent:", error);
    }
  }

  // ==========================================================================
  // AD Groups / RBAC Functions
  // ==========================================================================

  async function loadADGroups() {
    groupsLoading = true;
    try {
      const response = await authFetch(`/projects/${project}/groups`);
      if (response.ok) {
        const data = await response.json();
        adGroups = data.groups || [];
      }
    } catch (error) {
      console.error("Failed to load AD groups:", error);
    } finally {
      groupsLoading = false;
    }
  }

  async function searchLDAP() {
    if (ldapSearchQuery.length < 2) {
      ldapSearchResults = [];
      return;
    }

    ldapSearching = true;
    try {
      const response = await authFetch(`/ldap/search?q=${encodeURIComponent(ldapSearchQuery)}&type=group`);
      if (response.ok) {
        const data = await response.json();
        ldapSearchResults = data.results || [];
      }
    } catch (error) {
      console.error("LDAP search failed:", error);
    } finally {
      ldapSearching = false;
    }
  }

  function selectLDAPResult(result) {
    selectedGroup = result;
    showGroupForm = true;
    ldapSearchQuery = "";
    ldapSearchResults = [];
  }

  function closeGroupForm() {
    showGroupForm = false;
    selectedGroup = null;
    groupRole = "member";
  }

  async function addADGroup() {
    if (!selectedGroup) return;

    try {
      const response = await authPost(`/projects/${project}/groups`, {
        group_dn: selectedGroup.dn,
        group_name: selectedGroup.name,
        role: groupRole,
      });

      if (response.ok) {
        await loadADGroups();
        closeGroupForm();
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to add group");
      }
    } catch (error) {
      console.error("Failed to add AD group:", error);
    }
  }

  async function updateGroupRole(group, newRole) {
    try {
      const response = await authFetch(`/projects/${project}/groups/${group.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole }),
      });
      if (response.ok) {
        await loadADGroups();
      }
    } catch (error) {
      console.error("Failed to update group role:", error);
    }
  }

  async function removeADGroup(group) {
    if (!confirm(`Remove group "${group.group_name}" from project?`)) return;

    try {
      const response = await authFetch(`/projects/${project}/groups/${group.id}`, {
        method: "DELETE",
      });
      if (response.ok) {
        await loadADGroups();
      }
    } catch (error) {
      console.error("Failed to remove AD group:", error);
    }
  }

  // Debounced LDAP search
  let searchTimeout;
  function handleSearchInput(e) {
    ldapSearchQuery = e.target.value;
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(searchLDAP, 300);
  }
</script>

<div class="settings-container">
  <header class="settings-header">
    <button class="back-button" onclick={onback}>
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M19 12H5"/>
        <polyline points="12 19 5 12 12 5"/>
      </svg>
      <span>Back</span>
    </button>
    <h1 class="settings-title">
      <span class="project-name">{project}</span>
      <span class="settings-label">Settings</span>
    </h1>
  </header>

  <div class="tabs">
    <button
      class="tab"
      class:active={activeTab === "agents"}
      onclick={() => (activeTab = "agents")}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
        <circle cx="8.5" cy="8.5" r="1.5"/>
        <polyline points="21 15 16 10 5 21"/>
      </svg>
      Agents
    </button>
    <button
      class="tab"
      class:active={activeTab === "rbac"}
      onclick={() => (activeTab = "rbac")}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
      Access Control
    </button>
  </div>

  <div class="tab-content">
    {#if activeTab === "agents"}
      <!-- Agents Section -->
      <div class="section">
        <div class="section-header">
          <h2>AI Agents</h2>
          <button class="btn btn-primary" onclick={() => openAgentForm()}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="5" x2="12" y2="19"/>
              <line x1="5" y1="12" x2="19" y2="12"/>
            </svg>
            Add Agent
          </button>
        </div>

        {#if agentsLoading}
          <div class="loading">Loading agents...</div>
        {:else if agents.length === 0}
          <div class="empty-state">
            <p>No agents configured yet.</p>
            <p class="hint">Add an agent endpoint to connect AI services to this project.</p>
          </div>
        {:else}
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Endpoint</th>
                  <th>Type</th>
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
                      <span class="badge badge-{agent.connection_type}">{agent.connection_type}</span>
                    </td>
                    <td class="cell-actions">
                      <button class="btn-icon" onclick={() => openAgentForm(agent)} title="Edit">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                      </button>
                      <button class="btn-icon btn-danger" onclick={() => deleteAgent(agent)} title="Delete">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <polyline points="3 6 5 6 21 6"/>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    {:else}
      <!-- RBAC Section -->
      <div class="section">
        <div class="section-header">
          <h2>AD Groups</h2>
        </div>

        <div class="search-container">
          <label for="ldap-search">Search Active Directory</label>
          <div class="search-input-wrapper">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              id="ldap-search"
              type="text"
              placeholder="Search for groups..."
              value={ldapSearchQuery}
              oninput={handleSearchInput}
            />
            {#if ldapSearching}
              <span class="search-spinner"></span>
            {/if}
          </div>

          {#if ldapSearchResults.length > 0}
            <div class="search-results">
              {#each ldapSearchResults as result}
                <button class="search-result-item" onclick={() => selectLDAPResult(result)}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                  </svg>
                  <div class="result-info">
                    <span class="result-name">{result.name}</span>
                    <span class="result-dn">{result.dn}</span>
                  </div>
                </button>
              {/each}
            </div>
          {/if}
        </div>

        {#if groupsLoading}
          <div class="loading">Loading groups...</div>
        {:else if adGroups.length === 0}
          <div class="empty-state">
            <p>No AD groups added yet.</p>
            <p class="hint">Search for Active Directory groups above to add them to this project.</p>
          </div>
        {:else}
          <div class="table-container">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Group Name</th>
                  <th>Distinguished Name</th>
                  <th>Role</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {#each adGroups as group}
                  <tr>
                    <td class="cell-name">{group.group_name}</td>
                    <td class="cell-dn">
                      <code>{group.group_dn}</code>
                    </td>
                    <td>
                      <select
                        class="role-select"
                        value={group.role}
                        onchange={(e) => updateGroupRole(group, e.target.value)}
                      >
                        <option value="member">Member</option>
                        <option value="admin">Admin</option>
                      </select>
                    </td>
                    <td class="cell-actions">
                      <button class="btn-icon btn-danger" onclick={() => removeADGroup(group)} title="Remove">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                          <polyline points="3 6 5 6 21 6"/>
                          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<!-- Agent Form Modal -->
{#if showAgentForm}
  <div class="modal-overlay" onclick={closeAgentForm}>
    <div class="modal" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h3>{editingAgent ? "Edit Agent" : "Add Agent"}</h3>
        <button class="modal-close" onclick={closeAgentForm}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <form class="modal-body" onsubmit={(e) => { e.preventDefault(); saveAgent(); }}>
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
        <div class="form-group">
          <label for="agent-type">Connection Type</label>
          <select id="agent-type" bind:value={agentForm.connection_type}>
            {#each connectionTypes as type}
              <option value={type}>{type.toUpperCase()}</option>
            {/each}
          </select>
        </div>
        <div class="form-group form-group-checkbox">
          <label class="checkbox-label">
            <input
              type="checkbox"
              bind:checked={agentForm.is_default}
            />
            <span class="checkbox-text">Set as default agent</span>
          </label>
          <p class="form-hint">The default agent will be used for new conversations in this project.</p>
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
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" onclick={closeAgentForm}>Cancel</button>
          <button type="submit" class="btn btn-primary">
            {editingAgent ? "Update" : "Add"} Agent
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<!-- Add Group Form Modal -->
{#if showGroupForm && selectedGroup}
  <div class="modal-overlay" onclick={closeGroupForm}>
    <div class="modal" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h3>Add AD Group</h3>
        <button class="modal-close" onclick={closeGroupForm}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <form class="modal-body" onsubmit={(e) => { e.preventDefault(); addADGroup(); }}>
        <div class="form-group">
          <label>Group</label>
          <div class="selected-group">
            <strong>{selectedGroup.name}</strong>
            <code>{selectedGroup.dn}</code>
          </div>
        </div>
        <div class="form-group">
          <label for="group-role">Role</label>
          <select id="group-role" bind:value={groupRole}>
            <option value="member">Member - Can use agents and view project</option>
            <option value="admin">Admin - Can manage settings and members</option>
          </select>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" onclick={closeGroupForm}>Cancel</button>
          <button type="submit" class="btn btn-primary">Add Group</button>
        </div>
      </form>
    </div>
  </div>
{/if}

<style>
  .settings-container {
    width: 100%;
    max-width: 1000px;
    margin: 0 auto;
    padding: var(--spacing-xl);
    min-height: 100vh;
    background-color: var(--bg-primary);
  }

  .settings-header {
    display: flex;
    align-items: center;
    gap: var(--spacing-lg);
    margin-bottom: var(--spacing-xl);
    padding-bottom: var(--spacing-lg);
    border-bottom: 1px solid var(--border-color);
  }

  .back-button {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-md);
    color: var(--text-secondary);
    transition: all 0.2s ease;
  }

  .back-button:hover {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
  }

  .settings-title {
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .project-name {
    color: var(--primary-accent);
  }

  .settings-label {
    color: var(--text-secondary);
    font-weight: 400;
  }

  .tabs {
    display: flex;
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-xl);
    border-bottom: 1px solid var(--border-color);
  }

  .tab {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md) var(--spacing-lg);
    color: var(--text-secondary);
    font-weight: 500;
    border-bottom: 2px solid transparent;
    margin-bottom: -1px;
    transition: all 0.2s ease;
  }

  .tab:hover {
    color: var(--text-primary);
  }

  .tab.active {
    color: var(--primary-accent);
    border-bottom-color: var(--primary-accent);
  }

  .section {
    background-color: var(--bg-secondary);
    border-radius: var(--radius-lg);
    padding: var(--spacing-lg);
  }

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

  .cell-endpoint,
  .cell-dn {
    max-width: 300px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .cell-actions {
    display: flex;
    gap: var(--spacing-xs);
  }

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

  .badge-websocket {
    background-color: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }

  .badge-grpc {
    background-color: rgba(139, 92, 246, 0.1);
    color: #8b5cf6;
  }

  .badge-default {
    background-color: rgba(245, 158, 11, 0.15);
    color: var(--primary-accent);
    margin-left: var(--spacing-xs);
  }

  .role-select {
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    background-color: var(--bg-primary);
    font-size: 0.9rem;
  }

  /* Search */
  .search-container {
    margin-bottom: var(--spacing-lg);
  }

  .search-container label {
    display: block;
    font-size: 0.9rem;
    font-weight: 500;
    margin-bottom: var(--spacing-xs);
  }

  .search-input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .search-input-wrapper svg {
    position: absolute;
    left: var(--spacing-md);
    color: var(--text-secondary);
  }

  .search-input-wrapper input {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    padding-left: 44px;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background-color: var(--bg-primary);
    font-size: 0.95rem;
  }

  .search-input-wrapper input:focus {
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
  }

  .search-spinner {
    position: absolute;
    right: var(--spacing-md);
    width: 16px;
    height: 16px;
    border: 2px solid var(--border-color);
    border-top-color: var(--primary-accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .search-results {
    margin-top: var(--spacing-sm);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background-color: var(--bg-primary);
    max-height: 200px;
    overflow-y: auto;
  }

  .search-result-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    text-align: left;
    transition: background-color 0.15s ease;
  }

  .search-result-item:hover {
    background-color: var(--bg-secondary);
  }

  .result-info {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .result-name {
    font-weight: 500;
  }

  .result-dn {
    font-size: 0.8rem;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* Modal */
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
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--border-color);
  }

  .modal-header h3 {
    font-size: 1.1rem;
    font-weight: 600;
  }

  .modal-close {
    padding: var(--spacing-xs);
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    transition: all 0.2s ease;
  }

  .modal-close:hover {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
  }

  .modal-body {
    padding: var(--spacing-lg);
  }

  .form-group {
    margin-bottom: var(--spacing-md);
  }

  .form-group label {
    display: block;
    font-size: 0.9rem;
    font-weight: 500;
    margin-bottom: var(--spacing-xs);
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

  .selected-group {
    padding: var(--spacing-md);
    background-color: var(--bg-secondary);
    border-radius: var(--radius-md);
  }

  .selected-group strong {
    display: block;
    margin-bottom: var(--spacing-xs);
  }

  .selected-group code {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-lg);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-color);
  }
</style>

