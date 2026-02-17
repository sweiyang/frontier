<script>
  export let label;
  export let onClick;

  function handleClick() {
    if (onClick) {
      onClick();
    }
  }
</script>

<button on:click={handleClick}>{label}</button>

<style>
  button {
    padding: 10px 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-size: 14px;
    font-weight: 600;
    transition: all 0.3s ease;
    width: 100%;
    height: 100%;
    box-shadow: 0 4px 15px rgba(201, 205, 212, 0.4);
  }

  button:hover {
    background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    box-shadow: 0 6px 20px rgba(201, 205, 212, 0.6);
    transform: translateY(-2px);
  }

  button:active {
    transform: translateY(0);
    box-shadow: 0 2px 10px rgba(102, 126, 234, 0.4);
  }
</style>
