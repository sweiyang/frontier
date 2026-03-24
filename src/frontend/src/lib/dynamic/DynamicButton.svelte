<script>
    import { createEventDispatcher } from "svelte";

    export let id;
    export let label;
    export let variant = "primary";
    export let action;
    export let payload_template;
    export let context = {}; // { [componentId]: { value: ..., selected: ... } }

    const dispatch = createEventDispatcher();

    function handleClick() {
        if (action === "send_message") {
            // Resolve payload template
            let payload = payload_template.replace(
                /\{\{(.*?)\}\}/g,
                (_, path) => {
                    const parts = path.split(".");
                    let current = context;
                    for (const part of parts) {
                        current = current?.[part];
                    }

                    if (current == null) {
                        return "";
                    }

                    if (typeof current === "object") {
                        try {
                            return JSON.stringify(current);
                        } catch {
                            return String(current);
                        }
                    }

                    return String(current);
                },
            );
            dispatch("sendMessage", payload);
        }
    }
</script>

<button class="btn {variant}" on:click={handleClick}>
    {label}
</button>

<style>
    .btn {
        padding: 0.6rem 1.25rem;
        border-radius: var(--radius-xl, 1rem);
        cursor: pointer;
        border: none;
        font-weight: 500;
        font-size: 0.875rem;
        transition: background-color 0.15s, transform 0.12s;
    }
    .btn:active {
        transform: scale(0.97);
    }
    .primary {
        background-color: var(--primary-accent, #e11d48);
        color: white;
    }
    .primary:hover {
        background-color: var(--primary-accent-hover, #f43f5e);
    }
    .secondary {
        background-color: transparent;
        color: var(--text-primary, #e2e8f0);
        border: 1px solid var(--border-strong);
    }
    .secondary:hover {
        background-color: var(--bg-hover);
    }
    .danger {
        background-color: #dc2626;
        color: white;
    }
    .danger:hover {
        background-color: #ef4444;
    }
    .ghost {
        background-color: transparent;
        color: var(--text-secondary, #94a3b8);
        border: 1px solid var(--border-strong);
    }
    .ghost:hover {
        background-color: rgba(255, 255, 255, 0.06);
        color: var(--text-primary, #e2e8f0);
    }
</style>
