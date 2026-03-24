<script>
    import { createEventDispatcher } from "svelte";
    import { Search } from "lucide-svelte";

    export let id;
    export let placeholder = "Search...";
    export let target; // table id
    export let columns = []; // columns from the target table (for column filter dropdown)

    let selectedColumns = new Set();
    let showColumnDropdown = false;

    const dispatch = createEventDispatcher();

    let currentValue = "";

    function handleInput(event) {
        currentValue = event.target.value;
        dispatch("search", { target, value: currentValue, columns: [...selectedColumns] });
    }

    function toggleColumn(key) {
        if (selectedColumns.has(key)) {
            selectedColumns.delete(key);
        } else {
            selectedColumns.add(key);
        }
        selectedColumns = selectedColumns;
        dispatch("search", { target, value: currentValue, columns: [...selectedColumns] });
    }

    function toggleAllColumns() {
        if (selectedColumns.size === 0) {
            columns.forEach((col) => selectedColumns.add(col.key));
        } else {
            selectedColumns.clear();
        }
        selectedColumns = selectedColumns;
        dispatch("search", { target, value: currentValue, columns: [...selectedColumns] });
    }
</script>

<div class="search-bar">
    <div class="search-input-wrap">
        <span class="search-icon"><Search size={16} /></span>
        <input
            type="text"
            {id}
            placeholder={selectedColumns.size > 0
                ? `Search ${[...selectedColumns].map(k => columns.find(c => c.key === k)?.label).filter(Boolean).join(', ')}...`
                : placeholder}
            on:input={handleInput}
        />
    </div>
    {#if columns.length > 0}
        <div class="filter-wrapper">
            <button
                class="filter-btn"
                class:active={selectedColumns.size > 0}
                on:click={() => (showColumnDropdown = !showColumnDropdown)}
                title="Filter by column"
            >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                </svg>
                {#if selectedColumns.size > 0}
                    <span class="filter-badge">{selectedColumns.size}</span>
                {/if}
            </button>
            {#if showColumnDropdown}
                <div class="column-dropdown">
                    <label class="column-option">
                        <input
                            type="checkbox"
                            checked={selectedColumns.size === 0}
                            on:change={toggleAllColumns}
                        />
                        All columns
                    </label>
                    {#each columns as col}
                        <label class="column-option">
                            <input
                                type="checkbox"
                                checked={selectedColumns.has(col.key)}
                                on:change={() => toggleColumn(col.key)}
                            />
                            {col.label}
                        </label>
                    {/each}
                </div>
            {/if}
        </div>
    {/if}
</div>

<style>
    .search-bar {
        display: flex;
        gap: 0.5rem;
        align-items: center;
        margin-bottom: 0.5rem;
        width: 100%;
    }
    .search-input-wrap {
        flex: 1;
        min-width: 0;
        position: relative;
        display: flex;
        align-items: center;
    }
    .search-icon {
        position: absolute;
        left: 0.75rem;
        color: var(--text-muted, #64748b);
        display: flex;
        align-items: center;
        pointer-events: none;
    }
    input {
        flex: 1;
        min-width: 0;
        padding: 0.5rem 0.75rem 0.5rem 2.25rem;
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-xl, 1rem);
        font-size: 0.875rem;
        box-sizing: border-box;
        background: var(--bg-primary, #020617);
        color: var(--text-primary, #e2e8f0);
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    input::placeholder {
        color: var(--text-muted, #64748b);
    }
    input:focus {
        outline: none;
        border-color: var(--primary-accent, #e11d48);
        box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.15);
    }
    .filter-wrapper {
        position: relative;
        flex-shrink: 0;
    }
    .filter-btn {
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        width: 32px;
        height: 32px;
        border-radius: var(--radius-md, 0.5rem);
        border: 1px solid var(--border-strong);
        background: var(--bg-primary, #020617);
        color: var(--text-muted, #64748b);
        cursor: pointer;
        transition: all 0.15s;
    }
    .filter-btn:hover {
        background: var(--bg-hover);
        color: var(--text-primary, #e2e8f0);
        border-color: #475569;
    }
    .filter-btn.active {
        background: var(--accent-glow, rgba(225, 29, 72, 0.1));
        color: var(--primary-accent, #e11d48);
        border-color: var(--primary-accent, #e11d48);
    }
    .filter-badge {
        position: absolute;
        top: -6px;
        right: -6px;
        background: var(--primary-accent, #e11d48);
        color: white;
        font-size: 0.625rem;
        font-weight: 600;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        line-height: 1;
    }
    .column-dropdown {
        position: absolute;
        top: calc(100% + 4px);
        right: 0;
        background: var(--bg-primary, #020617);
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-md, 0.5rem);
        box-shadow: var(--shadow-lg);
        z-index: 20;
        min-width: 160px;
        max-height: 240px;
        overflow-y: auto;
        padding: 0.25rem;
    }
    .column-option {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        width: 100%;
        padding: 0.4rem 0.75rem;
        font-size: 0.8125rem;
        color: var(--text-secondary, #94a3b8);
        border-radius: var(--radius-sm, 0.375rem);
        cursor: pointer;
        white-space: nowrap;
    }
    .column-option:hover {
        background: var(--bg-hover);
        color: var(--text-primary, #e2e8f0);
    }
    .column-option input[type="checkbox"] {
        margin: 0;
        cursor: pointer;
        accent-color: var(--primary-accent, #e11d48);
    }
</style>
