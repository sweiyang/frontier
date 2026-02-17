<script>
  import { onMount } from 'svelte';
  import Renderer from './Renderer.svelte';
  import { schema } from './stores/schemaStore';
  
  async function handleFetchSchema(lastMessage = null, componentId = null) {
    await schema.fetchSchema(lastMessage, componentId);
  }

  onMount(() => {
    handleFetchSchema();
  });
</script>

<div class="container">
  <div class="renderer-wrapper">
    {#if $schema}
      <Renderer schema={$schema} onButtonClick={handleFetchSchema} />
    {:else}
      <div class="empty-state">
        <p>Loading UI schema from API...</p>
      </div>
    {/if}
  </div>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    min-height: 100vh;
  }

  .container {
    max-width: 1400px;
    margin: 0 auto;
    padding: 24px;
    background: transparent;
    border-radius: 0;
    box-shadow: none;
  }

  h1 {
    color: #1a1a2e;
    margin-top: 0;
    margin-bottom: 24px;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }

  .renderer-wrapper {
    border: none;
    border-radius: 16px;
    overflow: hidden;
    background: transparent;
    min-height: 600px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 600px;
    color: #7f8c9a;
    font-size: 16px;
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  }

  .empty-state p {
    font-weight: 500;
  }
</style>
