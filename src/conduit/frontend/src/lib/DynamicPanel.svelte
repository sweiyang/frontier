<script>
    import DynamicButton from "./dynamic/DynamicButton.svelte";
    import DynamicTextInput from "./dynamic/DynamicTextInput.svelte";
    import DynamicSearchBar from "./dynamic/DynamicSearchBar.svelte";
    import DynamicTable from "./dynamic/DynamicTable.svelte";
    import { createEventDispatcher } from "svelte";

    export let elements = [];

    const dispatch = createEventDispatcher();

    // Component state: { [id]: { value: ..., selected: ... } }
    export let componentState = {};

    // Search filters: { [tableId]: filterString }
    let searchFilters = {};

    function handleInputChange(event) {
        const { id, value } = event.detail;
        componentState[id] = { ...componentState[id], value };
        componentState = componentState;
    }

    function handleSearch(event) {
        const { target, value } = event.detail;
        searchFilters[target] = value;
        searchFilters = searchFilters;
    }

    function handleSelection(event) {
        const { id, selection } = event.detail;
        componentState[id] = { ...componentState[id], selected: selection };
        componentState = componentState;
    }

    function handleDelete(event) {
        const { id: tableId, row } = event.detail;
        const element = elements.find((el) => el.id === tableId);
        if (element) {
            element.rows = element.rows.filter((r) => r.id !== row.id);
            elements = elements; // trigger reactivity
        }
        // Track deleted rows in componentState so the backend receives them
        const existing = componentState[tableId]?.deleted || [];
        componentState[tableId] = {
            ...componentState[tableId],
            deleted: [...existing, row],
        };
        componentState = componentState;
    }

    function handleAdd(event) {
        const { id: tableId, row } = event.detail;
        const existing = componentState[tableId]?.added || [];
        componentState[tableId] = {
            ...componentState[tableId],
            added: [...existing, row],
        };
        componentState = componentState;
    }

    function handleSendMessage(event) {
        dispatch("sendMessage", event.detail);
    }
</script>

<div class="dynamic-panel">
    {#each elements as element (element.id)}
        <div class="element-wrapper" class:button-wrapper={element.type === "button"}>
            {#if element.type === "button"}
                <DynamicButton
                    {...element}
                    context={componentState}
                    on:sendMessage={handleSendMessage}
                />
            {:else if element.type === "text_input"}
                <DynamicTextInput {...element} on:change={handleInputChange} />
            {:else if element.type === "search_bar"}
                <DynamicSearchBar {...element} on:search={handleSearch} />
            {:else if element.type === "table"}
                <DynamicTable
                    {...element}
                    filter={searchFilters[element.id] || ""}
                    searchable={element.searchable}
                    on:selection={handleSelection}
                    on:delete={handleDelete}
                    on:add={handleAdd}
                />
            {/if}
        </div>
    {/each}
</div>

<style>
    .dynamic-panel {
        padding: 1rem;
        border-left: 1px solid #e5e7eb;
        background: white;
        height: 100%;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 1rem;
        box-sizing: border-box;
    }
    .element-wrapper {
        width: 100%;
    }
    .element-wrapper.button-wrapper {
        display: flex;
        justify-content: center;
    }
</style>
