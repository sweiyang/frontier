<script>
  import { onMount } from "svelte";
  import { authFetch, authPost } from "./utils.js";
  import { showToast } from "./toast.js";
  import ChangeRequests from "./ChangeRequests.svelte";
  import AgentManager from "./AgentManager.svelte";
  let { project = "", onback = () => {}, initialTab = "general", hideHeader = false, hideTabs = false, isPlatformOwner = false, onsettingssaved = () => {} } = $props();

  // Tab state
  let activeTab = $state(initialTab || "agents"); // "agents" | "approval" | "usage" | "general" | "builder"
  let rbacSubTab = $state("lan_ids"); // "lan_ids" | "ad_groups" | "roles"
  let generalSubTab = $state("general"); // "general" | "permissions" | "approval"

  // Sync activeTab when initialTab prop changes (e.g. from Workbench sidebar nav)
  $effect(() => {
    if (initialTab) {
      activeTab = initialTab;
    }
  });

  // Usage state
  let usageData = $state(null);
  let usageLoading = $state(false);
  let selectedUsageMonth = $state('all');

  // Site analytics state
  let siteAnalytics = $state(null);
  let siteAnalyticsLoading = $state(false);

  // General Settings state
  let projectSettings = $state({
    project_name: "",
    disable_authentication: false,
    disable_message_storage: true,
    site_builder_enabled: true,
    description: "",
    default_view: "site",
    view_locked: false,
  });
  let settingsLoading = $state(false);

  // Agents state (kept for member/group forms)
  let agents = $state([]);

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
    return agents.filter(
      (agent) =>
        agent.name.toLowerCase().includes(query) &&
        !memberForm.agent_ids.includes(agent.id),
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
    return agents.filter(
      (agent) =>
        agent.name.toLowerCase().includes(query) &&
        !groupForm.agent_ids.includes(agent.id),
    );
  });

  // Approval state
  let approvers = $state([]);
  let approversLoading = $state(true);
  let approvalSettings = $state({ approval_type: "any", approval_required: false });
  let showApproverForm = $state(false);
  let selectedApproverUserId = $state("");
  let approverSearchQuery = $state("");
  let approverError = $state("");

  // Computed: eligible approvers (admins/owners not already approvers)
  let eligibleApprovers = $derived.by(() => {
    const approverUserIds = new Set(approvers.map(a => a.user_id));
    return members
      .filter(m => (m.role === "admin" || m.is_owner) && !approverUserIds.has(m.user_id))
      .sort((a, b) => {
        if (a.is_owner && !b.is_owner) return -1;
        if (!a.is_owner && b.is_owner) return 1;
        return a.username.localeCompare(b.username);
      });
  });

  // Filtered eligible approvers based on search
  let filteredEligibleApprovers = $derived.by(() => {
    if (!approverSearchQuery.trim()) return eligibleApprovers;
    const query = approverSearchQuery.toLowerCase();
    return eligibleApprovers.filter(m => m.username.toLowerCase().includes(query));
  });

  onMount(async () => {
    await Promise.all([
      loadProjectSettings(),
      loadMembers(),
      loadADGroups(),
      loadApprovers(),
      loadApprovalSettings(),
    ]);
  });

  // Watch for tab changes to load usage data
  $effect(() => {
    if (activeTab === "usage") {
      loadUsage();
    }
  });

  // ==========================================================================
  // General Settings Functions
  // ==========================================================================

  async function loadProjectSettings() {
    settingsLoading = true;
    try {
      const response = await authFetch(`/projects/${project}`);
      if (response.ok) {
        const data = await response.json();
        projectSettings = {
          project_name: data.project_name,
          disable_authentication: data.disable_authentication || false,
          disable_message_storage: data.disable_message_storage || false,
          site_builder_enabled: data.site_builder_enabled !== false,
          description: data.description || "",
          default_view: data.default_view || "site",
          view_locked: data.view_locked ?? false,
        };
      }
    } catch (error) {
      console.error("Failed to load project settings:", error);
    } finally {
      settingsLoading = false;
    }
  }

  async function saveProjectSettings() {
    try {
      const response = await authFetch(`/projects/${project}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(projectSettings),
      });

      if (response.ok) {
        showToast("Settings saved successfully", "success");
        await loadProjectSettings();
        onsettingssaved();
      } else {
        const error = await response.json();
        showToast(error.detail || error.error || "Failed to save settings", "error");
      }
    } catch (error) {
      console.error("Failed to save settings:", error);
      showToast("Failed to save settings", "error");
    }
  }

  // ==========================================================================
  // Approval Functions
  // ==========================================================================

  async function loadApprovalSettings() {
    try {
      const response = await authFetch(`/projects/${project}/approval-settings`);
      if (response.ok) {
        const data = await response.json();
        approvalSettings = { approval_type: data.approval_type || "any", approval_required: data.approval_required || false };
      }
    } catch (error) {
      console.error("Failed to load approval settings:", error);
    }
  }

  async function loadApprovers() {
    approversLoading = true;
    try {
      const response = await authFetch(`/projects/${project}/approvers`);
      if (response.ok) {
        const data = await response.json();
        approvers = data.approvers || [];
      }
    } catch (error) {
      console.error("Failed to load approvers:", error);
    } finally {
      approversLoading = false;
    }
  }

  async function updateApprovalType(event) {
    const newType = event.target.value;
    try {
      const response = await authFetch(`/projects/${project}/approval-settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ approval_type: newType }),
      });
      if (response.ok) {
        const data = await response.json();
        approvalSettings = { approval_type: data.approval_type || newType, approval_required: data.approval_required || false };
      }
    } catch (error) {
      console.error("Failed to update approval type:", error);
    }
  }

  async function addApprover() {
    if (!selectedApproverUserId) return;
    approverError = "";
    const member = eligibleApprovers.find(m => String(m.user_id) === String(selectedApproverUserId));
    if (!member) return;
    try {
      const response = await authFetch(`/projects/${project}/approvers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username: member.username }),
      });
      if (response.ok) {
        await loadApprovers();
        selectedApproverUserId = "";
        showApproverForm = false;
      } else {
        const data = await response.json().catch((e) => { console.error('Failed to parse approver response:', e); return {}; });
        approverError = data.detail || "Failed to add approver.";
      }
    } catch (error) {
      approverError = "Network error. Please try again.";
    }
  }

  async function removeApprover(userId) {
    const approver = approvers.find(a => String(a.user_id) === String(userId));
    const name = approver?.username || "this approver";
    if (!confirm(`Remove "${name}" as an approver from this project?`)) return;
    try {
      const response = await authFetch(`/projects/${project}/approvers/${userId}`, {
        method: "DELETE",
      });
      if (response.ok) {
        await loadApprovers();
      }
    } catch (error) {
      console.error("Failed to remove approver:", error);
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
    memberForm.agent_ids = memberForm.agent_ids.filter((id) => id !== agentId);
  }

  function getAgentById(agentId) {
    return agents.find((a) => a.id === agentId);
  }

  async function saveMember() {
    try {
      let response;
      if (editingMember) {
        response = await authFetch(
          `/projects/${project}/members/${editingMember.user_id}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              role: memberForm.role,
              agent_ids: memberForm.agent_ids,
            }),
          },
        );
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
        showToast(error.detail || "Failed to save member", "error");
      }
    } catch (error) {
      console.error("Failed to save member:", error);
    }
  }

  async function updateMemberRole(member, newRole) {
    try {
      const response = await authFetch(
        `/projects/${project}/members/${member.user_id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role: newRole }),
        },
      );
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
      const response = await authFetch(
        `/projects/${project}/members/${member.user_id}`,
        {
          method: "DELETE",
        },
      );
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
    groupForm.agent_ids = groupForm.agent_ids.filter((id) => id !== agentId);
  }

  async function saveGroup() {
    try {
      let response;
      if (editingGroup) {
        response = await authFetch(
          `/projects/${project}/groups/${editingGroup.id}`,
          {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              role: groupForm.role,
              agent_ids: groupForm.agent_ids,
            }),
          },
        );
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
        showToast(error.detail || "Failed to save group", "error");
      }
    } catch (error) {
      console.error("Failed to save AD group:", error);
    }
  }

  async function updateGroupRole(group, newRole) {
    try {
      const response = await authFetch(
        `/projects/${project}/groups/${group.id}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ role: newRole }),
        },
      );
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
    siteAnalyticsLoading = true;
    try {
      const [usageRes, analyticsRes] = await Promise.all([
        authFetch(`/projects/${project}/usage`),
        authFetch(`/projects/${project}/dashboard/analytics?period=7d`).catch(() => null),
      ]);
      if (usageRes.ok) {
        usageData = await usageRes.json();
      } else {
        console.error("Failed to load usage data");
        usageData = null;
      }
      if (analyticsRes?.ok) {
        siteAnalytics = await analyticsRes.json();
      } else {
        siteAnalytics = null;
      }
    } catch (error) {
      console.error("Failed to load usage:", error);
      usageData = null;
      siteAnalytics = null;
    } finally {
      usageLoading = false;
      siteAnalyticsLoading = false;
    }
  }

  async function removeADGroup(group) {
    if (!confirm(`Remove group "${group.group_name}" from project?`)) return;

    try {
      const response = await authFetch(
        `/projects/${project}/groups/${group.id}`,
        {
          method: "DELETE",
        },
      );
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
    <button class="back-button" onclick={(e) => onback(e)}>
      <svg
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <path d="M19 12H5" />
        <polyline points="12 19 5 12 12 5" />
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
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <polyline points="21 15 16 10 5 21" />
      </svg>
      Agents
    </button>
    <button
      class="tab"
      class:active={activeTab === "approval"}
      onclick={() => (activeTab = "approval")}
    >
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
        <path d="M9 11l3 3L22 4" />
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
      </svg>
      Approval
    </button>
    <button
      class="tab"
      class:active={activeTab === "builder"}
      onclick={() => (activeTab = "builder")}
    >
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
        <rect x="3" y="3" width="7" height="7" rx="1" />
        <rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" />
        <rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
      Site Builder
    </button>
    <button
      class="tab"
      class:active={activeTab === "usage"}
      onclick={() => (activeTab = "usage")}
    >
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
        <line x1="12" y1="20" x2="12" y2="10" />
        <line x1="18" y1="20" x2="18" y2="4" />
        <line x1="6" y1="20" x2="6" y2="16" />
      </svg>
      Usage
    </button>
    <button
      class="tab"
      class:active={activeTab === "general"}
      onclick={() => (activeTab = "general")}
    >
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
        <path
          d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.74v-.52a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"
        />
        <circle cx="12" cy="12" r="3" />
      </svg>
      General
    </button>
  </div>

  <div class="tab-content">
    {#if activeTab === "general"}
      <div class="section">
        <div class="sub-tabs">
          <button
            class="sub-tab"
            class:active={generalSubTab === "general"}
            onclick={() => (generalSubTab = "general")}
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
                d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.74v-.52a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"
              />
              <circle cx="12" cy="12" r="3" />
            </svg>
            General
          </button>
          <button
            class="sub-tab"
            class:active={generalSubTab === "permissions"}
            onclick={() => (generalSubTab = "permissions")}
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
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
            Permissions
          </button>
          <button
            class="sub-tab"
            class:active={generalSubTab === "approval"}
            onclick={() => (generalSubTab = "approval")}
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
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
            Approval
          </button>
        </div>

        <div class="sub-tab-content">
          {#if generalSubTab === "general"}
            <div class="panel-header" style="margin-bottom: var(--spacing-lg);">
              <div>
                <h3>General Settings</h3>
                <p class="panel-description">Manage standard project configuration.</p>
              </div>
            </div>

            <div class="form-group" style="padding: 0 var(--spacing-md); margin-bottom: var(--spacing-md);">
              <label for="project_description">Project Description</label>
              <input
                type="text"
                id="project_description"
                bind:value={projectSettings.description}
                placeholder="Short description shown in the top bar..."
                maxlength="120"
              />
              <p class="help-text">Displayed below your name in the top bar. Keep it brief.</p>
            </div>

            <div class="form-group" style="padding: 0 var(--spacing-md);">
              <label class="checkbox-label" for="disable_msg_toggle">
                <input
                  type="checkbox"
                  id="disable_msg_toggle"
                  bind:checked={projectSettings.disable_message_storage}
                />
                Disable Message Content Storage
              </label>
              <p class="help-text">
                Enable this to prevent storing message content in the database. Only
                thread ID and conversation ID will be stored.
              </p>
            </div>

            <div class="form-group" style="padding: 0 var(--spacing-md); margin-top: var(--spacing-md);">
              <label class="checkbox-label" for="site_builder_toggle">
                <input
                  type="checkbox"
                  id="site_builder_toggle"
                  bind:checked={projectSettings.site_builder_enabled}
                />
                Enable Site Builder
              </label>
              <p class="help-text">
                When enabled, project admins can build a custom site dashboard for this project.
              </p>
            </div>

            {#if projectSettings.site_builder_enabled}
              <div class="form-group" style="padding: 0 var(--spacing-md); margin-top: var(--spacing-md);">
                <label for="default_view">Default Landing View</label>
                <select id="default_view" bind:value={projectSettings.default_view}>
                  <option value="site">Site</option>
                  <option value="chat">Chat</option>
                </select>
                <p class="help-text">Choose what users see first when they open this project.</p>
              </div>

              <div class="form-group" style="padding: 0 var(--spacing-md); margin-top: var(--spacing-md);">
                <label class="checkbox-label" for="view_locked_toggle">
                  <input
                    type="checkbox"
                    id="view_locked_toggle"
                    bind:checked={projectSettings.view_locked}
                  />
                  Lock View
                </label>
                <p class="help-text">When locked, users cannot switch between Site and Chat views.</p>
              </div>
            {/if}

            <div class="actions" style="padding: var(--spacing-lg) var(--spacing-md);">
              <button class="btn btn-primary" onclick={saveProjectSettings}>
                Save Settings
              </button>
            </div>

          {:else if generalSubTab === "permissions"}
            <div class="panel-header" style="margin-bottom: var(--spacing-lg);">
              <div>
                <h3>Project/Agent Permissions</h3>
                <p class="panel-description">Configure authentication and access definitions.</p>
              </div>
            </div>

            <div class="form-group" style="padding: 0 var(--spacing-md);">
              <label class="checkbox-label" for="disable_auth_toggle">
                <input
                  type="checkbox"
                  id="disable_auth_toggle"
                  bind:checked={projectSettings.disable_authentication}
                />
                Disable Authentication (Allow Anonymous Access to Agents)
              </label>
              <p class="help-text">
                Enable this to allow users to chat with agents in this project
                without logging in.
                <strong>Warning: This makes your agents publicly accessible.</strong
                >
              </p>
            </div>

            <div class="actions" style="padding: var(--spacing-lg) var(--spacing-md);">
              <button class="btn btn-primary" onclick={saveProjectSettings}>
                Save Settings
              </button>
            </div>

            <!-- RBAC Section with Sub-tabs -->
            <div style="border-top: 1px solid var(--border-color); padding-top: var(--spacing-lg); margin-top: var(--spacing-lg);">
              <div class="sub-tabs">
                <button
                  class="sub-tab"
                  class:active={rbacSubTab === "lan_ids"}
                  onclick={() => (rbacSubTab = "lan_ids")}
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
                    <rect x="3" y="4" width="18" height="16" rx="2" />
                    <line x1="7" y1="8" x2="17" y2="8" />
                    <line x1="7" y1="12" x2="12" y2="12" />
                  </svg>
                  LAN IDs
                </button>
                <button
                  class="sub-tab"
                  class:active={rbacSubTab === "ad_groups"}
                  onclick={() => (rbacSubTab = "ad_groups")}
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
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                    <circle cx="9" cy="7" r="4" />
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                    <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                  </svg>
                  AD Groups
                </button>
                <button
                  class="sub-tab"
                  class:active={rbacSubTab === "roles"}
                  onclick={() => (rbacSubTab = "roles")}
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
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
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
                      <p class="panel-description">
                        Add individual users by their LAN ID (username) to grant
                        access to this project.
                      </p>
                    </div>
                    <button class="btn btn-primary" onclick={() => openMemberForm()}>
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                      </svg>
                      Add LAN ID
                    </button>
                  </div>

                  {#if membersLoading}
                    <div class="loading">Loading members...</div>
                  {:else if members.length === 0}
                    <div class="empty-state">
                      <p>No members added yet.</p>
                      <p class="hint">
                        Add LAN IDs (usernames) to grant individual access to this
                        project.
                      </p>
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
                                  <span class="agent-count"
                                    >{member.agent_ids.length} agent{member.agent_ids
                                      .length !== 1
                                      ? "s"
                                      : ""}</span
                                  >
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
                                    onchange={(e) =>
                                      updateMemberRole(member, e.currentTarget.value)}
                                  >
                                    <option value="member">Member</option>
                                    <option value="admin">Admin</option>
                                  </select>
                                {/if}
                              </td>
                              <td class="cell-actions">
                                {#if !member.is_owner}
                                  <button
                                    class="btn-icon"
                                    onclick={() => openMemberForm(member)}
                                    title="Edit"
                                  >
                                    <svg
                                      width="16"
                                      height="16"
                                      viewBox="0 0 24 24"
                                      fill="none"
                                      stroke="currentColor"
                                      stroke-width="2"
                                    >
                                      <path
                                        d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                                      />
                                      <path
                                        d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
                                      />
                                    </svg>
                                  </button>
                                  <button
                                    class="btn-icon btn-danger"
                                    onclick={() => removeMember(member)}
                                    title="Remove"
                                  >
                                    <svg
                                      width="16"
                                      height="16"
                                      viewBox="0 0 24 24"
                                      fill="none"
                                      stroke="currentColor"
                                      stroke-width="2"
                                    >
                                      <polyline points="3 6 5 6 21 6" />
                                      <path
                                        d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                                      />
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
                      <p class="panel-description">
                        Add Active Directory groups to grant access to all members of
                        a group.
                      </p>
                    </div>
                    <button class="btn btn-primary" onclick={() => openGroupForm()}>
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                      </svg>
                        Add AD Group
                    </button>
                  </div>

                  {#if groupsLoading}
                    <div class="loading">Loading groups...</div>
                  {:else if adGroups.length === 0}
                    <div class="empty-state">
                      <p>No AD groups added yet.</p>
                      <p class="hint">
                        Add Active Directory groups to grant group-based access to
                        this project.
                      </p>
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
                                  <span class="agent-count"
                                    >{group.agent_ids.length} agent{group.agent_ids
                                      .length !== 1
                                      ? "s"
                                      : ""}</span
                                  >
                                {:else}
                                  <span class="text-muted">None</span>
                                {/if}
                              </td>
                              <td>
                                <select
                                  class="role-select"
                                  value={group.role}
                                  onchange={(e) =>
                                    updateGroupRole(group, e.currentTarget.value)}
                                >
                                  <option value="member">Member</option>
                                  <option value="admin">Admin</option>
                                </select>
                              </td>
                              <td class="cell-actions">
                                <button
                                  class="btn-icon"
                                  onclick={() => openGroupForm(group)}
                                  title="Edit"
                                >
                                  <svg
                                    width="16"
                                    height="16"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    stroke-width="2"
                                  >
                                    <path
                                      d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
                                    />
                                    <path
                                      d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
                                    />
                                  </svg>
                                </button>
                                <button
                                  class="btn-icon btn-danger"
                                  onclick={() => removeADGroup(group)}
                                  title="Remove"
                                >
                                  <svg
                                    width="16"
                                    height="16"
                                    viewBox="0 0 24 24"
                                    fill="none"
                                    stroke="currentColor"
                                    stroke-width="2"
                                  >
                                    <polyline points="3 6 5 6 21 6" />
                                    <path
                                      d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"
                                    />
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
                      <p class="panel-description">
                        Available roles and their permissions in this project.
                      </p>
                    </div>
                  </div>

                  <div class="roles-grid">
                    <div class="role-card">
                      <div class="role-header">
                        <span class="role-badge role-member">Member</span>
                      </div>
                      <div class="role-body">
                        <p class="role-description">
                          Standard project access with basic permissions.
                        </p>
                        <ul class="permission-list">
                          <li>
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                            >
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                            Use AI agents
                          </li>
                          <li>
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                            >
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                            View project resources
                          </li>
                          <li>
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                            >
                              <polyline points="20 6 9 17 4 12" />
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
                        <p class="role-description">
                          Full project management with elevated permissions.
                        </p>
                        <ul class="permission-list">
                          <li>
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                            >
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                            All Member permissions
                          </li>
                          <li>
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                            >
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                            Manage project settings
                          </li>
                          <li>
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                            >
                              <polyline points="20 6 9 17 4 12" />
                            </svg>
                            Add/remove members
                          </li>
                          <li>
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                            >
                              <polyline points="20 6 9 17 4 12" />
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

          {:else if generalSubTab === "approval"}
            <div class="panel-header" style="margin-bottom: var(--spacing-lg);">
              <div>
                <h3>Approval Settings</h3>
                <p class="panel-description">Determine requirements for agent changes in production.</p>
              </div>
            </div>

            <div style="padding: 0 var(--spacing-md);">
              <div class="form-group">
                <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: var(--spacing-lg);">
                  <div>
                    <label for="approval-type-select" class="form-label">Approval Type</label>
                    <p class="help-text" style="margin-top: 2px;">
                      Determines how many approvals are required for agent changes in production.
                    </p>
                  </div>
                  <select
                    id="approval-type-select"
                    class="select-input"
                    value={approvalSettings.approval_type}
                    onchange={updateApprovalType}
                  >
                    <option value="any">Any single approver</option>
                    <option value="majority">Majority of approvers</option>
                    <option value="all">All approvers</option>
                  </select>
                </div>
              </div>

              <div style="border-top: 1px solid var(--border-color); padding-top: var(--spacing-lg); margin-top: var(--spacing-md);">
                <div class="section-header">
                  <h3 style="margin: 0; font-size: 1rem;">Approvers</h3>
                  <button class="btn btn-primary btn-sm" onclick={() => (showApproverForm = true)}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="12" y1="5" x2="12" y2="19" />
                      <line x1="5" y1="12" x2="19" y2="12" />
                    </svg>
                    Add Approver
                  </button>
                </div>

                <p class="help-text" style="margin-bottom: var(--spacing-md);">
                  Approvers can approve or reject pending change requests in production environments.
                </p>

                {#if showApproverForm}
                  <div style="display: flex; flex-direction: column; gap: var(--spacing-sm); padding: var(--spacing-md); background: var(--bg-primary); border-radius: var(--radius-md); margin-bottom: var(--spacing-md);">
                    {#if eligibleApprovers.length === 0}
                      <p style="color: var(--text-secondary); font-size: 0.9rem;">
                        No eligible users available. Only project admins and owners can be added as approvers.
                      </p>
                    {:else}
                      <input
                        type="text"
                        placeholder="Search admins..."
                        bind:value={approverSearchQuery}
                        class="input"
                        style="margin-bottom: var(--spacing-xs);"
                      />
                      <div style="max-height: 200px; overflow-y: auto; border: 1px solid var(--border-color); border-radius: var(--radius-sm);">
                        {#each filteredEligibleApprovers as member}
                          <button
                            type="button"
                            class="approver-option"
                            class:selected={selectedApproverUserId === String(member.user_id)}
                            onclick={() => selectedApproverUserId = String(member.user_id)}
                            style="display: flex; align-items: center; gap: var(--spacing-sm); width: 100%; padding: var(--spacing-sm) var(--spacing-md); border: none; background: {selectedApproverUserId === String(member.user_id) ? 'var(--accent-glow, rgba(225, 29, 72, 0.1))' : 'transparent'}; cursor: pointer; text-align: left; color: var(--text-primary);"
                          >
                            <span style="font-weight: 500;">{member.username}</span>
                            {#if member.is_owner}
                              <span class="badge badge-owner" style="font-size: 0.7rem;">Owner</span>
                            {:else}
                              <span style="font-size: 0.75rem; color: var(--text-secondary);">Admin</span>
                            {/if}
                          </button>
                        {:else}
                          <p style="padding: var(--spacing-sm) var(--spacing-md); color: var(--text-secondary); font-size: 0.9rem;">
                            No matching users found.
                          </p>
                        {/each}
                      </div>
                    {/if}
                    {#if approverError}
                      <span style="color: #ef4444; font-size: 0.85rem;">{approverError}</span>
                    {/if}
                    <div style="display: flex; gap: var(--spacing-sm); justify-content: flex-end;">
                      <button class="btn btn-secondary btn-sm" onclick={() => { showApproverForm = false; approverError = ""; selectedApproverUserId = ""; approverSearchQuery = ""; }}>
                        Cancel
                      </button>
                      <button class="btn btn-primary btn-sm" onclick={addApprover} disabled={!selectedApproverUserId || eligibleApprovers.length === 0}>
                        Add
                      </button>
                    </div>
                  </div>
                {/if}

                {#if approversLoading}
                  <div style="padding: var(--spacing-md); text-align: center; color: var(--text-secondary);">
                    Loading approvers...
                  </div>
                {:else if approvers.length === 0}
                  <div style="padding: var(--spacing-md); text-align: center; color: var(--text-secondary);">
                    <p>No approvers configured.</p>
                    <p style="font-size: 0.85rem; margin-top: var(--spacing-xs);">Add approvers to enable the approval workflow in production.</p>
                  </div>
                {:else}
                  <div style="display: flex; flex-direction: column; gap: var(--spacing-sm);">
                    {#each approvers as approver}
                      <div style="display: flex; justify-content: space-between; align-items: center; padding: var(--spacing-sm) var(--spacing-md); background: var(--bg-primary); border-radius: var(--radius-sm);">
                        <div>
                          <span style="font-weight: 500;">{approver.username}</span>
                          <span style="font-size: 0.8rem; color: var(--text-secondary); margin-left: var(--spacing-sm);">
                            Added {new Date(approver.created_at).toLocaleDateString()}
                          </span>
                        </div>
                        <button
                          class="btn btn-icon"
                          onclick={() => removeApprover(approver.user_id)}
                          title="Remove approver"
                          style="color: #ef4444;"
                        >
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="3 6 5 6 21 6" />
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                          </svg>
                        </button>
                      </div>
                    {/each}
                  </div>
                {/if}
              </div>
            </div>
          {/if}
        </div>
      </div>
    {/if}

    {#if activeTab === "agents"}
      <div class="section">
        <AgentManager {project} {isPlatformOwner} onagentschange={(list) => agents = list} />
      </div>
    {:else if activeTab === "usage"}
      <!-- Usage Section -->
      <div class="section">
        <div class="section-header">
          <h2>Project Usage</h2>
          <button
            class="btn btn-secondary"
            onclick={loadUsage}
            disabled={usageLoading}
          >
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polyline points="23 4 23 10 17 10" />
              <polyline points="1 20 1 14 7 14" />
              <path
                d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"
              />
            </svg>
            Refresh
          </button>
        </div>

        {#if usageLoading}
          <div class="loading">Loading usage data...</div>
        {:else if !usageData}
          <div class="empty-state">
            <p>No usage data available.</p>
            <p class="hint">
              Usage statistics will appear here once messages are sent in this
              project.
            </p>
          </div>
        {:else}
          <div class="usage-stats">
            {#if usageData.by_month && Object.keys(usageData.by_month).length > 0}
              <div class="month-selector" style="margin-bottom: var(--spacing-md);">
                <label for="month-filter" style="font-size:0.85rem;font-weight:500;color:var(--text-secondary);margin-right:0.5rem;">Period:</label>
                <select id="month-filter" bind:value={selectedUsageMonth} style="font-size:0.85rem;padding:0.3rem 0.6rem;border-radius:var(--radius-md);border:1px solid var(--border-color);background:var(--bg-secondary);color:var(--text-primary);">
                  <option value="all">All Time</option>
                  {#each Object.keys(usageData.by_month).sort().reverse() as month}
                    <option value={month}>{month}</option>
                  {/each}
                </select>
              </div>
            {/if}
            {#if selectedUsageMonth === 'all'}
            <div class="usage-summary">
              <div class="stat-card">
                <div class="stat-label">Total Interactions</div>
                <div class="stat-value">{usageData.total_interactions?.toLocaleString() || 0}</div>
              </div>
              <div class="stat-card">
                <div class="stat-label">Agents Used</div>
                <div class="stat-value">
                  {Object.keys(usageData.by_agent || {}).length}
                </div>
              </div>
            </div>
            {/if}

            {#if selectedUsageMonth !== 'all' && usageData.by_month?.[selectedUsageMonth]}
              {@const monthData = usageData.by_month[selectedUsageMonth]}
              <div class="usage-summary">
                <div class="stat-card">
                  <div class="stat-label">Interactions</div>
                  <div class="stat-value">{Object.values(monthData).reduce((s, a) => s + (a.interactions || 0), 0).toLocaleString()}</div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">Unique Users</div>
                  <div class="stat-value">{Object.values(monthData).reduce((s, a) => s + (a.user_count || 0), 0)}</div>
                </div>
                <div class="stat-card">
                  <div class="stat-label">Agents Active</div>
                  <div class="stat-value">{Object.keys(monthData).length}</div>
                </div>
              </div>
            {/if}

            {#if selectedUsageMonth === 'all' && Object.keys(usageData.by_agent || {}).length > 0}
              <div class="usage-by-agent">
                <h3>Usage by Agent</h3>
                <div class="table-container">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Agent Name</th>
                        <th>Interactions</th>
                        <th>Total Users</th>
                        <th>
                          Active Users
                          <span
                            class="tooltip-trigger"
                            title="Users who used this agent in the last 7 days"
                          >
                            <svg
                              width="14"
                              height="14"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              stroke-width="2"
                            >
                              <circle cx="12" cy="12" r="10" />
                              <line x1="12" y1="16" x2="12" y2="12" />
                              <line x1="12" y1="8" x2="12.01" y2="8" />
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
                          <td>{stats.interactions || 0}</td>
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
                <p class="hint">
                  Usage will be tracked when agents are used in conversations.
                </p>
              </div>
            {/if}

            <!-- Monthly Usage (shown when a specific month is selected) -->
            {#if selectedUsageMonth !== 'all' && usageData.by_month?.[selectedUsageMonth]}
              {@const monthAgents = usageData.by_month[selectedUsageMonth]}
              <div class="usage-by-agent">
                <h3>Usage for {selectedUsageMonth}</h3>
                <div class="table-container">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Agent</th>
                        <th>Interactions</th>
                        <th>Unique Users</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each Object.entries(monthAgents) as [agentName, stats]}
                        <tr>
                          <td class="cell-name"><strong>{agentName}</strong></td>
                          <td>{stats.interactions || 0}</td>
                          <td>{stats.user_count || 0}</td>
                        </tr>
                      {/each}
                    </tbody>
                  </table>
                </div>
              </div>
            {/if}

            <!-- All-Time Monthly Breakdown (hidden when month filter active) -->
            {#if selectedUsageMonth === 'all' && usageData.by_month && Object.keys(usageData.by_month).length > 0}
              <div class="usage-by-agent">
                <h3>Usage by Month</h3>
                <div class="table-container">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Month</th>
                        <th>Agent</th>
                        <th>Interactions</th>
                        <th>Unique Users</th>
                      </tr>
                    </thead>
                    <tbody>
                      {#each Object.entries(usageData.by_month || {}).sort(([a], [b]) => b.localeCompare(a)) as [month, agents]}
                        {#each Object.entries(agents) as [agentName, stats], idx}
                          <tr>
                            {#if idx === 0}
                              <td class="cell-month" rowspan={Object.entries(agents).length}>
                                <strong>{month}</strong>
                              </td>
                            {/if}
                            <td class="cell-name">{agentName}</td>
                            <td>{stats.interactions || 0}</td>
                            <td>{stats.user_count || 0}</td>
                          </tr>
                        {/each}
                      {/each}
                    </tbody>
                  </table>
                </div>
              </div>
            {/if}

            <!-- Site Analytics -->
            {#if siteAnalytics && siteAnalytics.summary}
              <div class="usage-by-agent" style="margin-top: var(--spacing-lg);">
                <h3>Site Analytics <span class="hint" style="font-weight:400;font-size:0.8rem;">(last 7 days)</span></h3>
                <div class="usage-summary">
                  <div class="stat-card">
                    <div class="stat-label">Page Views</div>
                    <div class="stat-value">{siteAnalytics.summary.page_views?.toLocaleString() || 0}</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-label">Unique Users</div>
                    <div class="stat-value">{siteAnalytics.summary.unique_users?.toLocaleString() || 0}</div>
                  </div>
                  <div class="stat-card">
                    <div class="stat-label">Interactions</div>
                    <div class="stat-value">{siteAnalytics.summary.interactions?.toLocaleString() || 0}</div>
                  </div>
                </div>

                {#if siteAnalytics.by_page?.length}
                  <div style="margin-top: var(--spacing-md);">
                    <h4>Views by Page</h4>
                    <div class="table-container">
                      <table class="data-table">
                        <thead>
                          <tr>
                            <th>Page Path</th>
                            <th>Views</th>
                            <th>Unique Users</th>
                          </tr>
                        </thead>
                        <tbody>
                          {#each siteAnalytics.by_page as row}
                            <tr>
                              <td class="cell-name">{row.page_path}</td>
                              <td>{row.views}</td>
                              <td>{row.unique_users}</td>
                            </tr>
                          {/each}
                        </tbody>
                      </table>
                    </div>
                  </div>
                {/if}

                {#if siteAnalytics.top_components?.length}
                  <div style="margin-top: var(--spacing-md);">
                    <h4>Top Components</h4>
                    <div class="table-container">
                      <table class="data-table">
                        <thead>
                          <tr>
                            <th>Component ID</th>
                            <th>Type</th>
                            <th>Interactions</th>
                          </tr>
                        </thead>
                        <tbody>
                          {#each siteAnalytics.top_components as comp}
                            <tr>
                              <td class="cell-name">{comp.component_id}</td>
                              <td>{comp.component_type || "—"}</td>
                              <td>{comp.interactions}</td>
                            </tr>
                          {/each}
                        </tbody>
                      </table>
                    </div>
                  </div>
                {/if}
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {:else if activeTab === "approval"}
      <!-- Approval / Change Requests Section -->
      <div class="section">
        <ChangeRequests {project} />
      </div>
    {:else if activeTab === "builder"}
      <div class="section site-builder-cta">
        <p class="site-builder-cta-text">Site Builder opens in a full-page view so you get a larger canvas.</p>
        <button
          type="button"
          class="site-builder-cta-btn"
          onclick={() => {
            window.history.pushState({}, "", `/${project}/site-builder`);
            window.dispatchEvent(new PopStateEvent("popstate"));
          }}
        >
          Open Site Builder
        </button>
      </div>
    {/if}
  </div>
</div>



<!-- LAN ID (Member) Form Modal -->
{#if showMemberForm}
  <div class="modal-overlay" onclick={closeMemberForm}>
    <div class="modal" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h3>{editingMember ? "Edit Member" : "Add LAN ID"}</h3>
        <button class="modal-close" onclick={closeMemberForm}>
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
      <form
        class="modal-body"
        onsubmit={(e) => {
          e.preventDefault();
          saveMember();
        }}
      >
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
            <p class="form-hint">
              LAN ID cannot be changed. Remove and re-add to change.
            </p>
          {/if}
        </div>
        <div class="form-group">
          <label for="member-role">Role</label>
          <select id="member-role" bind:value={memberForm.role}>
            <option value="member"
              >Member - Can use agents and view project</option
            >
            <option value="admin"
              >Admin - Can manage settings and members</option
            >
          </select>
        </div>
        <div class="form-group">
          <label for="member-agent-search">Agent Permissions</label>
          <p class="form-hint" style="margin-bottom: var(--spacing-sm);">
            Add agents this user can access.
          </p>

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
                    <button
                      type="button"
                      class="agent-tag-remove"
                      onclick={() => removeAgentPermission(agentId)}
                      title="Remove"
                    >
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
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
                  id="member-agent-search"
                  type="text"
                  placeholder="Search agents to add..."
                  bind:value={agentSearchQuery}
                  class="agent-search-input"
                />
              </div>

              {#if filteredAgents().length > 0}
                <div class="agent-search-results">
                  {#each filteredAgents() as agent}
                    <button
                      type="button"
                      class="agent-search-result"
                      onclick={() => addAgentPermission(agent.id)}
                    >
                      <span class="agent-result-name">{agent.name}</span>
                      <span class="agent-result-badges">
                        <span class="badge badge-{agent.connection_type}"
                          >{agent.connection_type}</span
                        >
                        {#if agent.is_default}
                          <span class="badge badge-default">Default</span>
                        {/if}
                      </span>
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        class="add-icon"
                      >
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
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
          <button
            type="button"
            class="btn btn-secondary"
            onclick={closeMemberForm}>Cancel</button
          >
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
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>
      <form
        class="modal-body"
        onsubmit={(e) => {
          e.preventDefault();
          saveGroup();
        }}
      >
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
            <p class="form-hint">
              Group details cannot be changed. Remove and re-add to modify.
            </p>
          {/if}
        </div>
        <div class="form-group">
          <label for="group-role">Role</label>
          <select id="group-role" bind:value={groupForm.role}>
            <option value="member"
              >Member - Can use agents and view project</option
            >
            <option value="admin"
              >Admin - Can manage settings and members</option
            >
          </select>
        </div>
        <div class="form-group">
          <label for="group-agent-search">Agent Permissions</label>
          <p class="form-hint" style="margin-bottom: var(--spacing-sm);">
            Add agents this group can access.
          </p>

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
                    <button
                      type="button"
                      class="agent-tag-remove"
                      onclick={() => removeGroupAgentPermission(agentId)}
                      title="Remove"
                    >
                      <svg
                        width="14"
                        height="14"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                      >
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
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
                  id="group-agent-search"
                  type="text"
                  placeholder="Search agents to add..."
                  bind:value={groupAgentSearchQuery}
                  class="agent-search-input"
                />
              </div>

              {#if filteredGroupAgents().length > 0}
                <div class="agent-search-results">
                  {#each filteredGroupAgents() as agent}
                    <button
                      type="button"
                      class="agent-search-result"
                      onclick={() => addGroupAgentPermission(agent.id)}
                    >
                      <span class="agent-result-name">{agent.name}</span>
                      <span class="agent-result-badges">
                        <span class="badge badge-{agent.connection_type}"
                          >{agent.connection_type}</span
                        >
                        {#if agent.is_default}
                          <span class="badge badge-default">Default</span>
                        {/if}
                      </span>
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        stroke-width="2"
                        class="add-icon"
                      >
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
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
          <button
            type="button"
            class="btn btn-secondary"
            onclick={closeGroupForm}>Cancel</button
          >
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

  .site-builder-cta {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-lg);
    padding: var(--spacing-xl);
  }

  .site-builder-cta-text {
    margin: 0;
    font-size: 0.9375rem;
    color: var(--text-secondary);
  }

  .site-builder-cta-btn {
    padding: 0.5rem 1.25rem;
    border-radius: var(--radius-full);
    border: none;
    background: var(--primary-accent);
    color: white;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.12s ease;
  }

  .site-builder-cta-btn:hover {
    background: var(--primary-accent-hover);
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
    background-color: rgba(225, 29, 72, 0.15);
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
    background-color: rgba(255, 255, 255, 0.06);
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
    /* Removed opacity: 0.7 on secondary text — use text-muted directly for WCAG AA contrast */
    color: var(--text-muted);
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

  .cell-month {
    font-weight: 600;
    background-color: var(--bg-secondary);
    vertical-align: middle;
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

  .badge-default {
    background-color: rgba(225, 29, 72, 0.15);
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
    border: 1px solid #334155;
    border-radius: var(--radius-md);
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.95rem;
  }

  .agent-search-input:focus {
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
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
    border: 1px solid #334155;
    border-radius: var(--radius-sm);
    background-color: var(--bg-primary);
    color: var(--text-primary);
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
    from {
      opacity: 0;
    }
    to {
      opacity: 1;
    }
  }

  .modal {
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    width: 100%;
    max-width: 500px;
    max-height: 90vh;
    overflow-y: auto;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
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
    margin: 0;
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
  .form-group select {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    border: 1px solid #334155;
    border-radius: var(--radius-md);
    background-color: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.95rem;
  }

  .form-group input:focus,
  .form-group select:focus {
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
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

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-xl);
    padding-top: var(--spacing-lg);
    border-top: 1px solid var(--border-color);
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

  .spinner {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .approver-option {
    transition: background-color 0.15s ease;
  }

  .approver-option:hover {
    background-color: var(--bg-secondary) !important;
  }

  .approver-option.selected {
    background-color: var(--accent-glow, rgba(225, 29, 72, 0.1)) !important;
    border-left: 3px solid var(--primary-accent) !important;
  }

</style>
