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
        padding: 0.5rem 1rem;
        border-radius: 0.25rem;
        cursor: pointer;
        border: none;
        font-weight: 500;
        transition: background-color 0.2s;
    }
    .primary {
        background-color: #3b82f6;
        color: white;
    }
    .primary:hover {
        background-color: #2563eb;
    }
    .secondary {
        background-color: #e5e7eb;
        color: #374151;
    }
    .secondary:hover {
        background-color: #d1d5db;
    }
    .danger {
        background-color: #ef4444;
        color: white;
    }
    .danger:hover {
        background-color: #dc2626;
    }
</style>
