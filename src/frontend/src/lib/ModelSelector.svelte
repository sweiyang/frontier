<script lang="ts">
  import { onMount } from "svelte";
  import { authFetch } from "./utils.js";

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
        // Filter out artefact agents from the dropdown
        agents = allAgents.filter((a) => !a.is_artefact);

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
      <span class="chevron">…</span>
    {:else}
      <svg class="chevron-icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="6 9 12 15 18 9"></polyline>
      </svg>
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
    background: rgba(0, 0, 0, 0.04);
  }

  .model-name {
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chevron {
    color: var(--text-secondary, #888);
    font-size: 0.8rem;
  }

  .chevron-icon {
    color: var(--text-secondary, #888);
    flex-shrink: 0;
    margin-top: 1px;
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 4px);
    left: 0;
    min-width: 240px;
    max-width: 360px;
    background-color: var(--bg-primary, #fff);
    border: 1px solid var(--border-color, #e0e0e0);
    border-radius: 10px;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08), 0 1px 3px rgba(0, 0, 0, 0.04);
    overflow: hidden;
    z-index: 50;
    padding: 0.25rem;
  }

  .dropdown-empty {
    padding: 0.6rem 0.75rem;
    color: var(--text-secondary, #888);
    font-size: 0.85rem;
  }

  .dropdown-item {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
    padding: 0.4rem 0.6rem;
    text-align: left;
    color: var(--text-primary);
    transition: background 0.12s ease;
    border: none;
    background: transparent;
    cursor: pointer;
    border-radius: 7px;
    font-size: 0.875rem;
  }

  .dropdown-item:hover {
    background: rgba(0, 0, 0, 0.04);
  }

  .dropdown-item.active {
    background: rgba(0, 0, 0, 0.06);
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
    padding: 1px 6px;
    border-radius: 4px;
    font-size: 0.65rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  .pill-default {
    background-color: rgba(245, 158, 11, 0.12);
    color: var(--primary-accent, #d97706);
  }

  .pill-type {
    background-color: rgba(0, 0, 0, 0.05);
    color: var(--text-secondary, #888);
  }
</style>
