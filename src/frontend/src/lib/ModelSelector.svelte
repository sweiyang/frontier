<script lang="ts">
  import { onMount } from "svelte";
  import { authFetch } from "./utils.js";
  import { ChevronDown, Loader2 } from "lucide-svelte";

  type Agent = {
    id: number;
    name: string;
    endpoint: string;
    connection_type: string;
    is_default?: boolean;
    is_artefact?: boolean;
    extras?: Record<string, unknown> | null;
  };

  type ModelSelectorSelectEvent = {
    detail: {
      agent: Agent;
      model: string; // agent name (used as ChatRequest.model, deprecated)
      agent_id: number | null; // agent_id (optional)
    };
  };

  const props = $props<{
    project: string | null;
    preSelectedAgentId?: number | null;
    onselect?: (event: ModelSelectorSelectEvent) => void;
  }>();

  const project = $derived(props.project);
  const preSelectedAgentId = $derived(props.preSelectedAgentId ?? null);
  const onselect = $derived(props.onselect ?? (() => {}));

  let selectedModel = $state("Select an agent");
  let isOpen = $state(false);
  let isLoading = $state(false);
  let allAgents = $state<Agent[]>([]);
  let agents = $state<Agent[]>([]);
  let lastProject: string | null = null;

  async function loadAgents() {
    if (!project) {
      agents = [];
      selectedModel = "Select an agent";
      return;
    }

    isLoading = true;
    try {
      const response = await authFetch(`/projects/${project}/agents`);
      if (response.ok) {
        const data = await response.json();
        allAgents = data.agents || [];
        // Show all agents in the dropdown
        agents = allAgents;

        // If a pre-selected agent ID is provided, find it in the full list
        let selected: Agent | undefined;
        if (preSelectedAgentId) {
          selected = allAgents.find((a) => a.id === preSelectedAgentId);
        }
        if (!selected) {
          // Select default agent; otherwise first in dropdown list
          const defaultAgent = agents.find((a) => a.is_default);
          selected = defaultAgent || agents[0];
        }
        if (selected) {
          selectedModel = selected.name;
          onselect({
            detail: {
              agent: selected,
              model: selected.name,
              agent_id: selected.id
            }
          });
        } else {
          selectedModel = "No agents";
        }
      } else {
        allAgents = [];
        agents = [];
        selectedModel = "No agents";
      }
    } catch (e) {
      console.error("Failed to load agents:", e);
      allAgents = [];
      agents = [];
      selectedModel = "No agents";
    } finally {
      isLoading = false;
    }
  }

  function toggleOpen() {
    isOpen = !isOpen;
  }

  function selectAgent(agent: Agent) {
    selectedModel = agent.name;
    isOpen = false;
    onselect({ 
      detail: { 
        agent, 
        model: agent.name,
        agent_id: agent.id
      } 
    });
  }

  onMount(() => {
    loadAgents();

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement | null;
      if (!target?.closest(".model-selector-wrapper")) {
        isOpen = false;
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  });

  // React to project changes
  $effect(() => {
    if (project !== lastProject) {
      lastProject = project;
      loadAgents();
    }
  });
</script>

<div class="model-selector-wrapper">
  <button
    type="button"
    class="model-selector"
    on:click={toggleOpen}
    aria-haspopup="listbox"
    aria-expanded={isOpen}
    title={project ? "Select agent" : "No project selected"}
  >
    <span class="model-name">{selectedModel}</span>
    {#if isLoading}
      <span class="chevron-loading"><Loader2 size={16} class="spin" /></span>
    {:else}
      <ChevronDown size={16} class="chevron-icon" />
    {/if}
  </button>

  {#if isOpen}
    <div class="dropdown" role="listbox" aria-label="Available agents">
      {#if !project}
        <div class="dropdown-empty">No project selected</div>
      {:else if agents.length === 0}
        <div class="dropdown-empty">No agents configured</div>
      {:else}
        {#each agents as agent}
          <button
            type="button"
            class="dropdown-item"
            class:active={agent.name === selectedModel}
            on:click={() => selectAgent(agent)}
          >
            <span class="agent-name">{agent.name}</span>
            <span class="agent-meta">
              {#if agent.is_default}
                <span class="pill pill-default">Default</span>
              {/if}
              <span class="pill pill-type">{agent.connection_type}</span>
            </span>
          </button>
        {/each}
      {/if}
    </div>
  {/if}
</div>

<style>
  .model-selector-wrapper {
    position: relative;
    display: inline-block;
    z-index: 20;
    pointer-events: auto;
  }

  .model-selector {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.5rem;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 500;
    font-size: 0.95rem;
    color: var(--text-primary);
    transition: background 0.12s ease;
    background: transparent;
    border: none;
    letter-spacing: -0.01em;
  }

  .model-selector:hover {
    background: rgba(255, 255, 255, 0.06);
  }

  .model-name {
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chevron-loading {
    color: var(--text-muted);
    display: flex;
    align-items: center;
  }

  :global(.chevron-icon) {
    color: var(--text-muted);
    flex-shrink: 0;
  }

  :global(.spin) {
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    min-width: 240px;
    max-width: 360px;
    background-color: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-2xl);
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    z-index: 50;
    padding: 0.25rem;
  }

  .dropdown-empty {
    padding: 0.6rem 0.75rem;
    color: var(--text-muted);
    font-size: 0.85rem;
  }

  .dropdown-item {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    text-align: left;
    color: var(--text-primary);
    transition: background 0.12s ease;
    border: none;
    background: transparent;
    cursor: pointer;
    border-radius: var(--radius-xl);
    font-size: 0.875rem;
  }

  .dropdown-item:hover {
    background: var(--bg-hover);
  }

  .dropdown-item.active {
    background: var(--accent-glow);
    font-weight: 500;
  }

  .agent-name {
    font-weight: 400;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .dropdown-item.active .agent-name {
    font-weight: 500;
  }

  .agent-meta {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    flex-shrink: 0;
  }

  .pill {
    display: inline-flex;
    align-items: center;
    padding: 2px 7px;
    border-radius: var(--radius-sm);
    font-size: 0.65rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .pill-default {
    background-color: var(--accent-glow);
    color: var(--primary-accent);
  }

  .pill-type {
    background-color: rgba(255, 255, 255, 0.06);
    color: var(--text-muted);
  }
</style>
