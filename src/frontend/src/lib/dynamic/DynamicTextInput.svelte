<script>
    import { createEventDispatcher } from "svelte";

    export let id;
    export let label;
    export let placeholder = "";
    export let required = false;
    export let multiline = false;
    export let value = "";

    const dispatch = createEventDispatcher();

    function handleInput(event) {
        value = event.target.value;
        dispatch("change", { id, value });
    }
</script>

<div class="input-group">
    {#if label}
        <label for={id}>{label}</label>
    {/if}
    {#if multiline}
        <textarea
            {id}
            {placeholder}
            {required}
            {value}
            on:input={handleInput}
            rows="4"
        ></textarea>
    {:else}
        <input
            type="text"
            {id}
            {placeholder}
            {required}
            {value}
            on:input={handleInput}
        />
    {/if}
</div>

<style>
    .input-group {
        display: flex;
        flex-direction: column;
        gap: 0.375rem;
        width: 100%;
    }
    label {
        font-size: 0.8125rem;
        font-weight: 500;
        color: var(--text-secondary, #94a3b8);
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    input,
    textarea {
        padding: 0.625rem 0.875rem;
        border: 1px solid #334155;
        border-radius: var(--radius-xl, 1rem);
        font-size: 0.875rem;
        width: 100%;
        box-sizing: border-box;
        background: var(--bg-primary, #020617);
        color: var(--text-primary, #e2e8f0);
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    input::placeholder,
    textarea::placeholder {
        color: var(--text-muted, #64748b);
    }
    input:focus,
    textarea:focus {
        outline: none;
        border-color: var(--primary-accent, #e11d48);
        box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.15);
    }
</style>
