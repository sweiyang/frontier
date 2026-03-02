<script>
  import { registry } from "./componentRegistry";

  export let schema;
  export let onButtonClick;

  function cellStyle(item) {
    return `
      grid-column: ${item.x + 1} / span ${item.w};
      grid-row: ${item.y + 1} / span ${item.h};
    `;
  }
</script>

<div class="grid">
  {#each schema.components as item (item.id)}
    <div class="cell" style={cellStyle(item)}>
      {#if item.type === 'ChatWindow'}
        <svelte:component
          this={registry[item.type]}
          {...item.props}
          onClick={(msg) => onButtonClick(msg, item.id)}
        />
      {:else if item.type === 'Button'}
        <svelte:component
          this={registry[item.type]}
          {...item.props}
          onClick={() => onButtonClick()}
        />
      {:else if item.type === 'PopupBox'}
        <svelte:component
          this={registry[item.type]}
          {...item.props}
          {onButtonClick}
        />
      {:else}
        <svelte:component
          this={registry[item.type]}
          {...item.props}
        />
      {/if}
    </div>
  {/each}
</div>

<style>
  .grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    grid-auto-rows: 60px;
    gap: 16px;
    padding: 20px;
    min-height: 100%;
  }

  .cell {
    background: transparent;
    padding: 12px;
    border-radius: 12px;
    overflow: visible;
    display: flex;
    box-shadow: none;
    transition: all 0.3s ease;
  }

  .cell:hover {
    box-shadow: none;
  }
</style>
