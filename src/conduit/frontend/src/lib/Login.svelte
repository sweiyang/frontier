<script>
  let { onlogin = () => {} } = $props();

  let username = $state("");
  let password = $state("");
  let error = $state("");
  let loading = $state(false);

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
        // Pass token and username to parent
        onlogin({ detail: { username: data.username, access_token: data.access_token } });
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
  <div class="login-card">
    <div class="login-header">
      <h1>Welcome to Conduit</h1>
      <p>Sign in to continue</p>
    </div>

    <form onsubmit={handleSubmit}>
      {#if error}
        <div class="error-message">
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          {error}
        </div>
      {/if}

      <div class="form-group">
        <label for="username">Username</label>
        <input
          type="text"
          id="username"
          bind:value={username}
          placeholder="Enter your username"
          required
          disabled={loading}
        />
      </div>

      <div class="form-group">
        <label for="password">Password</label>
        <input
          type="password"
          id="password"
          bind:value={password}
          placeholder="Enter your password"
          required
          disabled={loading}
        />
      </div>

      <button type="submit" class="login-button" disabled={loading}>
        {#if loading}
          <span class="spinner"></span>
          Signing in...
        {:else}
          Sign in
        {/if}
      </button>
    </form>

    <div class="login-footer">
      <p>Secured with LDAP authentication</p>
    </div>
  </div>
</div>

<style>
  .login-container {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 100vh;
    width: 100%;
    background-color: var(--bg-primary);
    padding: var(--spacing-lg);
  }

  .login-card {
    width: 100%;
    max-width: 400px;
    background: var(--bg-secondary);
    border-radius: 32px;
    box-shadow: var(--shadow-sm);
    padding: var(--spacing-xl);
    border: 1px solid transparent;
    transition: all 0.2s;
  }

  .login-card:hover,
  .login-card:focus-within {
    box-shadow: var(--shadow-md);
    border-color: var(--border-color);
  }

  .login-header {
    text-align: center;
    margin-bottom: var(--spacing-xl);
  }

  .logo {
    margin-bottom: var(--spacing-md);
  }

  .login-header h1 {
    font-family: var(--font-display);
    font-size: 1.75rem;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--spacing-xs);
  }

  .login-header p {
    color: var(--text-secondary);
    font-size: 0.9rem;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-md);
  }

  .form-group {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .form-group label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .form-group input {
    padding: 0.75rem 1rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    font-size: 1rem;
    background: var(--bg-secondary);
    transition: all 0.2s ease;
  }

  .form-group input:focus {
    border-color: var(--text-secondary);
    box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
    background: var(--bg-primary);
  }

  .form-group input:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .form-group input::placeholder {
    color: var(--text-secondary);
    opacity: 0.7;
  }

  .login-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-sm);
    padding: 0.875rem 1.5rem;
    background-color: black;
    color: white;
    font-size: 1rem;
    font-weight: 600;
    border-radius: var(--radius-full);
    margin-top: var(--spacing-sm);
    transition: opacity 0.2s ease;
  }

  .login-button:hover:not(:disabled) {
    opacity: 0.85;
  }

  .login-button:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  .spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
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
    gap: var(--spacing-sm);
    padding: 0.75rem 1rem;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: var(--radius-md);
    color: #dc2626;
    font-size: 0.875rem;
  }

  .login-footer {
    text-align: center;
    margin-top: var(--spacing-xl);
    padding-top: var(--spacing-md);
    border-top: 1px solid var(--border-color);
  }

  .login-footer p {
    color: var(--text-secondary);
    font-size: 0.75rem;
  }
</style>
