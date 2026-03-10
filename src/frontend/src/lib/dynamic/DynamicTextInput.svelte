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
        gap: 0.25rem;
        width: 100%;
    }
    label {
        font-size: 0.875rem;
        font-weight: 500;
        color: #374151;
    }
    input,
    textarea {
        padding: 0.5rem;
        border: 1px solid #d1d5db;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        width: 100%;
        box-sizing: border-box;
    }
    input:focus,
    textarea:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px #3b82f6;
    }
</style>
