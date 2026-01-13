<script lang="ts">
  import { onMount } from "svelte";
  import { authFetch } from "./auth.js";

  type Agent = {
    id: number;
    name: string;
    endpoint: string;
    connection_type: string;
    is_default?: boolean;
    extras?: Record<string, unknown> | null;
  };

  type ModelSelectorSelectEvent = {
    detail: {
      agent: Agent;
      model: string; // agent name (used as ChatRequest.model)
    };
  };

  const props = $props<{
    project: string | null;
    onselect?: (event: ModelSelectorSelectEvent) => void;
  }>();

  const project = $derived(props.project);
  const onselect = $derived(props.onselect ?? (() => {}));

  let selectedModel = $state("Select an agent");
  let isOpen = $state(false);
  let isLoading = $state(false);
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
        agents = data.agents || [];

        // Select default agent; otherwise first in list
        const defaultAgent = agents.find((a) => a.is_default);
        const selected = defaultAgent || agents[0];
        if (selected) {
          selectedModel = selected.name;
          onselect({ detail: { agent: selected, model: selected.name } });
        } else {
          selectedModel = "No agents";
        }
      } else {
        agents = [];
        selectedModel = "No agents";
      }
    } catch (e) {
      console.error("Failed to load agents:", e);
      agents = [];
      selectedModel = "No agents";
    } finally {
      isLoading = false;
    }
  }

  function toggleOpen() {
    if (!project) return;
    isOpen = !isOpen;
  }

  function selectAgent(agent: Agent) {
    selectedModel = agent.name;
    isOpen = false;
    onselect({ detail: { agent, model: agent.name } });
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
    <span class="chevron">{isLoading ? "…" : "⌄"}</span>
  </button>

  {#if isOpen}
    <div class="dropdown" role="listbox" aria-label="Available agents">
      {#if agents.length === 0}
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
  }

  .model-selector {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-md);
    cursor: pointer;
    font-weight: 500;
    color: var(--text-primary);
    transition: background 0.2s;
    background: transparent;
  }

  .model-selector:hover {
    background-color: var(--bg-secondary);
  }

  .model-name {
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .chevron {
    color: var(--text-secondary);
    font-size: 0.8rem;
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    min-width: 280px;
    max-width: 420px;
    background-color: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    box-shadow: var(--shadow-lg);
    overflow: hidden;
    z-index: 50;
  }

  .dropdown-empty {
    padding: var(--spacing-md);
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  .dropdown-item {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: var(--spacing-md);
    padding: var(--spacing-sm) var(--spacing-md);
    text-align: left;
    color: var(--text-primary);
    transition: background 0.15s ease;
  }

  .dropdown-item:hover,
  .dropdown-item.active {
    background-color: var(--bg-secondary);
  }

  .agent-name {
    font-weight: 500;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .agent-meta {
    display: inline-flex;
    align-items: center;
    gap: var(--spacing-xs);
    flex-shrink: 0;
  }

  .pill {
    display: inline-flex;
    align-items: center;
    padding: 2px 8px;
    border-radius: var(--radius-full);
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
  }

  .pill-default {
    background-color: rgba(245, 158, 11, 0.15);
    color: var(--primary-accent);
  }

  .pill-type {
    background-color: rgba(0, 0, 0, 0.06);
    color: var(--text-secondary);
  }
</style>
