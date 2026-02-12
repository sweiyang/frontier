<script>
  import { registry } from "./componentRegistry";

  export let schema;

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
      <svelte:component
        this={registry[item.type]}
        {...item.props}
      />
    </div>
  {/each}
</div>

<style>
  .grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    grid-auto-rows: 60px;
    gap: 10px;
    padding: 12px;
    background: #f8f9fb;
  }

  .cell {
    background: white;
    padding: 8px;
    border-radius: 6px;
    overflow: auto;
  }
</style>
