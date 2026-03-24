<script>
  import { onMount } from "svelte";
  import { authFetch, authPost, getUser } from "./utils.js";

  let { project = "" } = $props();

  // State
  let changeRequests = $state([]);
  let requestsLoading = $state(true);
  let statusFilter = $state("all");
  let currentUserId = $state(null);

  // Selected change request for detail view
  let selectedRequest = $state(null);
  let selectedRequestDetail = $state(null);
  let detailLoading = $state(false);
  let actionComment = $state("");

  // Check if current user is the requester (cannot approve own request)
  let isRequester = $derived(
    selectedRequestDetail && currentUserId && 
    selectedRequestDetail.requested_by === currentUserId
  );

  onMount(async () => {
    const user = getUser();
    if (user) {
      currentUserId = user.user_id;
    }
    await loadChangeRequests();
  });

  async function loadChangeRequests() {
    requestsLoading = true;
    try {
      const url = statusFilter === "all"
        ? `/projects/${project}/change-requests`
        : `/projects/${project}/change-requests?status=${statusFilter}`;
      const response = await authFetch(url);
      if (response.ok) {
        const data = await response.json();
        changeRequests = data.change_requests || [];
      }
    } catch (error) {
      console.error("Failed to load change requests:", error);
    } finally {
      requestsLoading = false;
    }
  }

  async function viewRequest(request) {
    selectedRequest = request;
    detailLoading = true;
    actionComment = "";
    try {
      const response = await authFetch(`/projects/${project}/change-requests/${request.id}`);
      if (response.ok) {
        selectedRequestDetail = await response.json();
      } else {
        selectedRequestDetail = request;
      }
    } catch (error) {
      selectedRequestDetail = request;
    } finally {
      detailLoading = false;
    }
  }

  function closeDetail() {
    selectedRequest = null;
    selectedRequestDetail = null;
    actionComment = "";
  }

  async function approveRequest(requestId) {
    try {
      const response = await authPost(`/projects/${project}/change-requests/${requestId}/approve`, {
        comment: actionComment,
      });

      if (response.ok) {
        await loadChangeRequests();
        closeDetail();
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to approve request");
      }
    } catch (error) {
      alert("Failed to approve request");
    }
  }

  async function rejectRequest(requestId) {
    if (!actionComment.trim()) {
      alert("Please provide a reason for rejection");
      return;
    }

    try {
      const response = await authPost(`/projects/${project}/change-requests/${requestId}/reject`, {
        comment: actionComment,
      });

      if (response.ok) {
        await loadChangeRequests();
        closeDetail();
      } else {
        const error = await response.json();
        alert(error.detail || "Failed to reject request");
      }
    } catch (error) {
      alert("Failed to reject request");
    }
  }

  function onFilterChange(e) {
    statusFilter = e.target.value;
    loadChangeRequests();
  }

  function formatDate(dateStr) {
    if (!dateStr) return "-";
    return new Date(dateStr).toLocaleString();
  }

  function getStatusBadgeClass(status) {
    switch (status) {
      case "pending": return "badge-warning";
      case "approved": return "badge-success";
      case "rejected": return "badge-error";
      default: return "";
    }
  }

  function getRequestTypeLabel(type) {
    switch (type) {
      case "create": return "Create Agent";
      case "update": return "Update Agent";
      case "delete": return "Delete Agent";
      default: return type;
    }
  }

  // Compute the differences between current agent and proposed changes
  function computeDiff(currentAgent, payload) {
    if (!currentAgent || !payload) return null;
    
    const changes = [];
    const fieldsToCompare = ["name", "endpoint", "connection_type", "is_default", "extras", "auth", "icon"];
    
    for (const field of fieldsToCompare) {
      const oldVal = currentAgent[field];
      const newVal = payload[field];
      
      // Skip if both are null/undefined
      if (oldVal == null && newVal == null) continue;
      
      // Compare JSON-stringified values for objects
      const oldStr = typeof oldVal === "object" ? JSON.stringify(oldVal) : String(oldVal ?? "");
      const newStr = typeof newVal === "object" ? JSON.stringify(newVal) : String(newVal ?? "");
      
      if (oldStr !== newStr) {
        changes.push({
          field,
          oldValue: oldVal,
          newValue: newVal,
        });
      }
    }
    
    return changes;
  }

  // Computed diff for current request
  let requestDiff = $derived.by(() => {
    if (!selectedRequestDetail) return null;
    if (selectedRequestDetail.request_type !== "update") return null;
    // Use original_agent (stored at request creation time) for accurate diff
    return computeDiff(selectedRequestDetail.original_agent, selectedRequestDetail.payload);
  });

  let pendingCount = $derived(changeRequests.filter(r => r.status === "pending").length);
