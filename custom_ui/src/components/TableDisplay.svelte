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
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
  }

  .table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }

  thead {
    position: sticky;
    top: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }

  th {
    padding: 14px 16px;
    text-align: left;
    font-weight: 700;
    color: white;
    border-bottom: none;
    white-space: nowrap;
    font-size: 13px;
    letter-spacing: 0.5px;
  }

  td {
    padding: 12px 16px;
    border-bottom: 1px solid #000000;
    border-right: 1px solid #000000;
    color: #4a5568;
    font-size: 14px;
  }

  td:first-child {
    border-left: none;
  }

  td:last-child {
    border-right: none;
  }

  tbody tr {
    transition: all 0.2s ease;
  }

  tbody tr:hover {
    background: #f8f9fc;
    box-shadow: inset 0 0 8px rgba(201, 205, 212, 0.05);
  }

  tbody tr:last-child td {
    border-bottom: 1px solid #000000;
  }

  .empty {
    text-align: center;
    color: #a0aec0;
    font-style: italic;
    padding: 24px !important;
    font-weight: 500;
  }
</style>
