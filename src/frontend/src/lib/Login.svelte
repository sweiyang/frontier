<script>
  import { fly, fade } from "svelte/transition";
  import { AlertCircle, Loader2, Lock, User, Eye, EyeOff, Zap, Shield, Globe, Sparkles, ArrowRight, Sun, Moon } from "lucide-svelte";

  let { appName = "Frontier AI", onlogin = () => {}, currentTheme = "light", ontoggletTheme = () => {} } = $props();

  let username = $state("");
  let password = $state("");
  let error = $state("");
  let loading = $state(false);
  let showPassword = $state(false);
  let mounted = $state(false);

  $effect(() => {
    mounted = true;
  });

  async function handleSubmit(e) {
    e.preventDefault();
    error = "";
    loading = true;

    try {
      const response = await fetch("/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();
      if (response.ok) {
        onlogin({ detail: {
          username: data.username,
          access_token: data.access_token,
          display_name: data.display_name || null
        } });
      } else {
        error = data.detail || "Login failed";
      }
    } catch (err) {
      error = "Connection error. Please try again.";
    } finally {
      loading = false;
    }
  }
</script>

<div class="login-container">
  <!-- Theme toggle -->
  <button class="theme-toggle" onclick={ontoggletTheme} title="Toggle theme">
    {#if currentTheme === 'dark'}
      <Sun size={18} />
    {:else}
      <Moon size={18} />
    {/if}
  </button>

  <!-- Animated gradient orbs -->
  <div class="orb orb-rose"></div>
  <div class="orb orb-orange"></div>
  <div class="grid-overlay"></div>

  <div class="login-grid">
    <!-- Left panel: branding -->
    {#if mounted}
      <div class="branding-panel" in:fly={{ x: -40, duration: 600, delay: 100 }}>
        <div class="branding-content">
          <div class="brand-logo">
            <div class="logo-badge">
              <Sparkles size={28} color="white" />
            </div>
          </div>
          <div class="brand-pill">
            <Sparkles size={12} />
            The Future of Enterprise AI
          </div>
          <h1 class="brand-title">
            A centralized platform<br />
            <span class="gradient-text">for your AI Agents.</span>
          </h1>
          <p class="brand-tagline">Empowering line managers and data scientists alike with intuitive, actionable insights.</p>

          <div class="feature-cards">
            <div class="feature-card" in:fly={{ y: 20, duration: 400, delay: 300 }}>
              <div class="feature-icon">
                <Zap size={20} />
              </div>
              <div class="feature-info">
                <h3>Lightning Fast</h3>
                <p>Stream responses in real-time with multiple AI agent connectors.</p>
              </div>
            </div>

            <div class="feature-card" in:fly={{ y: 20, duration: 400, delay: 450 }}>
              <div class="feature-icon">
                <Shield size={20} />
              </div>
              <div class="feature-info">
                <h3>Enterprise Ready</h3>
                <p>RBAC, LDAP integration, and approval workflows built in.</p>
              </div>
            </div>

            <div class="feature-card" in:fly={{ y: 20, duration: 400, delay: 600 }}>
              <div class="feature-icon">
                <Globe size={20} />
              </div>
              <div class="feature-info">
                <h3>Multi-Project</h3>
                <p>Isolated environments with custom dashboards and site builder.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    {/if}

    <!-- Right panel: login form -->
    {#if mounted}
      <div class="form-panel" in:fly={{ y: 30, duration: 500, delay: 200 }}>
        <div class="login-card">
          <div class="login-header mobile-only">
            <div class="logo-badge logo-badge-sm">
              <Sparkles size={24} color="white" />
            </div>
            <h2>{appName}</h2>
          </div>
          <div class="login-header">
            <h2>Sign In</h2>
            <p>Enter your credentials to access the platform.</p>
          </div>

          <form onsubmit={handleSubmit}>
            {#if error}
              <div class="error-message" in:fly={{ y: -8, duration: 200 }}>
                <AlertCircle size={16} />
                <span>{error}</span>
              </div>
            {/if}

            <div class="form-group">
              <label for="username">Username</label>
              <div class="input-wrapper">
                <span class="input-icon">
                  <User size={18} />
                </span>
                <input
                  type="text"
                  id="username"
                  bind:value={username}
                  placeholder="Enter your username"
                  required
                  disabled={loading}
                />
              </div>
            </div>

            <div class="form-group">
              <label for="password">Password</label>
              <div class="input-wrapper">
                <span class="input-icon">
                  <Lock size={18} />
                </span>
                <input
                  type={showPassword ? "text" : "password"}
                  id="password"
                  bind:value={password}
                  placeholder="Enter your password"
                  required
                  disabled={loading}
                />
                <button
                  type="button"
                  class="toggle-password"
                  onclick={() => (showPassword = !showPassword)}
                  tabindex="-1"
                >
                  {#if showPassword}
                    <EyeOff size={18} />
                  {:else}
                    <Eye size={18} />
                  {/if}
                </button>
              </div>
            </div>

            <button type="submit" class="login-button" disabled={loading}>
              {#if loading}
                <span class="spinner-icon">
                  <Loader2 size={20} />
                </span>
                Signing in...
              {:else}
                Launch Platform
                <ArrowRight size={18} />
              {/if}
            </button>
          </form>

          <div class="login-footer">
            <button type="button" class="footer-link">Forgot password?</button>
            <button type="button" class="footer-link">Contact support</button>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>

<style>
  .theme-toggle {
    position: absolute;
    top: 1.25rem;
    right: 1.25rem;
    z-index: 10;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 50%;
    border: 1px solid rgba(0, 0, 0, 0.08);
    background: rgba(255, 255, 255, 0.7);
    color: #6b6b6b;
    cursor: pointer;
    transition: background 0.2s ease, color 0.2s ease, border-color 0.2s ease;
    backdrop-filter: blur(8px);
  }

  :global([data-theme="dark"]) .theme-toggle {
    border-color: rgba(255, 255, 255, 0.1);
    background: rgba(255, 255, 255, 0.08);
    color: #94a3b8;
  }

  .theme-toggle:hover {
    background: rgba(0, 0, 0, 0.06);
    color: #1a1a1a;
  }

  :global([data-theme="dark"]) .theme-toggle:hover {
    background: rgba(255, 255, 255, 0.15);
    color: #e2e8f0;
  }

  .login-container {
    position: relative;
    min-height: 100vh;
    width: 100%;
    background-color: #F6F4F0;
    overflow: hidden;
  }

  /* Subtle radial gradient accents for depth */
  .orb {
    position: absolute;
    border-radius: 50%;
    pointer-events: none;
  }

  .orb-rose {
    width: 600px;
    height: 600px;
    top: -100px;
    left: -100px;
    background: radial-gradient(circle, rgba(232, 68, 58, 0.08) 0%, transparent 70%);
    filter: blur(60px);
    animation: float-rose 8s ease-in-out infinite;
  }

  .orb-orange {
    width: 400px;
    height: 400px;
    bottom: -80px;
    right: -80px;
    background: radial-gradient(circle, rgba(232, 68, 58, 0.06) 0%, transparent 70%);
    filter: blur(80px);
    animation: float-orange 10s ease-in-out infinite;
  }

  @keyframes float-rose {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(40px, 30px); }
  }

  @keyframes float-orange {
    0%, 100% { transform: translate(0, 0); }
    50% { transform: translate(-30px, -40px); }
  }

  /* Subtle dot pattern overlay */
  .grid-overlay {
    position: absolute;
    inset: 0;
    background-image: radial-gradient(rgba(0, 0, 0, 0.04) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
  }

  /* 2-column grid layout */
  .login-grid {
    position: relative;
    z-index: 1;
    display: grid;
    grid-template-columns: 1fr 1fr;
    min-height: 100vh;
    width: 100%;
  }

  /* Left branding panel */
  .branding-panel {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem 1.5rem 2rem 3rem;
  }

  .branding-content {
    max-width: 440px;
  }

  .brand-logo {
    margin-bottom: 1.5rem;
  }

  .logo-badge {
    width: 56px;
    height: 56px;
    background: #E8443A;
    border-radius: var(--radius-xl);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 10px 25px -5px rgba(232, 68, 58, 0.3);
  }

  .logo-badge-sm {
    width: 48px;
    height: 48px;
    margin-bottom: 1.25rem;
  }

  .brand-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.25rem 0.75rem;
    border-radius: var(--radius-full);
    background: rgba(232, 68, 58, 0.08);
    border: 1px solid rgba(232, 68, 58, 0.15);
    color: #E8443A;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 1.25rem;
  }

  .brand-title {
    font-family: var(--font-display);
    font-size: 2.75rem;
    font-weight: 700;
    margin-bottom: 0.75rem;
    line-height: 1.1;
    color: #1a1a1a;
  }

  .gradient-text {
    background: linear-gradient(135deg, #E8443A, #f97316);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .brand-tagline {
    font-size: 1.05rem;
    color: #6b6b6b;
    line-height: 1.6;
    margin-bottom: 2.5rem;
  }

  .feature-cards {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .feature-card {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem;
    border-radius: var(--radius-xl);
    background: rgba(255, 255, 255, 0.6);
    border: 1px solid rgba(0, 0, 0, 0.06);
    transition: border-color 0.2s ease, background 0.2s ease, transform 0.2s ease;
  }

  .feature-card:hover {
    border-color: rgba(232, 68, 58, 0.25);
    background: rgba(255, 255, 255, 0.9);
    transform: translateX(4px);
    box-shadow: -3px 0 0 0 #E8443A, 0 4px 12px rgba(0, 0, 0, 0.04);
  }

  .feature-icon {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-lg);
    background: rgba(232, 68, 58, 0.08);
    color: #E8443A;
  }

  .feature-info h3 {
    font-family: var(--font-display);
    font-size: 0.9rem;
    font-weight: 600;
    color: #1a1a1a;
    margin-bottom: 0.2rem;
  }

  .feature-info p {
    font-size: 0.8rem;
    color: #6b6b6b;
    line-height: 1.4;
  }

  /* Right form panel */
  .form-panel {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem 3rem 2rem 1.5rem;
  }

  .login-card {
    width: 100%;
    max-width: 420px;
    background: #ffffff;
    border-radius: var(--radius-3xl);
    border: 1px solid rgba(0, 0, 0, 0.06);
    padding: 2.5rem;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04);
    transition: box-shadow 0.3s ease;
  }

  .login-card:hover {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.08), 0 2px 4px rgba(0, 0, 0, 0.04);
  }

  .login-header {
    margin-bottom: 2rem;
  }

  .login-header h2 {
    font-family: var(--font-display);
    font-size: 1.75rem;
    font-weight: 700;
    color: #1a1a1a;
    margin-bottom: 0.35rem;
  }

  .login-header p {
    color: #6b6b6b;
    font-size: 0.9rem;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }

  .form-group label {
    font-size: 0.8rem;
    font-weight: 500;
    color: #6b6b6b;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .input-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .input-icon {
    position: absolute;
    left: 1rem;
    color: #9b9b9b;
    display: flex;
    align-items: center;
    pointer-events: none;
  }

  .form-group input {
    width: 100%;
    padding: 0.75rem 1rem 0.75rem 2.75rem;
    background: #F6F4F0;
    border: 1px solid #e0ddd8;
    border-radius: var(--radius-2xl);
    font-size: 0.95rem;
    font-family: var(--font-sans);
    color: #1a1a1a;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .form-group input:focus {
    border-color: #E8443A;
    box-shadow: 0 0 0 3px rgba(232, 68, 58, 0.1);
    outline: none;
  }

  .form-group input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .form-group input::placeholder {
    color: #9b9b9b;
  }

  .toggle-password {
    position: absolute;
    right: 0.75rem;
    color: #9b9b9b;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.25rem;
    border-radius: var(--radius-sm);
    transition: color 0.15s ease;
    cursor: pointer;
    background: none;
    border: none;
  }

  .toggle-password:hover {
    color: #6b6b6b;
  }

  .login-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.75rem;
    background: #E8443A;
    color: white;
    font-size: 1rem;
    font-family: var(--font-display);
    font-weight: 600;
    border: none;
    border-radius: var(--radius-xl);
    cursor: pointer;
    margin-top: 0.5rem;
    box-shadow: 0 10px 25px -5px rgba(232, 68, 58, 0.25);
    transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.12s ease;
  }

  .login-button:hover:not(:disabled) {
    background: #d63a31;
    box-shadow: 0 10px 30px -5px rgba(232, 68, 58, 0.35);
    transform: translateY(-1px);
  }

  .login-button:active:not(:disabled) {
    transform: translateY(0);
  }

  .login-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .spinner-icon {
    display: flex;
    align-items: center;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to {
      transform: rotate(360deg);
    }
  }

  .error-message {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.75rem 1rem;
    background: #fef2f2;
    border: 1px solid rgba(220, 38, 38, 0.2);
    border-radius: var(--radius-lg);
    color: #dc2626;
    font-size: 0.85rem;
  }

  .login-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 2rem;
    padding-top: 1.25rem;
    border-top: 1px solid rgba(0, 0, 0, 0.06);
  }

  .footer-link {
    font-size: 0.75rem;
    font-weight: 500;
    color: #9b9b9b;
    background: none;
    border: none;
    cursor: pointer;
    transition: color 0.15s ease;
  }

  .footer-link:hover {
    color: #E8443A;
  }

  .mobile-only {
    display: none;
  }

  @media (max-width: 900px) {
    .mobile-only {
      display: flex;
      flex-direction: column;
      align-items: center;
    }
  }

  /* Responsive: hide left panel on mobile */
  @media (max-width: 900px) {
    .login-grid {
      grid-template-columns: 1fr;
    }

    .branding-panel {
      display: none;
    }

    .form-panel {
      padding: 1.5rem;
    }

    .login-card {
      max-width: 400px;
    }
  }

  /* ── Dark mode overrides ── */
  :global([data-theme="dark"]) .login-container {
    background-color: #020617;
  }

  :global([data-theme="dark"]) .orb-rose {
    background: radial-gradient(circle, rgba(232, 68, 58, 0.12) 0%, transparent 70%);
  }

  :global([data-theme="dark"]) .orb-orange {
    background: radial-gradient(circle, rgba(232, 68, 58, 0.08) 0%, transparent 70%);
  }

  :global([data-theme="dark"]) .grid-overlay {
    background-image: radial-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px);
  }

  :global([data-theme="dark"]) .brand-pill {
    background: rgba(232, 68, 58, 0.12);
    border-color: rgba(232, 68, 58, 0.2);
  }

  :global([data-theme="dark"]) .brand-title {
    color: #e2e8f0;
  }

  :global([data-theme="dark"]) .brand-tagline {
    color: #94a3b8;
  }

  :global([data-theme="dark"]) .feature-card {
    background: rgba(15, 23, 42, 0.6);
    border-color: rgba(255, 255, 255, 0.06);
  }

  :global([data-theme="dark"]) .feature-card:hover {
    background: rgba(15, 23, 42, 0.8);
    border-color: rgba(232, 68, 58, 0.3);
    box-shadow: -3px 0 0 0 #E8443A, 0 4px 12px rgba(0, 0, 0, 0.2);
  }

  :global([data-theme="dark"]) .feature-icon {
    background: rgba(232, 68, 58, 0.12);
  }

  :global([data-theme="dark"]) .feature-info h3 {
    color: #e2e8f0;
  }

  :global([data-theme="dark"]) .feature-info p {
    color: #94a3b8;
  }

  :global([data-theme="dark"]) .login-card {
    background: rgba(15, 23, 42, 0.6);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-color: rgba(255, 255, 255, 0.08);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  }

  :global([data-theme="dark"]) .login-card:hover {
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.6);
  }

  :global([data-theme="dark"]) .login-header h2 {
    color: #e2e8f0;
  }

  :global([data-theme="dark"]) .login-header p {
    color: #94a3b8;
  }

  :global([data-theme="dark"]) .form-group label {
    color: #94a3b8;
  }

  :global([data-theme="dark"]) .input-icon {
    color: #64748b;
  }

  :global([data-theme="dark"]) .form-group input {
    background: #0f172a;
    border-color: #334155;
    color: #e2e8f0;
  }

  :global([data-theme="dark"]) .form-group input::placeholder {
    color: #64748b;
  }

  :global([data-theme="dark"]) .form-group input:focus {
    border-color: #E8443A;
    box-shadow: 0 0 0 3px rgba(232, 68, 58, 0.2);
  }

  :global([data-theme="dark"]) .toggle-password {
    color: #64748b;
  }

  :global([data-theme="dark"]) .toggle-password:hover {
    color: #94a3b8;
  }

  :global([data-theme="dark"]) .error-message {
    background: rgba(220, 38, 38, 0.1);
    border-color: rgba(220, 38, 38, 0.25);
    color: #fca5a5;
  }

  :global([data-theme="dark"]) .login-footer {
    border-top-color: rgba(255, 255, 255, 0.06);
  }

  :global([data-theme="dark"]) .footer-link {
    color: #64748b;
  }

  :global([data-theme="dark"]) .footer-link:hover {
    color: #E8443A;
  }
</style>
