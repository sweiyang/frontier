<script>
  import { onMount } from "svelte";
  import { authFetch, authPost } from "./utils.js";

  let {
    project = "",
    onback = () => {},
  } = $props();

  // Tab state
  let activeTab = $state("agents"); // "agents" | "rbac" | "usage"
  let rbacSubTab = $state("lan_ids"); // "lan_ids" | "ad_groups" | "roles"
  
  // Usage state
  let usageData = $state(null);
  let usageLoading = $state(false);

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
  });
  
  // Password visibility toggle
  let showCredentials = $state(false);

  // LAN IDs (Members) state
  let members = $state([]);
  let membersLoading = $state(true);
  let showMemberForm = $state(false);
  let editingMember = $state(null);
  let memberForm = $state({
    username: "",
    role: "member",
    agent_ids: [],
  });
  let agentSearchQuery = $state("");
  let filteredAgents = $derived(() => {
    if (!agentSearchQuery.trim()) return [];
    const query = agentSearchQuery.toLowerCase();
    return agents.filter(agent => 
      agent.name.toLowerCase().includes(query) && 
      !memberForm.agent_ids.includes(agent.id)
    );
  });

  // AD Groups state
  let adGroups = $state([]);
  let groupsLoading = $state(true);
  let showGroupForm = $state(false);
  let editingGroup = $state(null);
  let groupForm = $state({
    group_dn: "",
    group_name: "",
    role: "member",
    agent_ids: [],
  });
  let groupAgentSearchQuery = $state("");
  let filteredGroupAgents = $derived(() => {
    if (!groupAgentSearchQuery.trim()) return [];
    const query = groupAgentSearchQuery.toLowerCase();
    return agents.filter(agent => 
      agent.name.toLowerCase().includes(query) && 
      !groupForm.agent_ids.includes(agent.id)
    );
  });

  const connectionTypes = ["http", "langgraph"];
  const authTypes = [
    { value: "none", label: "None" },
    { value: "api_key", label: "API Key" },
    { value: "bearer", label: "Bearer Token" },
    { value: "basic", label: "Basic Auth" },
  ];

  onMount(async () => {
    await Promise.all([loadAgents(), loadMembers(), loadADGroups()]);
  });
  
  // Watch for tab changes to load usage data
  $effect(() => {
    if (activeTab === "usage") {
      loadUsage();
    }
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
      const auth = agent.auth || {};
      const authType = auth.auth_type || "none";
      const credentials = auth.credentials || "";
      
      agentForm = {
        name: agent.name,
        endpoint: agent.endpoint,
        connection_type: agent.connection_type,
        is_default: agent.is_default || false,
        extras: agent.extras ? JSON.stringify(agent.extras, null, 2) : "",
        auth_type: authType,
        auth_credentials: typeof credentials === "string" ? credentials : "",
        auth_username: typeof credentials === "object" ? credentials.username || "" : "",
        auth_password: typeof credentials === "object" ? credentials.password || "" : "",
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
    };
    showCredentials = false;
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

    // Build auth object
    let auth = null;
    if (agentForm.auth_type !== "none") {
      if (agentForm.auth_type === "basic") {
        auth = {
          auth_type: "basic",
          credentials: {
            username: agentForm.auth_username,
            password: agentForm.auth_password,
          }
        };
      } else {
        auth = {
          auth_type: agentForm.auth_type,
          credentials: agentForm.auth_credentials,
        };
      }
    }

    const payload = {
      name: agentForm.name,
      endpoint: agentForm.endpoint,
      connection_type: agentForm.connection_type,
      is_default: agentForm.is_default,
      extras,
      auth,
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
  // LAN ID (Members) Functions
  // ==========================================================================

  async function loadMembers() {
    membersLoading = true;
    try {
      const response = await authFetch(`/projects/${project}/members`);
      if (response.ok) {
        const data = await response.json();
        members = data.members || [];
      }
    } catch (error) {
      console.error("Failed to load members:", error);
    } finally {
      membersLoading = false;
    }
  }

  function openMemberForm(member = null) {
    if (member) {
      editingMember = member;
      memberForm = {
        username: member.username,
        role: member.role,
        agent_ids: member.agent_ids || [],
      };
    } else {
      editingMember = null;
      memberForm = {
        username: "",
        role: "member",
        agent_ids: [],
      };
    }
    showMemberForm = true;
  }

  function closeMemberForm() {
    showMemberForm = false;
    editingMember = null;
    memberForm = {
      username: "",
      role: "member",
      agent_ids: [],
    };
    agentSearchQuery = "";
  }

  function addAgentPermission(agentId) {
    if (!memberForm.agent_ids.includes(agentId)) {
      memberForm.agent_ids = [...memberForm.agent_ids, agentId];
    }
    agentSearchQuery = "";
  }

  function removeAgentPermission(agentId) {
    memberForm.agent_ids = memberForm.agent_ids.filter(id => id !== agentId);
  }

  function getAgentById(agentId) {
    return agents.find(a => a.id === agentId);
  }

  async function saveMember() {
    try {
      let response;
      if (editingMember) {
        response = await authFetch(`/projects/${project}/members/${editingMember.user_id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            role: memberForm.role,
            agent_ids: memberForm.agent_ids,
          }),
        });
      } else {
        response = await authPost(`/projects/${project}/members`, {
          username: memberForm.username,
          role: memberForm.role,
          agent_ids: memberForm.agent_ids,
        });
      }

      if (response.ok) {
        await loadMembers();
        closeMemberForm();
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to save member");
      }
    } catch (error) {
      console.error("Failed to save member:", error);
    }
  }

  async function updateMemberRole(member, newRole) {
    try {
      const response = await authFetch(`/projects/${project}/members/${member.user_id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole }),
      });
      if (response.ok) {
        await loadMembers();
      }
    } catch (error) {
      console.error("Failed to update member role:", error);
    }
  }

  async function removeMember(member) {
    if (!confirm(`Remove "${member.username}" from project?`)) return;

    try {
      const response = await authFetch(`/projects/${project}/members/${member.user_id}`, {
        method: "DELETE",
      });
      if (response.ok) {
        await loadMembers();
      }
    } catch (error) {
      console.error("Failed to remove member:", error);
    }
  }

  // ==========================================================================
  // AD Groups Functions
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

  function openGroupForm(group = null) {
    if (group) {
      editingGroup = group;
      groupForm = {
        group_dn: group.group_dn,
        group_name: group.group_name,
        role: group.role,
        agent_ids: group.agent_ids || [],
      };
    } else {
      editingGroup = null;
      groupForm = {
        group_dn: "",
        group_name: "",
        role: "member",
        agent_ids: [],
      };
    }
    showGroupForm = true;
  }

  function closeGroupForm() {
    showGroupForm = false;
    editingGroup = null;
    groupForm = {
      group_dn: "",
      group_name: "",
      role: "member",
      agent_ids: [],
    };
    groupAgentSearchQuery = "";
  }

  function addGroupAgentPermission(agentId) {
    if (!groupForm.agent_ids.includes(agentId)) {
      groupForm.agent_ids = [...groupForm.agent_ids, agentId];
    }
    groupAgentSearchQuery = "";
  }

  function removeGroupAgentPermission(agentId) {
    groupForm.agent_ids = groupForm.agent_ids.filter(id => id !== agentId);
  }

  async function saveGroup() {
    try {
      let response;
      if (editingGroup) {
        response = await authFetch(`/projects/${project}/groups/${editingGroup.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            role: groupForm.role,
            agent_ids: groupForm.agent_ids,
          }),
        });
      } else {
        response = await authPost(`/projects/${project}/groups`, {
          group_dn: groupForm.group_dn,
          group_name: groupForm.group_name,
          role: groupForm.role,
          agent_ids: groupForm.agent_ids,
        });
      }

      if (response.ok) {
        await loadADGroups();
        closeGroupForm();
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to save group");
      }
    } catch (error) {
      console.error("Failed to save AD group:", error);
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

  // ==========================================================================
  // Usage Functions
  // ==========================================================================

  async function loadUsage() {
    usageLoading = true;
    try {
      const response = await authFetch(`/projects/${project}/usage`);
      if (response.ok) {
        const data = await response.json();
        usageData = data;
      } else {
        console.error("Failed to load usage data");
        usageData = null;
      }
    } catch (error) {
      console.error("Failed to load usage:", error);
      usageData = null;
    } finally {
      usageLoading = false;
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
    <button
      class="tab"
      class:active={activeTab === "usage"}
      onclick={() => (activeTab = "usage")}
    >
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="12" y1="20" x2="12" y2="10"/>
        <line x1="18" y1="20" x2="18" y2="4"/>
        <line x1="6" y1="20" x2="6" y2="16"/>
      </svg>
      Usage
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
    {:else if activeTab === "usage"}
      <!-- Usage Section -->
      <div class="section">
        <div class="section-header">
          <h2>Project Usage</h2>
          <button class="btn btn-secondary" onclick={loadUsage} disabled={usageLoading}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="23 4 23 10 17 10"/>
              <polyline points="1 20 1 14 7 14"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            Refresh
          </button>
        </div>

        {#if usageLoading}
          <div class="loading">Loading usage data...</div>
        {:else if !usageData}
          <div class="empty-state">
            <p>No usage data available.</p>
            <p class="hint">Usage statistics will appear here once messages are sent in this project.</p>
          </div>
        {:else}
          <div class="usage-stats">
            <div class="usage-summary">
              <div class="stat-card">
                <div class="stat-label">Total Messages</div>
                <div class="stat-value">{usageData.total_messages || 0}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">Total Tokens</div>
                <div class="stat-value">{usageData.total_tokens?.toLocaleString() || 0}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">Agents Used</div>
                <div class="stat-value">{Object.keys(usageData.by_agent || {}).length}</div>
              </div>
            </div>

            {#if Object.keys(usageData.by_agent || {}).length > 0}
              <div class="usage-by-agent">
                <h3>Usage by Agent</h3>
                <div class="table-container">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Agent Name</th>
                        <th>Messages</th>
                        <th>Tokens</th>
                        <th>Avg Tokens/Message</th>
                        <th>Total Users</th>
                        <th>
                          Active Users
                          <span class="tooltip-trigger" title="Users who used this agent in the last 7 days">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <circle cx="12" cy="12" r="10"/>
                              <line x1="12" y1="16" x2="12" y2="12"/>
                              <line x1="12" y1="8" x2="12.01" y2="8"/>
                            </svg>
                          </span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each Object.entries(usageData.by_agent || {}) as [agentName, stats]}
                        <tr>
                          <td class="cell-name">
                            <strong>{agentName}</strong>
                          </td>
                          <td>{stats.message_count || 0}</td>
                          <td>{stats.total_tokens?.toLocaleString() || 0}</td>
                          <td>
                            {stats.message_count > 0 
                              ? Math.round(stats.total_tokens / stats.message_count)
                              : 0}
                          </td>
                          <td>{stats.total_users || 0}</td>
                          <td>{stats.active_users || 0}</td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
              </div>
            {:else}
              <div class="empty-state">
                <p>No agent usage data yet.</p>
                <p class="hint">Usage will be tracked when agents are used in conversations.</p>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {:else}
      <!-- RBAC Section with Sub-tabs -->
      <div class="section">
        <div class="sub-tabs">
          <button
            class="sub-tab"
            class:active={rbacSubTab === "lan_ids"}
            onclick={() => (rbacSubTab = "lan_ids")}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="4" width="18" height="16" rx="2"/>
              <line x1="7" y1="8" x2="17" y2="8"/>
              <line x1="7" y1="12" x2="12" y2="12"/>
            </svg>
            LAN IDs
          </button>
          <button
            class="sub-tab"
            class:active={rbacSubTab === "ad_groups"}
            onclick={() => (rbacSubTab = "ad_groups")}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            AD Groups
          </button>
          <button
            class="sub-tab"
            class:active={rbacSubTab === "roles"}
            onclick={() => (rbacSubTab = "roles")}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            Roles
          </button>
        </div>

        <div class="sub-tab-content">
          {#if rbacSubTab === "lan_ids"}
            <!-- LAN IDs (Members) Panel -->
            <div class="panel-header">
              <div>
                <h3>LAN IDs</h3>
                <p class="panel-description">Add individual users by their LAN ID (username) to grant access to this project.</p>
              </div>
              <button class="btn btn-primary" onclick={() => openMemberForm()}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                Add LAN ID
              </button>
            </div>

            {#if membersLoading}
              <div class="loading">Loading members...</div>
            {:else if members.length === 0}
              <div class="empty-state">
                <p>No members added yet.</p>
                <p class="hint">Add LAN IDs (usernames) to grant individual access to this project.</p>
              </div>
            {:else}
              <div class="table-container">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>LAN ID</th>
                      <th>Agents</th>
                      <th>Role</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each members as member}
                      <tr>
                        <td class="cell-name">
                          <code>{member.username}</code>
                          {#if member.is_owner}
                            <span class="badge badge-owner">Owner</span>
                          {/if}
                        </td>
                        <td>
                          {#if member.agent_ids && member.agent_ids.length > 0}
                            <span class="agent-count">{member.agent_ids.length} agent{member.agent_ids.length !== 1 ? 's' : ''}</span>
                          {:else}
                            <span class="text-muted">None</span>
                          {/if}
                        </td>
                        <td>
                          {#if member.is_owner}
                            <span class="role-text">Owner</span>
                          {:else}
                            <select
                              class="role-select"
                              value={member.role}
                              onchange={(e) => updateMemberRole(member, e.target.value)}
                            >
                              <option value="member">Member</option>
                              <option value="admin">Admin</option>
                            </select>
                          {/if}
                        </td>
                        <td class="cell-actions">
                          {#if !member.is_owner}
                            <button class="btn-icon" onclick={() => openMemberForm(member)} title="Edit">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                              </svg>
                            </button>
                            <button class="btn-icon btn-danger" onclick={() => removeMember(member)} title="Remove">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polyline points="3 6 5 6 21 6"/>
                                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                              </svg>
                            </button>
                          {:else}
                            <span class="text-muted">—</span>
                          {/if}
                        </td>
                      </tr>
                    {/each}
                  </tbody>
                </table>
              </div>
            {/if}
          {:else if rbacSubTab === "ad_groups"}
            <!-- AD Groups Panel -->
            <div class="panel-header">
              <div>
                <h3>AD Groups</h3>
                <p class="panel-description">Add Active Directory groups to grant access to all members of a group.</p>
              </div>
              <button class="btn btn-primary" onclick={() => openGroupForm()}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                Add AD Group
              </button>
            </div>

            {#if groupsLoading}
              <div class="loading">Loading groups...</div>
            {:else if adGroups.length === 0}
              <div class="empty-state">
                <p>No AD groups added yet.</p>
                <p class="hint">Add Active Directory groups to grant group-based access to this project.</p>
              </div>
            {:else}
              <div class="table-container">
                <table class="data-table">
                  <thead>
                    <tr>
                      <th>Group Name</th>
                      <th>DN</th>
                      <th>Agents</th>
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
                          {#if group.agent_ids && group.agent_ids.length > 0}
                            <span class="agent-count">{group.agent_ids.length} agent{group.agent_ids.length !== 1 ? 's' : ''}</span>
                          {:else}
                            <span class="text-muted">None</span>
                          {/if}
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
                          <button class="btn-icon" onclick={() => openGroupForm(group)} title="Edit">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                              <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                              <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                            </svg>
                          </button>
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
          {:else if rbacSubTab === "roles"}
            <!-- Roles Panel -->
            <div class="panel-header">
              <div>
                <h3>Role Definitions</h3>
                <p class="panel-description">Available roles and their permissions in this project.</p>
              </div>
            </div>

            <div class="roles-grid">
              <div class="role-card">
                <div class="role-header">
                  <span class="role-badge role-member">Member</span>
                </div>
                <div class="role-body">
                  <p class="role-description">Standard project access with basic permissions.</p>
                  <ul class="permission-list">
                    <li>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Use AI agents
                    </li>
                    <li>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      View project resources
                    </li>
                    <li>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Create conversations
                    </li>
                  </ul>
                </div>
              </div>

              <div class="role-card">
                <div class="role-header">
                  <span class="role-badge role-admin">Admin</span>
                </div>
                <div class="role-body">
                  <p class="role-description">Full project management with elevated permissions.</p>
                  <ul class="permission-list">
                    <li>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      All Member permissions
                    </li>
                    <li>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Manage project settings
                    </li>
                    <li>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Add/remove members
                    </li>
                    <li>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"/>
                      </svg>
                      Configure AI agents
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          {/if}
        </div>
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
            <label for="agent-credentials">{agentForm.auth_type === "api_key" ? "API Key" : "Token"}</label>
            <div class="password-input-wrapper">
              <input
                id="agent-credentials"
                type={showCredentials ? "text" : "password"}
                placeholder={agentForm.auth_type === "api_key" ? "Enter API key" : "Enter bearer token"}
                bind:value={agentForm.auth_credentials}
              />
              <button type="button" class="toggle-visibility" onclick={() => showCredentials = !showCredentials} title={showCredentials ? "Hide" : "Show"}>
                {#if showCredentials}
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                {:else}
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
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
              <button type="button" class="toggle-visibility" onclick={() => showCredentials = !showCredentials} title={showCredentials ? "Hide" : "Show"}>
                {#if showCredentials}
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/>
                    <line x1="1" y1="1" x2="23" y2="23"/>
                  </svg>
                {:else}
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                    <circle cx="12" cy="12" r="3"/>
                  </svg>
                {/if}
              </button>
            </div>
          </div>
        {/if}
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

<!-- LAN ID (Member) Form Modal -->
{#if showMemberForm}
  <div class="modal-overlay" onclick={closeMemberForm}>
    <div class="modal" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h3>{editingMember ? "Edit Member" : "Add LAN ID"}</h3>
        <button class="modal-close" onclick={closeMemberForm}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <form class="modal-body" onsubmit={(e) => { e.preventDefault(); saveMember(); }}>
        <div class="form-group">
          <label for="member-username">LAN ID (Username)</label>
          <input
            id="member-username"
            type="text"
            placeholder="e.g., jsmith"
            bind:value={memberForm.username}
            required
            disabled={!!editingMember}
          />
          {#if editingMember}
            <p class="form-hint">LAN ID cannot be changed. Remove and re-add to change.</p>
          {/if}
        </div>
        <div class="form-group">
          <label for="member-role">Role</label>
          <select id="member-role" bind:value={memberForm.role}>
            <option value="member">Member - Can use agents and view project</option>
            <option value="admin">Admin - Can manage settings and members</option>
          </select>
        </div>
        <div class="form-group">
          <label>Agent Permissions</label>
          <p class="form-hint" style="margin-bottom: var(--spacing-sm);">Add agents this user can access.</p>
          
          <!-- Agent Tags -->
          <div class="agent-tags-container">
            {#if memberForm.agent_ids.length === 0}
              <span class="no-agents-text">No agents assigned</span>
            {:else}
              {#each memberForm.agent_ids as agentId}
                {@const agent = getAgentById(agentId)}
                {#if agent}
                  <span class="agent-tag">
                    <span class="agent-tag-name">{agent.name}</span>
                    <button type="button" class="agent-tag-remove" onclick={() => removeAgentPermission(agentId)} title="Remove">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </span>
                {/if}
              {/each}
            {/if}
          </div>

          <!-- Search and Add -->
          {#if agents.length > 0}
            <div class="agent-search-container">
              <div class="agent-search-input-wrapper">
                <input
                  type="text"
                  placeholder="Search agents to add..."
                  bind:value={agentSearchQuery}
                  class="agent-search-input"
                />
              </div>
              
              {#if filteredAgents().length > 0}
                <div class="agent-search-results">
                  {#each filteredAgents() as agent}
                    <button type="button" class="agent-search-result" onclick={() => addAgentPermission(agent.id)}>
                      <span class="agent-result-name">{agent.name}</span>
                      <span class="agent-result-badges">
                        <span class="badge badge-{agent.connection_type}">{agent.connection_type}</span>
                        {#if agent.is_default}
                          <span class="badge badge-default">Default</span>
                        {/if}
                      </span>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="add-icon">
                        <line x1="12" y1="5" x2="12" y2="19"/>
                        <line x1="5" y1="12" x2="19" y2="12"/>
                      </svg>
                    </button>
                  {/each}
                </div>
              {:else if agentSearchQuery.trim() && filteredAgents().length === 0}
                <div class="agent-search-empty">No matching agents found</div>
              {/if}
            </div>
          {:else}
            <div class="empty-permissions">
              <p>No agents configured for this project.</p>
            </div>
          {/if}
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" onclick={closeMemberForm}>Cancel</button>
          <button type="submit" class="btn btn-primary">
            {editingMember ? "Update" : "Add"} Member
          </button>
        </div>
      </form>
    </div>
  </div>
{/if}

<!-- AD Group Form Modal -->
{#if showGroupForm}
  <div class="modal-overlay" onclick={closeGroupForm}>
    <div class="modal" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h3>{editingGroup ? "Edit AD Group" : "Add AD Group"}</h3>
        <button class="modal-close" onclick={closeGroupForm}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18"/>
            <line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <form class="modal-body" onsubmit={(e) => { e.preventDefault(); saveGroup(); }}>
        <div class="form-group">
          <label for="group-name">Group Name</label>
          <input
            id="group-name"
            type="text"
            placeholder="e.g., Engineering Team"
            bind:value={groupForm.group_name}
            required
            disabled={!!editingGroup}
          />
        </div>
        <div class="form-group">
          <label for="group-dn">Distinguished Name (DN)</label>
          <input
            id="group-dn"
            type="text"
            placeholder="e.g., CN=Engineering,OU=Groups,DC=example,DC=com"
            bind:value={groupForm.group_dn}
            required
            disabled={!!editingGroup}
          />
          {#if editingGroup}
            <p class="form-hint">Group details cannot be changed. Remove and re-add to modify.</p>
          {/if}
        </div>
        <div class="form-group">
          <label for="group-role">Role</label>
          <select id="group-role" bind:value={groupForm.role}>
            <option value="member">Member - Can use agents and view project</option>
            <option value="admin">Admin - Can manage settings and members</option>
          </select>
        </div>
        <div class="form-group">
          <label>Agent Permissions</label>
          <p class="form-hint" style="margin-bottom: var(--spacing-sm);">Add agents this group can access.</p>
          
          <!-- Agent Tags -->
          <div class="agent-tags-container">
            {#if groupForm.agent_ids.length === 0}
              <span class="no-agents-text">No agents assigned</span>
            {:else}
              {#each groupForm.agent_ids as agentId}
                {@const agent = getAgentById(agentId)}
                {#if agent}
                  <span class="agent-tag">
                    <span class="agent-tag-name">{agent.name}</span>
                    <button type="button" class="agent-tag-remove" onclick={() => removeGroupAgentPermission(agentId)} title="Remove">
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"/>
                        <line x1="6" y1="6" x2="18" y2="18"/>
                      </svg>
                    </button>
                  </span>
                {/if}
              {/each}
            {/if}
          </div>

          <!-- Search and Add -->
          {#if agents.length > 0}
            <div class="agent-search-container">
              <div class="agent-search-input-wrapper">
                <input
                  type="text"
                  placeholder="Search agents to add..."
                  bind:value={groupAgentSearchQuery}
                  class="agent-search-input"
                />
              </div>
              
              {#if filteredGroupAgents().length > 0}
                <div class="agent-search-results">
                  {#each filteredGroupAgents() as agent}
                    <button type="button" class="agent-search-result" onclick={() => addGroupAgentPermission(agent.id)}>
                      <span class="agent-result-name">{agent.name}</span>
                      <span class="agent-result-badges">
                        <span class="badge badge-{agent.connection_type}">{agent.connection_type}</span>
                        {#if agent.is_default}
                          <span class="badge badge-default">Default</span>
                        {/if}
                      </span>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="add-icon">
                        <line x1="12" y1="5" x2="12" y2="19"/>
                        <line x1="5" y1="12" x2="19" y2="12"/>
                      </svg>
                    </button>
                  {/each}
                </div>
              {:else if groupAgentSearchQuery.trim() && filteredGroupAgents().length === 0}
                <div class="agent-search-empty">No matching agents found</div>
              {/if}
            </div>
          {:else}
            <div class="empty-permissions">
              <p>No agents configured for this project.</p>
            </div>
          {/if}
        </div>
        <div class="modal-actions">
          <button type="button" class="btn btn-secondary" onclick={closeGroupForm}>Cancel</button>
          <button type="submit" class="btn btn-primary">
            {editingGroup ? "Update" : "Add"} Group
          </button>
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

  .sub-tabs {
    display: flex;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-lg);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-color);
  }

  .sub-tab {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    color: var(--text-secondary);
    font-weight: 500;
    font-size: 0.9rem;
    border-radius: var(--radius-md);
    transition: all 0.2s ease;
  }

  .sub-tab:hover {
    background-color: var(--bg-primary);
    color: var(--text-primary);
  }

  .sub-tab.active {
    background-color: var(--primary-accent);
    color: white;
  }

  .sub-tab-content {
    min-height: 300px;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: var(--spacing-lg);
  }

  .panel-header h3 {
    font-size: 1rem;
    font-weight: 600;
    margin-bottom: var(--spacing-xs);
  }

  .panel-description {
    font-size: 0.85rem;
    color: var(--text-secondary);
    margin: 0;
  }

  .roles-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: var(--spacing-lg);
  }

  .role-card {
    background-color: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  .role-header {
    padding: var(--spacing-md) var(--spacing-lg);
    border-bottom: 1px solid var(--border-color);
    background-color: var(--bg-secondary);
  }

  .role-badge {
    display: inline-block;
    padding: var(--spacing-xs) var(--spacing-md);
    border-radius: var(--radius-full);
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .role-member {
    background-color: rgba(59, 130, 246, 0.15);
    color: #3b82f6;
  }

  .role-admin {
    background-color: rgba(245, 158, 11, 0.15);
    color: var(--primary-accent);
  }

  .role-body {
    padding: var(--spacing-lg);
  }

  .role-description {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: var(--spacing-md);
  }

  .permission-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .permission-list li {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-xs) 0;
    font-size: 0.9rem;
    color: var(--text-primary);
  }

  .permission-list svg {
    color: #10b981;
    flex-shrink: 0;
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

  .badge-langgraph {
    background-color: rgba(16, 185, 129, 0.1);
    color: #10b981;
  }

  .badge-default {
    background-color: rgba(245, 158, 11, 0.15);
    color: var(--primary-accent);
    margin-left: var(--spacing-xs);
  }

  .badge-owner {
    background-color: rgba(139, 92, 246, 0.15);
    color: #8b5cf6;
    margin-left: var(--spacing-xs);
  }

  .role-text {
    font-weight: 500;
    color: var(--text-secondary);
  }

  .text-muted {
    color: var(--text-secondary);
  }

  .agent-tags-container {
    display: flex;
    flex-wrap: wrap;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm);
    min-height: 44px;
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    margin-bottom: var(--spacing-sm);
  }

  .no-agents-text {
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-style: italic;
  }

  .agent-tag {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: 4px 8px 4px 12px;
    background-color: var(--primary-accent);
    color: white;
    border-radius: var(--radius-full);
    font-size: 0.85rem;
    font-weight: 500;
  }

  .agent-tag-name {
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .agent-tag-remove {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background-color: rgba(255, 255, 255, 0.2);
    color: white;
    transition: background-color 0.15s ease;
  }

  .agent-tag-remove:hover {
    background-color: rgba(255, 255, 255, 0.4);
  }

  .agent-search-container {
    position: relative;
  }

  .agent-search-input-wrapper {
    position: relative;
  }

  .agent-search-input {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background-color: var(--bg-primary);
    font-size: 0.95rem;
  }

  .agent-search-input:focus {
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 3px rgba(245, 158, 11, 0.1);
  }

  .agent-search-results {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    margin-top: 4px;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    background-color: var(--bg-primary);
    box-shadow: var(--shadow-lg);
    max-height: 180px;
    overflow-y: auto;
    z-index: 10;
  }

  .agent-search-result {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    text-align: left;
    transition: background-color 0.15s ease;
    border-bottom: 1px solid var(--border-color);
  }

  .agent-search-result:last-child {
    border-bottom: none;
  }

  .agent-search-result:hover {
    background-color: var(--bg-secondary);
  }

  .agent-result-name {
    flex: 1;
    font-weight: 500;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .agent-result-badges {
    display: flex;
    gap: var(--spacing-xs);
  }

  .agent-search-result .add-icon {
    color: var(--primary-accent);
    flex-shrink: 0;
  }

  .agent-search-empty {
    padding: var(--spacing-md);
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.9rem;
    background-color: var(--bg-secondary);
    border-radius: var(--radius-md);
    margin-top: 4px;
  }

  .empty-permissions {
    padding: var(--spacing-md);
    background-color: var(--bg-secondary);
    border-radius: var(--radius-md);
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .empty-permissions p {
    margin: 0;
  }

  .agent-count {
    display: inline-block;
    padding: 2px 8px;
    background-color: rgba(59, 130, 246, 0.1);
    color: #3b82f6;
    border-radius: var(--radius-full);
    font-size: 0.8rem;
    font-weight: 500;
  }

  .role-select {
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    background-color: var(--bg-primary);
    font-size: 0.9rem;
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

  .auth-field {
    padding-left: var(--spacing-md);
    border-left: 2px solid var(--primary-accent);
    margin-left: var(--spacing-xs);
    animation: slideIn 0.2s ease-out;
  }

  @keyframes slideIn {
    from {
      opacity: 0;
      transform: translateX(-10px);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
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


  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-lg);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-color);
  }

  /* Usage Section Styles */
  .usage-stats {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xl);
  }

  .usage-summary {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: var(--spacing-md);
  }

  .stat-card {
    background-color: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: var(--spacing-lg);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .stat-label {
    font-size: 0.875rem;
    color: var(--text-secondary);
    font-weight: 500;
  }

  .stat-value {
    font-size: 2rem;
    font-weight: 600;
    color: var(--primary-accent);
  }

  .usage-by-agent {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .usage-by-agent h3 {
    font-size: 1.1rem;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0;
  }

  .tooltip-trigger {
    display: inline-flex;
    align-items: center;
    margin-left: var(--spacing-xs);
    color: var(--text-secondary);
    cursor: help;
    vertical-align: middle;
  }

  .tooltip-trigger:hover {
    color: var(--text-primary);
  }

  .tooltip-trigger svg {
    width: 14px;
    height: 14px;
  }
</style>

