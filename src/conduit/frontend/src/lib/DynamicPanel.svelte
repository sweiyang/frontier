<script>
    import DynamicButton from "./dynamic/DynamicButton.svelte";
    import DynamicTextInput from "./dynamic/DynamicTextInput.svelte";
    import DynamicSearchBar from "./dynamic/DynamicSearchBar.svelte";
    import DynamicTable from "./dynamic/DynamicTable.svelte";
    import { createEventDispatcher, onMount, onDestroy } from "svelte";

    export let elements = [];

    const dispatch = createEventDispatcher();

    // Component state: { [id]: { value: ..., selected: ... } }
    export let componentState = {};

    // Search filters: { [tableId]: filterString }
    let searchFilters = {};

    // Lifted selection state: { [tableId]: [rowId, ...] }
    let tableSelectedIds = {};

    // Modal state
    let expandedElementId = null;
    $: expandedElement = expandedElementId
        ? elements.find((el) => el.id === expandedElementId)
        : null;

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

        // Extract IDs so both inline and modal tables stay in sync
        if (selection == null) {
            tableSelectedIds[id] = [];
        } else if (Array.isArray(selection)) {
            tableSelectedIds[id] = selection.map((r) => r.id);
        } else {
            tableSelectedIds[id] = [selection.id];
        }
        tableSelectedIds = tableSelectedIds;
    }

    function handleDelete(event) {
        const { id: tableId, row } = event.detail;
        const element = elements.find((el) => el.id === tableId);
        if (element) {
            element.rows = element.rows.filter((r) => r.id !== row.id);
            elements = elements;
        }
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

    function handleExpand(event) {
        expandedElementId = event.detail.id;
    }

    function closeModal() {
        expandedElementId = null;
    }

    function handleModalKeydown(event) {
        if (event.key === "Escape") closeModal();
    }

    function handleBackdropClick(event) {
        if (event.target === event.currentTarget) closeModal();
    }

    onMount(() => {
        document.addEventListener("keydown", handleModalKeydown);
    });
    onDestroy(() => {
        document.removeEventListener("keydown", handleModalKeydown);
    });
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
                    external_selected_ids={tableSelectedIds[element.id] || null}
                    on:selection={handleSelection}
                    on:delete={handleDelete}
                    on:add={handleAdd}
                    on:expand={handleExpand}
                />
            {/if}
        </div>
    {/each}
</div>

{#if expandedElement}
    <!-- svelte-ignore a11y-click-events-have-key-events -->
    <!-- svelte-ignore a11y-no-static-element-interactions -->
    <div class="modal-backdrop" on:click={handleBackdropClick}>
        <div class="modal-container">
            <div class="modal-header">
                <h2 class="modal-title">{expandedElement.title || "Data View"}</h2>
                <button class="modal-close" on:click={closeModal} title="Close (Esc)">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>
            <div class="modal-body">
                {#if expandedElement.type === "table"}
                    <DynamicTable
                        {...expandedElement}
                        expanded={true}
                        filter={searchFilters[expandedElement.id] || ""}
                        searchable={true}
                        external_selected_ids={tableSelectedIds[expandedElement.id] || null}
                        on:selection={handleSelection}
                        on:delete={handleDelete}
                        on:add={handleAdd}
                        on:expand={() => {}}
                    />
                {/if}
            </div>
        </div>
    </div>
{/if}

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

    /* Modal */
    .modal-backdrop {
        position: fixed;
        inset: 0;
        background: rgba(0, 0, 0, 0.5);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        animation: fadeIn 0.15s ease-out;
    }
    .modal-container {
        background: white;
        border-radius: 0.75rem;
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
        width: 100%;
        max-width: 1100px;
        max-height: 90vh;
        display: flex;
        flex-direction: column;
        animation: scaleIn 0.15s ease-out;
    }
    .modal-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 1.5rem;
        border-bottom: 1px solid #e5e7eb;
        flex-shrink: 0;
    }
    .modal-title {
        font-size: 1.125rem;
        font-weight: 600;
        margin: 0;
        color: #111827;
    }
    .modal-close {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: 0.5rem;
        border: none;
        background: transparent;
        color: #6b7280;
        cursor: pointer;
        transition: all 0.15s;
    }
    .modal-close:hover {
        background: #f3f4f6;
        color: #111827;
    }
    .modal-body {
        padding: 1.5rem;
        overflow-y: auto;
        flex: 1;
        min-height: 0;
    }

    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    @keyframes scaleIn {
        from { opacity: 0; transform: scale(0.95); }
        to { opacity: 1; transform: scale(1); }
    }
</style>
