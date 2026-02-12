<script>
  import { onMount } from 'svelte';
  import Renderer from './Renderer.svelte';
  
  let schema = null;

  onMount(async () => {
    // Load schema from fixed path
    try {
      const response = await fetch('/sample-schema.json');
      if (!response.ok) throw new Error('Failed to load schema');
      schema = await response.json();
    } catch (e) {
      console.error("Failed to load sample-schema.json", e);
    }
  });
</script>

<div class="container">
  <h1>Internal POC UI Renderer</h1>

  <div class="renderer-wrapper">
    {#if schema}
      <Renderer {schema} />
    {:else}
      <div class="empty-state">
        <p>Loading UI from sample-schema.json...</p>
      </div>
    {/if}
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
  }

  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  h1 {
    color: #333;
    margin-top: 0;
    margin-bottom: 20px;
  }

  .renderer-wrapper {
    border: 1px solid #ddd;
    border-radius: 4px;
    overflow: hidden;
    background: #f8f9fb;
    min-height: 600px;
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 600px;
    color: #999;
    font-size: 16px;
  }
</style>
