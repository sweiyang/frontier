<script>
  /**
   * SplashScreen component - displays logo and configurable text for initial loading.
   * @prop {string} logoSrc - Path to the logo image
   * @prop {string} text - Text to display on splash screen (from environment variable)
   * @prop {boolean} fadeOut - Whether the splash screen should fade out
   */
  let { logoSrc = "/ds_ui.svg", text = "Welcome", fadeOut = false } = $props();
</script>

<div class="splash-screen" class:fade-out={fadeOut}>
  <div class="splash-content">
    <div class="logo-container">
      <img src={logoSrc} alt="Logo" class="logo" />
    </div>
    <p class="splash-text">{text}</p>
    <div class="loading-dots">
      <span class="dot"></span>
      <span class="dot"></span>
      <span class="dot"></span>
    </div>
  </div>
</div>

<style>
  .splash-screen {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary, #1a1a2e) 100%);
    z-index: 9999;
    opacity: 1;
    transition: opacity 0.5s ease-out;
  }

  .splash-screen.fade-out {
    opacity: 0;
    pointer-events: none;
  }

  .splash-content {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1.5rem;
    animation: slideUp 0.6s ease-out;
  }

  @keyframes slideUp {
    from {
      opacity: 0;
      transform: translateY(20px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .logo-container {
    width: 500px;
    height: 500px;
    display: flex;
    align-items: center;
    justify-content: center;
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% {
      transform: scale(1);
    }
    50% {
      transform: scale(1.05);
    }
  }

  .logo {
    width: 100%;
    height: 100%;
    object-fit: contain;
  }

  .splash-text {
    font-size: 1.25rem;
    font-weight: 500;
    color: var(--text-primary);
    text-align: center;
    margin: 0;
    max-width: 80%;
    line-height: 1.5;
  }

  .loading-dots {
    display: flex;
    gap: 0.5rem;
    margin-top: 0.5rem;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--text-secondary, #888);
    animation: bounce 1.4s ease-in-out infinite;
  }

  .dot:nth-child(1) {
    animation-delay: 0s;
  }

  .dot:nth-child(2) {
    animation-delay: 0.2s;
  }

  .dot:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes bounce {
    0%, 80%, 100% {
      transform: translateY(0);
      opacity: 0.5;
    }
    40% {
      transform: translateY(-8px);
      opacity: 1;
    }
  }
</style>
