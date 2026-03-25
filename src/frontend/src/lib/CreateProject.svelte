<script>
    import { authPost } from "./utils.js";

    let { appName = "Frontier AI", oncreate = () => {}, oncancel = () => {} } = $props();

    let projectName = $state("");
    let error = $state("");
    let nameHint = $state("");
    let loading = $state(false);

    const PROJECT_NAME_RE = /^[a-z0-9][a-z0-9_-]*$/;

    function validateName(name) {
        const n = name.trim().toLowerCase();
        if (!n) return "Project name cannot be empty.";
        if (n.length > 63) return "Project name cannot exceed 63 characters.";
        if (n[0] === '-' || n[0] === '_') return "Project name cannot start with a hyphen or underscore.";
        if (!PROJECT_NAME_RE.test(n)) return "Only lowercase letters, numbers, hyphens, and underscores allowed.";
        return "";
    }

    function suggestName(raw) {
        return raw.trim().toLowerCase().replace(/[^a-z0-9_-]/g, '-').replace(/-+/g, '-').replace(/^[-_]+/, '').slice(0, 63);
    }

    function handleInput() {
        const raw = projectName;
        const validationError = validateName(raw);
        if (validationError && raw.trim()) {
            error = validationError;
            const suggested = suggestName(raw);
            nameHint = suggested && !validateName(suggested) ? suggested : "";
        } else {
            error = "";
            nameHint = "";
        }
    }

    function applySuggestion() {
        projectName = nameHint;
        nameHint = "";
        error = "";
    }

    async function handleSubmit(e) {
        e.preventDefault();
        const validationError = validateName(projectName);
        if (validationError) {
            error = validationError;
            return;
        }
        error = "";
        loading = true;

        try {
            const response = await authPost("/projects", {
                project_name: projectName.trim().toLowerCase(),
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
                    oninput={handleInput}
                    placeholder="e.g. my-project"
                    required
                    minlength="1"
                    maxlength="63"
                    pattern="[a-z0-9][a-z0-9_\-]*"
                    title="Lowercase letters, numbers, hyphens, and underscores only. Must start with a letter or number."
                    disabled={loading}
                />
                <span class="name-hint-text">Lowercase letters, numbers, hyphens, and underscores only</span>
                {#if nameHint}
                    <button type="button" class="name-suggestion" onclick={applySuggestion}>
                        Use <strong>{nameHint}</strong> instead?
                    </button>
                {/if}
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
        width: 100%;
        height: 100%;
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
        color: var(--text-primary);
        transition: all 0.2s ease;
    }

    .form-group input:focus {
        border-color: var(--primary-accent);
        box-shadow: 0 0 0 2px var(--accent-glow);
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
        background-color: var(--primary-accent);
        color: white;
        font-size: 1rem;
        font-weight: 600;
        border-radius: var(--radius-full);
        transition: opacity 0.2s ease, background-color 0.2s ease;
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
        background: rgba(220, 38, 38, 0.1);
        border: 1px solid rgba(220, 38, 38, 0.3);
        border-radius: var(--radius-md);
        color: #f87171;
        font-size: 0.875rem;
    }

    .name-hint-text {
        font-size: 0.75rem;
        color: var(--text-secondary);
    }

    .name-suggestion {
        display: inline-block;
        padding: 0.3rem 0.6rem;
        font-size: 0.8rem;
        color: var(--primary-accent);
        background: var(--accent-glow);
        border: 1px solid rgba(225, 29, 72, 0.2);
        border-radius: var(--radius-sm);
        cursor: pointer;
        transition: background 0.12s ease;
        text-align: left;
    }

    .name-suggestion:hover {
        background: rgba(225, 29, 72, 0.15);
    }
</style>
