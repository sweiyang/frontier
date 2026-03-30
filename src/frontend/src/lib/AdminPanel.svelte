<script>
  import { onMount } from "svelte";
  import { authFetch } from "./utils.js";

  let { appName = "Frontier AI", onback = () => {} } = $props();

  let grants = $state([]);
  let loading = $state(true);
  let grantType = $state("user");
  let grantValue = $state("");
  let displayName = $state("");
  let adding = $state(false);
  let error = $state("");
  let deleteConfirmId = $state(null);

  let projects = $state([]);
  let projectsLoading = $state(true);
  let deleteProjectConfirm = $state(null);
  let deletingProject = $state(false);
  let projectSearch = $state("");

  let usageData = $state(null);
  let usageLoading = $state(true);
  let expandedMonth = $state(null);

  let filteredProjects = $derived(
    projectSearch
      ? projects.filter(p =>
          p.project_name.toLowerCase().includes(projectSearch.toLowerCase()) ||
          (p.owner || "").toLowerCase().includes(projectSearch.toLowerCase()) ||
          (p.description || "").toLowerCase().includes(projectSearch.toLowerCase())
        )
      : projects
  );

  let currentMonthUsage = $derived(
    usageData?.months?.[0] ?? { interactions: 0, unique_users: 0, active_projects: 0 }
  );

  function formatMonth(monthStr) {
    const [year, month] = monthStr.split("-");
    const date = new Date(parseInt(year), parseInt(month) - 1);
    return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
  }

  onMount(async () => {
    await Promise.all([loadGrants(), loadProjects(), loadUsage()]);
  });

  async function loadGrants() {
    loading = true;
    try {
      const response = await authFetch("/admin/workbench-access");
      if (response.ok) {
        const data = await response.json();
        grants = data.grants || [];
      }
    } catch (err) {
      console.error("Failed to load grants:", err);
    } finally {
      loading = false;
    }
  }

  async function handleAdd() {
    if (!grantValue.trim()) return;
    adding = true;
    error = "";
    try {
      const response = await authFetch("/admin/workbench-access", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          grant_type: grantType,
          grant_value: grantValue.trim(),
          display_name: displayName.trim() || null,
        }),
      });
      if (response.ok) {
        grantValue = "";
        displayName = "";
        await loadGrants();
      } else {
        const data = await response.json();
        error = data.detail || "Failed to add grant";
      }
    } catch (err) {
      error = "Network error";
    } finally {
      adding = false;
    }
  }

  async function loadProjects() {
    projectsLoading = true;
    try {
      const response = await authFetch("/admin/projects");
      if (response.ok) {
        const data = await response.json();
        projects = data.projects || [];
      }
    } catch (err) {
      console.error("Failed to load projects:", err);
    } finally {
      projectsLoading = false;
    }
  }

  async function handleDeleteProject(projectName) {
    deletingProject = true;
    try {
      const response = await authFetch(`/admin/projects/${encodeURIComponent(projectName)}`, {
        method: "DELETE",
      });
      if (response.ok) {
        deleteProjectConfirm = null;
        await loadProjects();
      }
    } catch (err) {
      console.error("Failed to delete project:", err);
    } finally {
      deletingProject = false;
    }
  }

  async function handleDelete(grantId) {
    try {
      const response = await authFetch(`/admin/workbench-access/${grantId}`, {
        method: "DELETE",
      });
      if (response.ok) {
        deleteConfirmId = null;
        await loadGrants();
      }
    } catch (err) {
      console.error("Failed to delete grant:", err);
    }
  }

  async function loadUsage() {
    usageLoading = true;
    try {
      const response = await authFetch("/admin/usage");
      if (response.ok) {
        usageData = await response.json();
      }
    } catch (err) {
      console.error("Failed to load usage:", err);
    } finally {
      usageLoading = false;
    }
  }
</script>