</script>

<div class="change-requests">
  <!-- Header -->
  <div class="cr-header">
    <div class="cr-title-area">
      <h2>Change Requests</h2>
      {#if pendingCount > 0}
        <span class="pending-badge">{pendingCount} pending</span>
      {/if}
    </div>
    <div class="cr-actions">
      <select class="filter-select" value={statusFilter} onchange={onFilterChange}>
        <option value="all">All statuses</option>
        <option value="pending">Pending</option>
        <option value="approved">Approved</option>
        <option value="rejected">Rejected</option>
      </select>
      <button class="btn btn-secondary btn-sm" onclick={loadChangeRequests} disabled={requestsLoading}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="23 4 23 10 17 10" />
          <polyline points="1 20 1 14 7 14" />
          <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" />
        </svg>
        Refresh
      </button>
    </div>
  </div>

  <!-- Request List -->
  {#if requestsLoading}
    <div class="loading">Loading change requests...</div>
  {:else if changeRequests.length === 0}
    <div class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <path d="M9 11l3 3L22 4" />
          <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
        </svg>
      </div>
      <p>No change requests found.</p>
      <p class="hint">Change requests appear here when agent modifications are made in production.</p>
    </div>
  {:else}
    <div class="requests-list">
      {#each changeRequests as request}
        <button class="request-card" onclick={() => viewRequest(request)}>
          <div class="request-left">
            <div class="request-id">#{request.id}</div>
            <div class="request-main">
              <span class="request-type">{getRequestTypeLabel(request.request_type)}</span>
              <span class="request-meta">
                <span class="request-requester">by {request.requested_by_username || `User #${request.requested_by}`}</span>
                <span class="request-date">{formatDate(request.created_at)}</span>
              </span>
            </div>
          </div>
          <div class="request-right">
            <span class="request-approvals">{request.current_approvals}/{request.required_approvals}</span>
            <span class="badge {getStatusBadgeClass(request.status)}">{request.status}</span>
          </div>
        </button>
      {/each}
    </div>
  {/if}
</div>

<!-- Change Request Detail Modal -->
{#if selectedRequest}
  <div class="modal-overlay" onclick={closeDetail} role="dialog" aria-modal="true" tabindex="-1" onkeydown={(e) => e.key === 'Escape' && closeDetail()}>
    <div class="modal" onclick={(e) => e.stopPropagation()} role="document">
      <div class="modal-header">
        <h2>Change Request #{selectedRequest.id}</h2>
        <button class="close-btn" onclick={closeDetail} aria-label="Close">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      </div>

      <div class="modal-body">
        {#if detailLoading}
          <div class="loading">Loading details...</div>
        {:else if selectedRequestDetail}
          <div class="detail-grid">
            <div class="detail-item">
              <span class="detail-label">Type</span>
              <span>{getRequestTypeLabel(selectedRequestDetail.request_type)}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Status</span>
              <span class="badge {getStatusBadgeClass(selectedRequestDetail.status)}">
                {selectedRequestDetail.status}
              </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Requested By</span>
              <span class="requester-name">
                {selectedRequestDetail.requested_by_username || `User #${selectedRequestDetail.requested_by}`}
                {#if isRequester}
                  <span class="badge badge-info">You</span>
                {/if}
              </span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Approvals</span>
              <span>{selectedRequestDetail.current_approvals}/{selectedRequestDetail.required_approvals} ({selectedRequestDetail.approval_type})</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Created</span>
              <span>{formatDate(selectedRequestDetail.created_at)}</span>
            </div>
            {#if selectedRequestDetail.resolved_at}
              <div class="detail-item">
                <span class="detail-label">Resolved</span>
                <span>{formatDate(selectedRequestDetail.resolved_at)}</span>
              </div>
            {/if}
          </div>

          <!-- Show diff for update requests, full payload for create/delete -->
          {#if selectedRequestDetail.request_type === "update" && requestDiff && requestDiff.length > 0}
            <div class="diff-section">
              <span class="detail-label">Changes</span>
              <div class="diff-list">
                {#each requestDiff as change}
                  <div class="diff-item">
                    <span class="diff-field">{change.field}</span>
                    <div class="diff-values">
                      <div class="diff-old">
                        <span class="diff-label">Before:</span>
                        <code>{typeof change.oldValue === "object" ? JSON.stringify(change.oldValue, null, 2) : String(change.oldValue ?? "(empty)")}</code>
                      </div>
                      <div class="diff-new">
                        <span class="diff-label">After:</span>
                        <code>{typeof change.newValue === "object" ? JSON.stringify(change.newValue, null, 2) : String(change.newValue ?? "(empty)")}</code>
                      </div>
                    </div>
                  </div>
                {/each}
              </div>
            </div>
          {:else if selectedRequestDetail.request_type === "update" && (!requestDiff || requestDiff.length === 0)}
            <div class="payload-section">
              <span class="detail-label">Changes</span>
              <p class="no-changes">No differences detected (agent may have been modified since this request).</p>
            </div>
          {:else}
            <div class="payload-section">
              <span class="detail-label">{selectedRequestDetail.request_type === "delete" ? "Agent to Delete" : "New Agent"}</span>
              <pre>{JSON.stringify(selectedRequestDetail.payload, null, 2)}</pre>
            </div>
          {/if}

          {#if selectedRequestDetail.approvals && selectedRequestDetail.approvals.length > 0}
            <div class="history-section">
              <span class="detail-label">Approval History</span>
              <div class="approval-history">
                {#each selectedRequestDetail.approvals as action}
                  <div class="approval-item">
                    <span class="action-user">{action.username}</span>
                    <span class="badge {action.action === 'approve' ? 'badge-success' : 'badge-error'}">
                      {action.action}
                    </span>
                    <span class="action-time">{formatDate(action.created_at)}</span>
                    {#if action.comment}
                      <p class="action-comment">{action.comment}</p>
                    {/if}
                  </div>
                {/each}
              </div>
            </div>
          {/if}

          {#if selectedRequestDetail.status === "pending"}
            <div class="action-section">
              <span class="detail-label">Your Action</span>
              {#if isRequester}
                <div class="self-approval-warning">
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <span>You cannot approve or reject your own change request.</span>
                </div>
              {:else}
                <textarea
                  placeholder="Add a comment (required for rejection)"
                  bind:value={actionComment}
                  rows="3"
                ></textarea>
                <div class="action-buttons">
                  <button class="btn btn-success" onclick={() => approveRequest(selectedRequestDetail.id)}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    Approve
                  </button>
                  <button class="btn btn-danger" onclick={() => rejectRequest(selectedRequestDetail.id)}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <line x1="18" y1="6" x2="6" y2="18" />
                      <line x1="6" y1="6" x2="18" y2="18" />
                    </svg>
                    Reject
                  </button>
                </div>
              {/if}
            </div>
          {/if}
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .change-requests {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .cr-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: var(--spacing-md);
  }

  .cr-title-area {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .cr-title-area h2 {
    margin: 0;
    font-size: 1.15rem;
  }

  .pending-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: var(--radius-full, 999px);
    font-size: 0.8rem;
    font-weight: 600;
    background: rgba(234, 179, 8, 0.15);
    color: #eab308;
  }

  .cr-actions {
    display: flex;
    gap: var(--spacing-sm);
    align-items: center;
  }

  .filter-select {
    padding: var(--spacing-xs) var(--spacing-sm);
    border: 1px solid #334155;
    border-radius: var(--radius-sm);
    background: var(--bg-primary);
    color: var(--text-primary);
    font-size: 0.85rem;
    cursor: pointer;
  }

  .filter-select:focus {
    outline: none;
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
  }

  .requests-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .request-card {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: left;
    width: 100%;
  }

  .request-card:hover {
    border-color: var(--primary-accent);
    background: #1e293b;
  }

  .request-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }

  .request-id {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-secondary);
    min-width: 40px;
  }

  .request-main {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .request-type {
    font-weight: 500;
    font-size: 0.95rem;
  }

  .request-meta {
    display: flex;
    gap: var(--spacing-sm);
    align-items: center;
  }

  .request-requester {
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .request-date {
    font-size: 0.8rem;
    color: var(--text-muted, var(--text-secondary));
  }

  .request-date::before {
    content: "•";
    margin-right: var(--spacing-sm);
  }

  .request-right {
    display: flex;
    align-items: center;
    gap: var(--spacing-md);
  }

  .request-approvals {
    font-size: 0.85rem;
    color: var(--text-secondary);
  }

  .loading,
  .empty-state {
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
  }

  .empty-icon {
    opacity: 0.3;
    margin-bottom: var(--spacing-sm);
  }

  .empty-state .hint {
    font-size: 0.85rem;
    margin-top: var(--spacing-xs);
  }

  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: var(--radius-sm);
    font-size: 0.8rem;
    font-weight: 500;
    text-transform: uppercase;
  }

  .badge-warning {
    background: rgba(234, 179, 8, 0.15);
    color: #eab308;
  }

  .badge-success {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
  }

  .badge-error {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
  }

  .btn {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: var(--spacing-sm) var(--spacing-md);
    border: none;
    border-radius: var(--radius-sm);
    cursor: pointer;
    font-size: 0.9rem;
    transition: all 0.2s;
  }

  .btn-sm {
    padding: var(--spacing-xs) var(--spacing-sm);
    font-size: 0.85rem;
  }

  .btn-secondary {
    background: transparent;
    color: var(--text-primary);
    border: 1px solid var(--border-color);
  }

  .btn-success {
    background: #22c55e;
    color: white;
  }

  .btn-danger {
    background: #ef4444;
    color: white;
  }

  .btn:hover {
    opacity: 0.9;
  }

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  /* Modal */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }

  .modal {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    width: 90%;
    max-width: 620px;
    max-height: 90vh;
    overflow-y: auto;
  }

  .modal-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-lg);
    border-bottom: 1px solid var(--border-color);
  }

  .modal-header h2 {
    margin: 0;
    font-size: 1.15rem;
  }

  .close-btn {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-secondary);
    padding: var(--spacing-xs);
  }

  .modal-body {
    padding: var(--spacing-lg);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-lg);
  }

  .detail-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-md);
  }

  .detail-label {
    display: block;
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.03em;
    margin-bottom: var(--spacing-xs);
  }

  .payload-section pre {
    background: var(--bg-secondary);
    padding: var(--spacing-md);
    border-radius: var(--radius-sm);
    overflow-x: auto;
    margin: 0;
    font-size: 0.85rem;
  }

  .history-section .approval-history {
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
    padding: var(--spacing-sm);
  }

  .approval-item {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm);
    background: var(--bg-primary);
    border-radius: var(--radius-sm);
    margin-bottom: var(--spacing-xs);
  }

  .approval-item:last-child {
    margin-bottom: 0;
  }

  .action-user {
    font-weight: 500;
  }

  .action-time {
    font-size: 0.85rem;
    color: var(--text-secondary);
  }

  .action-comment {
    width: 100%;
    margin: var(--spacing-xs) 0 0;
    font-size: 0.9rem;
    color: var(--text-secondary);
  }

  .action-section textarea {
    width: 100%;
    padding: var(--spacing-sm);
    border: 1px solid #334155;
    border-radius: var(--radius-sm);
    background: var(--bg-primary);
    color: var(--text-primary);
    resize: vertical;
    font-family: inherit;
  }

  .action-section textarea:focus {
    outline: none;
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
  }

  .action-buttons {
    display: flex;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-sm);
  }

  .requester-name {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    font-weight: 500;
  }

  .badge-info {
    background: rgba(59, 130, 246, 0.15);
    color: #60a5fa;
  }

  /* Diff styles */
  .diff-section {
    margin-top: var(--spacing-sm);
  }

  .diff-list {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .diff-item {
    background: var(--bg-secondary);
    border-radius: var(--radius-sm);
    padding: var(--spacing-md);
  }

  .diff-field {
    display: block;
    font-weight: 600;
    font-size: 0.9rem;
    margin-bottom: var(--spacing-sm);
    color: var(--text-primary);
    text-transform: capitalize;
  }

  .diff-values {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .diff-old, .diff-new {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .diff-label {
    font-size: 0.75rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .diff-old .diff-label {
    color: #ef4444;
  }

  .diff-new .diff-label {
    color: #22c55e;
  }

  .diff-old code {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    color: #fca5a5;
  }

  .diff-new code {
    background: rgba(34, 197, 94, 0.1);
    border: 1px solid rgba(34, 197, 94, 0.2);
    color: #86efac;
  }

  .diff-item code {
    display: block;
    padding: var(--spacing-sm);
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    white-space: pre-wrap;
    word-break: break-word;
    font-family: monospace;
  }

  .no-changes {
    color: var(--text-secondary);
    font-style: italic;
    margin: 0;
  }

  /* Self-approval warning */
  .self-approval-warning {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-md);
    background: rgba(234, 179, 8, 0.1);
    border: 1px solid rgba(234, 179, 8, 0.25);
    border-radius: var(--radius-sm);
    color: #eab308;
    font-size: 0.9rem;
  }

  .self-approval-warning svg {
    flex-shrink: 0;
    color: #eab308;
  }
</style>
