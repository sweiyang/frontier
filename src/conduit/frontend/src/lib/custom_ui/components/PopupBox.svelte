<script>
  import Renderer from "../Renderer.svelte";

  export let title = "Popup";
  export let content = "";
  export let components = [];
  export let isOpen = false;
  export let onClose;
  export let onButtonClick;

  function handleClose() {
    if (onClose) {
      onClose();
    }
  }

  $: schema = { components: components || [] };
</script>

{#if isOpen}
  <div class="popup-box">
    <div class="popup-header">
      <h2>{title}</h2>
      <button class="close-btn" on:click={handleClose}>×</button>
    </div>
    <div class="popup-content">
      {#if components && components.length > 0}
        <Renderer {schema} {onButtonClick} />
      {:else if typeof content === "string"}
        <p>{content}</p>
      {:else}
        <slot />
      {/if}
    </div>
  </div>
{/if}

<style>
  .popup-box {
    background: white;
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
    z-index: 9999;
  }

  .popup-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px 12px 0 0;
    color: white;
    flex-shrink: 0;
  }

  .popup-header h2 {
    margin: 0;
    font-size: 18px;
    font-weight: 700;
  }

  .close-btn {
    background: none;
    border: none;
    color: white;
    font-size: 32px;
    cursor: pointer;
    padding: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: transform 0.2s ease;
    line-height: 1;
  }

  .close-btn:hover {
    transform: scale(1.2);
  }

  .popup-content {
    color: #4a5568;
    font-size: 14px;
    line-height: 1.6;
    overflow-y: auto;
    flex: 1;
    padding: 0;
  }

  .popup-content :global(.grid) {
    padding: 0;
    background: transparent;
    gap: 8px;
    min-height: auto;
  }

  .popup-content p {
    margin: 0;
    padding: 20px;
  }
</style>
