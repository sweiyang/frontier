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
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    padding: 16px;
    border-radius: 12px;
    height: 100%;
    width: 100%;
    display: flex;
    flex-direction: column;
    justify-content: center;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.1);
    border: none;
    transition: all 0.3s ease;
  }

  .card:hover {
    box-shadow: 0 12px 24px rgba(0, 0, 0, 0.15);
    transform: translateY(-2px);
  }

  .label {
    color: #7f8c9a;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 8px;
    font-weight: 600;
  }

  .value {
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
</style>
