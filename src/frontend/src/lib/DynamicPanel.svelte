<script>
    import DynamicButton from "./dynamic/DynamicButton.svelte";
    import DynamicTextInput from "./dynamic/DynamicTextInput.svelte";
    import DynamicSearchBar from "./dynamic/DynamicSearchBar.svelte";
    import DynamicTable from "./dynamic/DynamicTable.svelte";
    import DynamicStats from "./dynamic/DynamicStats.svelte";
    import { X } from "lucide-svelte";
    import { onMount, onDestroy } from "svelte";

    let {
        elements = [],
        componentState = $bindable({}),
        onsendMessage = () => {},
    } = $props();

    // Search filters: { [tableId]: { value: string, columns: string[] } }
    let searchFilters = $state({});

    // Lifted selection state: { [tableId]: [rowId, ...] }
    let tableSelectedIds = $state({});

    // Cell-level selections: { [tableId]: { [rowId]: { [colKey]: bool } } }
    let tableCellSelections = $state({});

    // Modal state
    let expandedElementId = $state(null);
    let expandedElement = $derived(
        expandedElementId
            ? elements.find((el) => el.id === expandedElementId)
            : null
    );

    // Initialize componentState entries for text_input elements with their default values
    $effect(() => {
      let needsUpdate = false;
      const patch = {};
      for (const el of elements) {
        if (el.type === "text_input" && !(el.id in componentState)) {
          patch[el.id] = { value: el.value || "" };
          needsUpdate = true;
        }
      }
      if (needsUpdate) {
        componentState = { ...componentState, ...patch };
      }
    });

    function handleInputChange(event) {
        const { id, value } = event.detail;
        componentState = { ...componentState, [id]: { ...componentState[id], value } };
    }

    function handleSearch(event) {
        const { target, value, columns = [] } = event.detail;
        searchFilters = { ...searchFilters, [target]: { value, columns } };
    }

    function getTargetTableColumns(targetId) {
        const table = elements.find((el) => el.id === targetId && el.type === "table");
        return table?.columns || [];
    }

    function handleSelection(event) {
        const { id, selection } = event.detail;
        componentState = { ...componentState, [id]: { ...componentState[id], selected: selection } };

        let newIds;
        if (selection == null) {
            newIds = [];
        } else if (Array.isArray(selection)) {
            newIds = selection.map((r) => r.id);
        } else {
            newIds = [selection.id];
        }
        tableSelectedIds = { ...tableSelectedIds, [id]: newIds };
    }

    function handleDelete(event) {
        const { id: tableId, row } = event.detail;
        elements = elements.map((el) =>
            el.id === tableId ? { ...el, rows: el.rows.filter((r) => r.id !== row.id) } : el
        );
        const existing = componentState[tableId]?.deleted || [];
        componentState = {
            ...componentState,
            [tableId]: { ...componentState[tableId], deleted: [...existing, row] },
        };
    }

    function handleAdd(event) {
        const { id: tableId, row } = event.detail;
        elements = elements.map((el) =>
            el.id === tableId ? { ...el, rows: [...el.rows, row] } : el
        );
        const existing = componentState[tableId]?.added || [];
        componentState = {
            ...componentState,
            [tableId]: { ...componentState[tableId], added: [...existing, row] },
        };
    }

    function handleCellSelection(event) {
        const { id, cellSelections } = event.detail;
        tableCellSelections = { ...tableCellSelections, [id]: cellSelections };

        const element = elements.find((el) => el.id === id);
        const rowsById = {};
        if (element?.rows) {
            for (const row of element.rows) {
                rowsById[row.id] = row;
            }
        }

        const enriched = {};
        for (const [rowId, colSelections] of Object.entries(cellSelections)) {
            const hasAnySelected = Object.values(colSelections).some(Boolean);
            if (hasAnySelected && rowsById[rowId]) {
                enriched[rowId] = {
                    ...rowsById[rowId],
                    _selections: colSelections,
                };
            }
        }

        componentState = {
            ...componentState,
            [id]: { ...componentState[id], cell_selections: enriched },
        };
    }

    function handleSendMessage(event) {
        onsendMessage(event);
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
                <DynamicSearchBar
                    {...element}
                    columns={getTargetTableColumns(element.target)}
                    on:search={handleSearch}
                />
            {:else if element.type === "table"}
                <DynamicTable
                    {...element}
                    filter={searchFilters[element.id]?.value || ""}
                    filter_columns={searchFilters[element.id]?.columns || []}
                    searchable={element.searchable}
                    external_selected_ids={tableSelectedIds[element.id] || null}
                    external_cell_selections={tableCellSelections[element.id] || null}
                    on:selection={handleSelection}
                    on:cellSelection={handleCellSelection}
                    on:delete={handleDelete}
                    on:add={handleAdd}
                    on:expand={handleExpand}
                />
            {:else if element.type === "stats"}
                <DynamicStats {...element} />
            {/if}
        </div>
    {/each}
</div>

{#if expandedElement}
    <div
        class="modal-backdrop"
        role="dialog"
        aria-modal="true"
        aria-labelledby="dynamic-panel-modal-title"
        tabindex="-1"
        on:click={handleBackdropClick}
        on:keydown={(e) => { if (e.key === 'Escape') closeModal(); }}
    >
        <div class="modal-container">
            <div class="modal-header">
                <h2 id="dynamic-panel-modal-title" class="modal-title">{expandedElement.title || "Data View"}</h2>
                <button class="modal-close" on:click={closeModal} title="Close (Esc)">
                    <X size={20} />
                </button>
            </div>
            <div class="modal-body">
                {#if expandedElement.type === "table"}
                    <DynamicTable
                        {...expandedElement}
                        expanded={true}
                        filter={searchFilters[expandedElement.id]?.value || ""}
                        filter_columns={searchFilters[expandedElement.id]?.columns || []}
                        searchable={true}
                        external_selected_ids={tableSelectedIds[expandedElement.id] || null}
                        external_cell_selections={tableCellSelections[expandedElement.id] || null}
                        on:selection={handleSelection}
                        on:cellSelection={handleCellSelection}
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
        border-left: 1px solid var(--border-color);
        background: var(--bg-secondary);
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
        background: rgba(0, 0, 0, 0.7);
        z-index: 1000;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 2rem;
        animation: fadeIn 0.15s ease-out;
    }
    .modal-container {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
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
        border-bottom: 1px solid var(--border-color);
        background: var(--bg-primary);
        border-radius: var(--radius-lg) var(--radius-lg) 0 0;
        flex-shrink: 0;
    }
    .modal-title {
        font-size: 1.125rem;
        font-weight: 600;
        margin: 0;
        color: var(--text-primary);
    }
    .modal-close {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 36px;
        height: 36px;
        border-radius: var(--radius-md);
        border: none;
        background: transparent;
        color: var(--text-muted);
        cursor: pointer;
        transition: all 0.15s;
    }
    .modal-close:hover {
        background: rgba(255, 255, 255, 0.06);
        color: var(--text-primary);
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
