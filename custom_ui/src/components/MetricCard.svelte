<script>
  export let label;
  export let value;
</script>

<div class="card">
  <div class="label">{label}</div>
  <div class="value">{value}</div>
</div>

<style>
  .card {
    border: 1px solid #ddd;
    padding: 12px;
    border-radius: 6px;
    height: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .label {
    color: #666;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
  }

  .value {
    font-size: 24px;
    font-weight: bold;
    color: #333;
  }
</style>
