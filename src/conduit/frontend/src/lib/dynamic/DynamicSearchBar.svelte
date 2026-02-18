<script>
    import { createEventDispatcher } from "svelte";

    export let id;
    export let placeholder = "Search...";
    export let target; // table id

    const dispatch = createEventDispatcher();

    function handleInput(event) {
        dispatch("search", { target, value: event.target.value });
    }
</script>

<div class="search-bar">
    <input type="text" {id} {placeholder} on:input={handleInput} />
</div>

<style>
    .search-bar {
        margin-bottom: 0.5rem;
        width: 100%;
    }
    input {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid #d1d5db;
        border-radius: 0.25rem;
        font-size: 0.875rem;
        box-sizing: border-box;
    }
    input:focus {
        outline: none;
        border-color: #3b82f6;
    }
</style>
