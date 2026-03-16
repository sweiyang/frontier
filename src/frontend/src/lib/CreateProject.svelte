<script>
    import { authPost } from "./utils.js";

    let { appName = "Frontier", oncreate = () => {}, oncancel = () => {} } = $props();

    let projectName = $state("");
    let error = $state("");
    let loading = $state(false);

    async function handleSubmit(e) {
        e.preventDefault();
        error = "";
        loading = true;

        try {
            const response = await authPost("/projects", {
                project_name: projectName,
            });

            if (response.ok) {
                const data = await response.json();
                oncreate({ detail: { projectName, projectId: data.id } });
            } else {
                const data = await response.json();
                error = data.detail || "Failed to create project";
            }
        } catch (err) {
            error = "Connection error. Please try again.";
        } finally {
            loading = false;
        }
    }
</script>

<div class="create-project-container">
    <div class="create-project-card">
        <div class="create-project-header">
            <h1>Create Project</h1>
            <p>Start a new project in {appName}</p>
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
                <label for="project-name">Project Name</label>
                <input
                    type="text"
                    id="project-name"
                    bind:value={projectName}
                    placeholder="Enter project name"
                    required
                    disabled={loading}
                />
            </div>

            <div class="button-group">
                <button
                    type="button"
                    class="cancel-button"
                    onclick={oncancel}
                    disabled={loading}
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    class="create-button"
                    disabled={loading || !projectName.trim()}
                >
                    {#if loading}
                        <span class="spinner"></span>
                        Creating...
                    {:else}
                        Create Project
                    {/if}
                </button>
            </div>
        </form>
    </div>
</div>

<style>
    .create-project-container {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 100vh;
        width: 100%;
        background-color: var(--bg-primary);
        padding: var(--spacing-lg);
    }

    .create-project-card {
        width: 100%;
        max-width: 400px;
        background: var(--bg-secondary);
        border-radius: 32px;
        box-shadow: var(--shadow-sm);
        padding: var(--spacing-xl);
        border: 1px solid transparent;
        transition: all 0.2s;
    }

    .create-project-card:hover,
    .create-project-card:focus-within {
        box-shadow: var(--shadow-md);
        border-color: var(--border-color);
    }

    .create-project-header {
        text-align: center;
        margin-bottom: var(--spacing-xl);
    }

    .create-project-header h1 {
        font-family: var(--font-display);
        font-size: 1.75rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: var(--spacing-xs);
    }

    .create-project-header p {
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

    .button-group {
        display: flex;
        gap: var(--spacing-sm);
        margin-top: var(--spacing-sm);
    }

    .cancel-button {
        flex: 1;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0.875rem 1.5rem;
        background-color: var(--bg-primary);
        color: var(--text-primary);
        font-size: 1rem;
        font-weight: 500;
        border-radius: var(--radius-full);
        border: 1px solid var(--border-color);
        transition: all 0.2s ease;
    }

    .cancel-button:hover:not(:disabled) {
        background-color: var(--bg-secondary);
        border-color: var(--text-secondary);
    }

    .cancel-button:disabled {
        opacity: 0.7;
        cursor: not-allowed;
    }

    .create-button {
        flex: 1;
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
        transition: opacity 0.2s ease;
    }

    .create-button:hover:not(:disabled) {
        opacity: 0.85;
    }

    .create-button:disabled {
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
</style>