<div class="admin-container">
  <header class="admin-header">
    <div class="header-left">
      <button class="back-btn" onclick={onback}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M19 12H5" />
          <polyline points="12 19 5 12 12 5" />
        </svg>
        <span>Back</span>
      </button>
    </div>
    <div class="header-right">
      <div class="admin-badge">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        </svg>
        <span>Platform Admin</span>
      </div>
    </div>
  </header>

  <div class="admin-body">
    <div class="admin-content">
      <div class="section">
        <h2 class="section-title">Platform Usage</h2>
        <p class="section-desc">
          Monthly usage across all projects on the platform.
        </p>

        {#if usageLoading}
          <div class="usage-cards">
            {#each [1, 2, 3] as _}
              <div class="usage-card">
                <div class="usage-card-label">Loading...</div>
                <div class="usage-card-value">—</div>
              </div>
            {/each}
          </div>
        {:else if usageData}
          <div class="usage-cards">
            <div class="usage-card">
              <div class="usage-card-label">Interactions this month</div>
              <div class="usage-card-value">{currentMonthUsage.interactions.toLocaleString()}</div>
            </div>
            <div class="usage-card">
              <div class="usage-card-label">Unique users this month</div>
              <div class="usage-card-value">{currentMonthUsage.unique_users.toLocaleString()}</div>
            </div>
            <div class="usage-card">
              <div class="usage-card-label">Active projects this month</div>
              <div class="usage-card-value">{currentMonthUsage.active_projects.toLocaleString()}</div>
            </div>
          </div>

          <div class="grants-table-wrapper">
            {#if usageData.months.length === 0}
              <div class="table-empty">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M21 12V7H5a2 2 0 0 1 0-4h14v4" />
                  <path d="M3 5v14a2 2 0 0 0 2 2h16v-5" />
                  <path d="M18 12a2 2 0 0 0 0 4h4v-4Z" />
                </svg>
                <h3>No usage data yet</h3>
                <p>Usage will appear here once users start interacting with agents</p>
              </div>
            {:else}
              <table class="grants-table usage-table">
                <thead>
                  <tr>
                    <th>Month</th>
                    <th>Interactions</th>
                    <th>Unique Users</th>
                    <th>Active Projects</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {#each usageData.months as entry}
                    <tr class="expandable-row" onclick={() => expandedMonth = expandedMonth === entry.month ? null : entry.month}>
                      <td class="month-cell">{formatMonth(entry.month)}</td>
                      <td class="count-cell">{entry.interactions.toLocaleString()}</td>
                      <td class="count-cell">{entry.unique_users.toLocaleString()}</td>
                      <td class="count-cell">{entry.active_projects.toLocaleString()}</td>
                      <td class="action-cell">
                        <svg
                          class="expand-icon"
                          class:expanded={expandedMonth === entry.month}
                          width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
                        >
                          <polyline points="9 18 15 12 9 6" />
                        </svg>
                      </td>
                    </tr>
                    {#if expandedMonth === entry.month}
                      <tr class="nested-detail-row">
                        <td colspan="5">
                          {#if entry.projects.length === 0}
                            <div class="nested-empty">No project breakdown available</div>
                          {:else}
                            <table class="nested-table">
                              <thead>
                                <tr>
                                  <th>Project</th>
                                  <th>Interactions</th>
                                  <th>Unique Users</th>
                                  <th>Agents</th>
                                </tr>
                              </thead>
                              <tbody>
                                {#each entry.projects as proj}
                                  <tr>
                                    <td class="project-name-nested">{proj.project_name}</td>
                                    <td class="count-cell">{proj.interactions.toLocaleString()}</td>
                                    <td class="count-cell">{proj.unique_users.toLocaleString()}</td>
                                    <td class="count-cell">{proj.agent_count}</td>
                                  </tr>
                                {/each}
                              </tbody>
                            </table>
                          {/if}
                        </td>
                      </tr>
                    {/if}
                  {/each}
                </tbody>
              </table>
            {/if}
          </div>
          {#if usageData.totals}
            <div class="table-footer">
              All time: {usageData.totals.interactions.toLocaleString()} interactions, {usageData.totals.unique_users.toLocaleString()} users, {usageData.totals.active_projects.toLocaleString()} projects
            </div>
          {/if}
        {/if}
      </div>

      <div class="section">
        <h2 class="section-title">Workbench Access</h2>
        <p class="section-desc">
          Control who can access the Workbench. Add users by LAN ID or AD groups by distinguished name.
        </p>

        <!-- Add grant form -->
        <div class="add-form">
          <div class="form-row">
            <div class="type-toggle">
              <button
                class="toggle-btn"
                class:active={grantType === "user"}
                onclick={() => grantType = "user"}
              >User (LAN ID)</button>
              <button
                class="toggle-btn"
                class:active={grantType === "ad_group"}
                onclick={() => grantType = "ad_group"}
              >AD Group</button>
            </div>
          </div>
          <div class="form-row form-inputs">
            <input
              type="text"
              class="form-input"
              placeholder={grantType === "user" ? "Enter LAN ID (username)" : "Enter AD group DN (e.g. CN=group,OU=Groups,DC=example,DC=com)"}
              bind:value={grantValue}
              onkeydown={(e) => e.key === "Enter" && handleAdd()}
            />
            <input
              type="text"
              class="form-input display-name-input"
              placeholder="Display name (optional)"
              bind:value={displayName}
              onkeydown={(e) => e.key === "Enter" && handleAdd()}
            />
            <button class="add-btn" onclick={handleAdd} disabled={adding || !grantValue.trim()}>
              {adding ? "Adding..." : "Add"}
            </button>
          </div>
          {#if error}
            <div class="form-error">{error}</div>
          {/if}
        </div>

        <!-- Grants table -->
        <div class="grants-table-wrapper">
          {#if loading}
            <div class="table-loading">
              <div class="spinner"></div>
              <span>Loading grants...</span>
            </div>
          {:else if grants.length === 0}
            <div class="table-empty">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              <h3>No access grants yet</h3>
              <p>Add users or AD groups above to grant workbench access</p>
            </div>
          {:else}
            <table class="grants-table">
              <thead>
                <tr>
                  <th>Type</th>
                  <th>Value</th>
                  <th>Display Name</th>
                  <th>Granted By</th>
                  <th>Date</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {#each grants as grant}
                  <tr>
                    <td>
                      <span class="type-badge" class:user={grant.grant_type === "user"} class:group={grant.grant_type === "ad_group"}>
                        {grant.grant_type === "user" ? "User" : "AD Group"}
                      </span>
                    </td>
                    <td class="value-cell">{grant.grant_value}</td>
                    <td class="display-name-cell">{grant.display_name || "—"}</td>
                    <td>{grant.granted_by}</td>
                    <td class="date-cell">{new Date(grant.created_at).toLocaleDateString()}</td>
                    <td class="action-cell">
                      {#if deleteConfirmId === grant.id}
                        <div class="confirm-delete">
                          <span>Remove?</span>
                          <button class="confirm-yes" onclick={() => handleDelete(grant.id)}>Yes</button>
                          <button class="confirm-no" onclick={() => deleteConfirmId = null}>No</button>
                        </div>
                      {:else}
                        <button class="delete-btn" onclick={() => deleteConfirmId = grant.id} title="Remove grant">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6" />
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                          </svg>
                        </button>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {/if}
        </div>
      </div>

      <div class="section">
        <h2 class="section-title">Project Management</h2>
        <p class="section-desc">
          View and manage all projects on the platform. Deleting a project removes all its conversations, agents, and data permanently.
        </p>

        <div class="project-search">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            class="form-input search-input"
            placeholder="Search projects..."
            bind:value={projectSearch}
          />
        </div>

        <div class="grants-table-wrapper">
          {#if projectsLoading}
            <div class="table-loading">
              <div class="spinner"></div>
              <span>Loading projects...</span>
            </div>
          {:else if projects.length === 0}
            <div class="table-empty">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
              </svg>
              <h3>No projects yet</h3>
              <p>Projects will appear here once created</p>
            </div>
          {:else if filteredProjects.length === 0}
            <div class="table-empty">
              <h3>No matching projects</h3>
              <p>Try a different search term</p>
            </div>
          {:else}
            <table class="grants-table projects-table">
              <thead>
                <tr>
                  <th>Project Name</th>
                  <th>Owner</th>
                  <th>Agents</th>
                  <th>Members</th>
                  <th>Created</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {#each filteredProjects as project}
                  <tr>
                    <td>
                      <div class="project-name-cell">
                        <span class="project-name">{project.project_name}</span>
                        {#if project.description}
                          <span class="project-desc">{project.description}</span>
                        {/if}
                      </div>
                    </td>
                    <td>{project.owner}</td>
                    <td class="count-cell">{project.agent_count}</td>
                    <td class="count-cell">{project.member_count}</td>
                    <td class="date-cell">{project.created_at ? new Date(project.created_at).toLocaleDateString() : "—"}</td>
                    <td class="action-cell">
                      {#if deleteProjectConfirm === project.project_name}
                        <div class="confirm-delete">
                          <span>Delete?</span>
                          <button class="confirm-yes" onclick={() => handleDeleteProject(project.project_name)} disabled={deletingProject}>
                            {deletingProject ? "..." : "Yes"}
                          </button>
                          <button class="confirm-no" onclick={() => deleteProjectConfirm = null}>No</button>
                        </div>
                      {:else}
                        <button class="delete-btn" onclick={() => deleteProjectConfirm = project.project_name} title="Delete project">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="3 6 5 6 21 6" />
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                          </svg>
                        </button>
                      {/if}
                    </td>
                  </tr>
                {/each}
              </tbody>
            </table>
          {/if}
        </div>
        {#if !projectsLoading && projects.length > 0}
          <div class="table-footer">
            {filteredProjects.length} of {projects.length} project{projects.length !== 1 ? "s" : ""}
          </div>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  .admin-container {
    width: 100%;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background-color: var(--bg-primary);
  }

  .admin-header {
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
    background: none;
    border: none;
    cursor: pointer;
  }

  .back-btn:hover {
    background-color: var(--bg-secondary);
    color: var(--text-primary);
  }

  .header-right {
    display: flex;
    align-items: center;
  }

  .admin-badge {
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

  .admin-body {
    flex: 1;
    overflow-y: auto;
    display: flex;
    justify-content: center;
  }

  .admin-content {
    width: 100%;
    max-width: 900px;
    padding: 2.5rem 1.5rem;
  }

  .section {
    margin-bottom: 2rem;
  }

  .section-title {
    font-family: var(--font-display);
    font-size: 1.5rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  .section-desc {
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin-bottom: 1.5rem;
  }

  /* Add form */
  .add-form {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    margin-bottom: 1.5rem;
  }

  .form-row {
    margin-bottom: 0.75rem;
  }

  .form-row:last-child {
    margin-bottom: 0;
  }

  .type-toggle {
    display: flex;
    gap: 0;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-full);
    overflow: hidden;
    width: fit-content;
  }

  .toggle-btn {
    padding: 0.4rem 1rem;
    font-size: 0.85rem;
    font-weight: 500;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .toggle-btn.active {
    background: var(--text-primary);
    color: var(--bg-primary);
  }

  .form-inputs {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
  }

  .form-input {
    flex: 1;
    min-width: 200px;
    padding: 0.6rem 0.9rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    font-size: 0.9rem;
    background: var(--bg-primary);
    color: var(--text-primary);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .form-input:focus {
    outline: none;
    border-color: var(--text-primary);
    box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
  }

  .display-name-input {
    max-width: 200px;
    flex: 0 1 200px;
  }

  .add-btn {
    padding: 0.6rem 1.25rem;
    background: var(--text-primary);
    color: var(--bg-primary);
    border: none;
    border-radius: var(--radius-full);
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: opacity 0.15s ease;
    white-space: nowrap;
  }

  .add-btn:hover:not(:disabled) {
    opacity: 0.85;
  }

  .add-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .form-error {
    margin-top: 0.5rem;
    color: #dc2626;
    font-size: 0.85rem;
    background: #fef2f2;
    padding: 0.4rem 0.75rem;
    border-radius: var(--radius-md);
  }

  /* Grants table */
  .grants-table-wrapper {
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    overflow: hidden;
  }

  .table-loading {
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

  .table-empty {
    text-align: center;
    padding: 3rem 1.5rem;
    color: var(--text-secondary);
  }

  .table-empty svg {
    opacity: 0.35;
    margin-bottom: 0.75rem;
  }

  .table-empty h3 {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  .table-empty p {
    font-size: 0.85rem;
    margin: 0;
  }

  .grants-table {
    width: 100%;
    border-collapse: collapse;
  }

  .grants-table th {
    text-align: left;
    padding: 0.65rem 1rem;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-secondary);
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
  }

  .grants-table td {
    padding: 0.65rem 1rem;
    font-size: 0.9rem;
    color: var(--text-primary);
    border-bottom: 1px solid var(--border-color);
  }

  .grants-table tr:last-child td {
    border-bottom: none;
  }

  .grants-table tr:hover td {
    background: rgba(0, 0, 0, 0.02);
  }

  .type-badge {
    display: inline-block;
    padding: 0.15rem 0.5rem;
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 600;
  }

  .type-badge.user {
    background: #eff6ff;
    color: #3b82f6;
  }

  .type-badge.group {
    background: #fefce8;
    color: #ca8a04;
  }

  .value-cell {
    font-family: monospace;
    font-size: 0.85rem;
    word-break: break-all;
  }

  .display-name-cell {
    color: var(--text-secondary);
  }

  .date-cell {
    white-space: nowrap;
    color: var(--text-secondary);
    font-size: 0.85rem;
  }

  .action-cell {
    width: 1%;
    white-space: nowrap;
  }

  .delete-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 32px;
    height: 32px;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .delete-btn:hover {
    background: #fef2f2;
    color: #dc2626;
  }

  .confirm-delete {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    font-size: 0.8rem;
  }

  .confirm-delete span {
    color: var(--text-secondary);
  }

  .confirm-yes {
    padding: 0.2rem 0.5rem;
    background: #dc2626;
    color: white;
    border: none;
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
  }

  .confirm-no {
    padding: 0.2rem 0.5rem;
    background: var(--bg-secondary);
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
    font-weight: 500;
    cursor: pointer;
  }

  /* Project management */
  .project-search {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 1rem;
    color: var(--text-secondary);
  }

  .search-input {
    flex: 1;
    max-width: 320px;
  }

  .project-name-cell {
    display: flex;
    flex-direction: column;
    gap: 0.1rem;
  }

  .project-name {
    font-weight: 500;
    font-family: monospace;
    font-size: 0.85rem;
  }

  .project-desc {
    font-size: 0.75rem;
    color: var(--text-secondary);
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 280px;
  }

  .count-cell {
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.85rem;
  }

  .table-footer {
    padding: 0.5rem 1rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
    text-align: right;
  }

  /* Usage cards */
  .usage-cards {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  .usage-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
  }

  .usage-card-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
  }

  .usage-card-value {
    font-family: var(--font-display);
    font-size: 2rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  /* Usage table */
  .expandable-row {
    cursor: pointer;
  }

  .expandable-row:hover td {
    background: rgba(0, 0, 0, 0.03);
  }

  .month-cell {
    font-weight: 500;
  }

  .expand-icon {
    color: var(--text-secondary);
    transition: transform 0.2s ease;
  }

  .expand-icon.expanded {
    transform: rotate(90deg);
  }

  .nested-detail-row td {
    padding: 0 !important;
    background: var(--bg-secondary);
  }

  .nested-table {
    width: 100%;
    border-collapse: collapse;
  }

  .nested-table th {
    text-align: left;
    padding: 0.5rem 1rem 0.5rem 2rem;
    font-size: 0.65rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border-color);
  }

  .nested-table td {
    padding: 0.5rem 1rem 0.5rem 2rem;
    font-size: 0.85rem;
    color: var(--text-secondary);
    border-bottom: 1px solid var(--border-color);
  }

  .nested-table tr:last-child td {
    border-bottom: none;
  }

  .project-name-nested {
    font-family: monospace;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .nested-empty {
    padding: 1rem 2rem;
    font-size: 0.85rem;
    color: var(--text-muted);
  }

  @media (max-width: 768px) {
    .form-inputs {
      flex-direction: column;
    }

    .form-input, .display-name-input {
      max-width: none;
      width: 100%;
    }

    .grants-table th:nth-child(3),
    .grants-table td:nth-child(3),
    .grants-table th:nth-child(4),
    .grants-table td:nth-child(4) {
      display: none;
    }

    .projects-table th:nth-child(3),
    .projects-table td:nth-child(3),
    .projects-table th:nth-child(4),
    .projects-table td:nth-child(4) {
      display: none;
    }

    .usage-cards {
      grid-template-columns: 1fr;
    }

    .usage-table th:nth-child(3),
    .usage-table td:nth-child(3),
    .usage-table th:nth-child(4),
    .usage-table td:nth-child(4) {
      display: none;
    }
  }
</style>
