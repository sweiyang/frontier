<script>
  export let label;
</script>

<button>{label}</button>

<style>
  button {
    padding: 8px 16px;
    background: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: background 0.2s;
  }

  button:hover {
    background: #1976D2;
  }

  button:active {
    background: #1565C0;
  }
</style>
