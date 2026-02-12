<script>
  export let columns = [];
  export let rows = [];

  function getCellValue(row, column) {
    if (typeof column === "string") {
      return row[column];
    }
    return row[column.key];
  }
</script>

<div class="table-container">
  <table class="table">
    <thead>
      <tr>
        {#each columns as col}
          <th>{typeof col === "string" ? col : col.label}</th>
        {/each}
      </tr>
    </thead>
    <tbody>
      {#each rows as row (row)}
        <tr>
          {#each columns as col}
            <td>{getCellValue(row, col)}</td>
          {/each}
        </tr>
      {/each}
      {#if rows.length === 0}
        <tr>
          <td colspan={columns.length} class="empty">No data available</td>
        </tr>
      {/if}
    </tbody>
  </table>
</div>

<style>
  .table-container {
    width: 100%;
    height: 100%;
    overflow: auto;
    border: 1px solid #ddd;
    border-radius: 6px;
    background: white;
  }

  .table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }

  thead {
    position: sticky;
    top: 0;
    background: #f5f5f5;
  }

  th {
    padding: 12px;
    text-align: left;
    font-weight: 600;
    color: #333;
    border-bottom: 2px solid #ddd;
    white-space: nowrap;
  }

  td {
    padding: 10px 12px;
    border-bottom: 1px solid #eee;
    color: #666;
  }

  tbody tr:hover {
    background: #f9f9f9;
  }

  tbody tr:last-child td {
    border-bottom: none;
  }

  .empty {
    text-align: center;
    color: #999;
    font-style: italic;
    padding: 20px !important;
  }
</style>
