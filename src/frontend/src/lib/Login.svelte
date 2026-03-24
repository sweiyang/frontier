<script>
  import { fly, fade } from "svelte/transition";
  import { AlertCircle, Loader2, Lock, User, Eye, EyeOff, Zap, Shield, Globe, Sparkles, ArrowRight } from "lucide-svelte";

  let { appName = "Frontier", onlogin = () => {} } = $props();

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
  .login-container {
    position: relative;
    min-height: 100vh;
    width: 100%;
    background-color: var(--bg-primary);
    overflow: hidden;
  }

  /* Animated gradient orbs */
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
    background: rgba(225, 29, 72, 0.1);
    filter: blur(100px);
    animation: float-rose 8s ease-in-out infinite;
  }

  .orb-orange {
    width: 400px;
    height: 400px;
    bottom: -80px;
    right: -80px;
    background: rgba(234, 88, 12, 0.1);
    filter: blur(120px);
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

  /* Subtle grid pattern overlay */
  .grid-overlay {
    position: absolute;
    inset: 0;
    background-image: radial-gradient(rgba(255, 255, 255, 0.15) 1px, transparent 1px);
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
    padding: 3rem;
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
    background: var(--primary-accent);
    border-radius: var(--radius-xl);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 10px 15px -3px rgba(225, 29, 72, 0.2);
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
    background: rgba(225, 29, 72, 0.1);
    border: 1px solid rgba(225, 29, 72, 0.2);
    color: #fb7185;
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
    color: #ffffff;
  }

  .gradient-text {
    background: linear-gradient(135deg, #fb7185, #fb923c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .brand-tagline {
    font-size: 1.05rem;
    color: var(--text-secondary);
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
    background: rgba(15, 23, 42, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    transition: border-color 0.2s ease, background 0.2s ease;
  }

  .feature-card:hover {
    border-color: rgba(255, 255, 255, 0.12);
    background: rgba(15, 23, 42, 0.7);
  }

  .feature-icon {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-lg);
    background: rgba(225, 29, 72, 0.1);
    color: var(--primary-accent);
  }

  .feature-info h3 {
    font-family: var(--font-display);
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 0.2rem;
  }

  .feature-info p {
    font-size: 0.8rem;
    color: var(--text-secondary);
    line-height: 1.4;
  }

  /* Right form panel */
  .form-panel {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem;
  }

  .login-card {
    width: 100%;
    max-width: 420px;
    background: rgba(15, 23, 42, 0.5);
    backdrop-filter: blur(24px);
    -webkit-backdrop-filter: blur(24px);
    border-radius: var(--radius-3xl);
    border: 1px solid rgba(255, 255, 255, 0.1);
    padding: 2.5rem;
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  }

  .login-header {
    margin-bottom: 2rem;
  }

  .login-header h2 {
    font-family: var(--font-display);
    font-size: 1.75rem;
    font-weight: 700;
    color: #ffffff;
    margin-bottom: 0.35rem;
  }

  .login-header p {
    color: var(--text-secondary);
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
    color: var(--text-secondary);
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
    color: var(--text-muted);
    display: flex;
    align-items: center;
    pointer-events: none;
  }

  .form-group input {
    width: 100%;
    padding: 0.75rem 1rem 0.75rem 2.75rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-strong);
    border-radius: var(--radius-2xl);
    font-size: 0.95rem;
    color: #ffffff;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .form-group input:focus {
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 2px rgba(225, 29, 72, 0.25);
    outline: none;
  }

  .form-group input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .form-group input::placeholder {
    color: var(--text-muted);
  }

  .toggle-password {
    position: absolute;
    right: 0.75rem;
    color: var(--text-muted);
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
    color: var(--text-secondary);
  }

  .login-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.75rem;
    background: var(--primary-accent);
    color: white;
    font-size: 1rem;
    font-weight: 600;
    border: none;
    border-radius: var(--radius-xl);
    cursor: pointer;
    margin-top: 0.5rem;
    box-shadow: 0 10px 15px -3px rgba(225, 29, 72, 0.2);
    transition: background 0.2s ease, box-shadow 0.2s ease, transform 0.12s ease;
  }

  .login-button:hover:not(:disabled) {
    background: var(--primary-accent-hover);
    box-shadow: 0 10px 20px -3px rgba(225, 29, 72, 0.3);
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
    background: rgba(220, 38, 38, 0.1);
    border: 1px solid rgba(220, 38, 38, 0.25);
    border-radius: var(--radius-lg);
    color: #fca5a5;
    font-size: 0.85rem;
  }

  .login-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 2rem;
    padding-top: 1.25rem;
    border-top: 1px solid rgba(255, 255, 255, 0.05);
  }

  .footer-link {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-muted);
    background: none;
    border: none;
    cursor: pointer;
    transition: color 0.15s ease;
  }

  .footer-link:hover {
    color: #fb7185;
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
</style>
