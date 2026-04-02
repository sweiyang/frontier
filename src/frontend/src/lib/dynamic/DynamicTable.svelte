<script>
    import { createEventDispatcher } from "svelte";

    export let id;
    export let title;
    export let select_mode = "single";
    export let columns = [];
    export let rows = [];
    export let filter = ""; // external search filter text
    export let filter_columns = []; // external column keys to filter by (empty = all columns)
    export let searchable = false; // enable inbuilt search bar
    export let deletable = false; // enable row deletion
    export let addable = false; // enable adding rows via text input
    export let page_size = 10;
    export let expanded = false; // when true, renders in expanded modal mode
    export let external_selected_ids = null; // parent-controlled selection (array of row IDs)
    export let external_cell_selections = null; // parent-controlled cell selections { rowId: { colKey: bool } }

    let addInputs = {}; // { [columnKey]: value }
    let showAddForm = false;

    let internalFilter = "";
    let internalFilterColumns = new Set(); // empty = all columns
    let showColumnDropdown = false;

    function toggleColumn(key) {
        if (internalFilterColumns.has(key)) {
            internalFilterColumns.delete(key);
        } else {
            internalFilterColumns.add(key);
        }
        internalFilterColumns = internalFilterColumns;
    }

    function toggleAllColumns() {
        if (internalFilterColumns.size === 0) {
            columns.forEach((col) => internalFilterColumns.add(col.key));
        } else {
            internalFilterColumns.clear();
        }
        internalFilterColumns = internalFilterColumns;
    }

    let selectedIds = new Set();

    // Sync internal selectedIds from external prop when it changes
    let lastExternalRef = null;
    $: if (external_selected_ids !== lastExternalRef) {
        lastExternalRef = external_selected_ids;
        if (external_selected_ids != null) {
            selectedIds = new Set(external_selected_ids);
        }
    }

    // Cell-level selections for selectable columns: { [rowId]: { [colKey]: boolean } }
    let cellSelections = {};

    let lastCellSelectionsRef = null;
    $: if (external_cell_selections !== lastCellSelectionsRef) {
        lastCellSelectionsRef = external_cell_selections;
        if (external_cell_selections != null) {
            cellSelections = { ...external_cell_selections };
        }
    }

    $: selectableColumns = columns.filter((col) => col.selectable);

    function toggleCellSelection(rowId, colKey, event) {
        event.stopPropagation();
        if (!cellSelections[rowId]) {
            cellSelections[rowId] = {};
        }
        cellSelections[rowId][colKey] = !cellSelections[rowId][colKey];
        cellSelections = cellSelections;
        dispatch("cellSelection", { id, cellSelections });
    }

    function isCellSelected(rowId, colKey) {
        return !!cellSelections[rowId]?.[colKey];
    }

    // Sort state
    let sortKey = "";
    let sortDirection = 1; // 1 for asc, -1 for desc

    // Pagination state
    let currentPage = 0;

    $: effectiveFilter = filter || internalFilter;
    $: effectiveFilterCols = filter
        ? new Set(filter_columns)
        : internalFilterColumns;

    $: filteredRows = rows
        .filter((row) => {
            if (!effectiveFilter) return true;
            const query = effectiveFilter.toLowerCase();
            if (effectiveFilterCols.size > 0) {
                return [...effectiveFilterCols].some((key) =>
                    String(row[key] ?? "").toLowerCase().includes(query),
                );
            }
            return Object.values(row).some((val) =>
                String(val).toLowerCase().includes(query),
            );
        })
        .sort((a, b) => {
            if (!sortKey) return 0;
            const valA = a[sortKey];
            const valB = b[sortKey];
            if (valA < valB) return -1 * sortDirection;
            if (valA > valB) return 1 * sortDirection;
            return 0;
        });

    $: totalPages = Math.max(1, Math.ceil(filteredRows.length / effectivePageSize));
    $: effectivePageSize = expanded ? 50 : page_size;
    $: if (currentPage >= totalPages) currentPage = Math.max(0, totalPages - 1);
    $: paginatedRows = filteredRows.slice(
        currentPage * effectivePageSize,
        (currentPage + 1) * effectivePageSize,
    );
    $: needsPagination = filteredRows.length > effectivePageSize;

    $: allSelected =
        filteredRows.length > 0 &&
        filteredRows.every((r) => selectedIds.has(r.id));
    $: indeterminate =
        filteredRows.length > 0 &&
        !allSelected &&
        filteredRows.some((r) => selectedIds.has(r.id));

    const dispatch = createEventDispatcher();

    function toggleAll() {
        if (select_mode !== "multi") return;

        if (allSelected) {
            filteredRows.forEach((r) => selectedIds.delete(r.id));
        } else {
            filteredRows.forEach((r) => selectedIds.add(r.id));
        }
        selectedIds = selectedIds;
        dispatchSelection();
    }

    function dispatchSelection() {
        let selection;
        if (select_mode === "single") {
            selection =
                selectedIds.size > 0
                    ? rows.find((r) => r.id === [...selectedIds][0])
                    : null;
        } else {
            selection = rows.filter((r) => selectedIds.has(r.id));
        }
        dispatch("selection", { id, selection });
    }

    function handleSelect(row, event) {
        if (select_mode === "none") return;

        if (select_mode === "single") {
            if (selectedIds.has(row.id)) {
                selectedIds.clear();
            } else {
                selectedIds.clear();
                selectedIds.add(row.id);
            }
        } else {
            if (selectedIds.has(row.id)) {
                selectedIds.delete(row.id);
            } else {
                selectedIds.add(row.id);
            }
        }
        selectedIds = selectedIds;
        dispatchSelection();
    }

    function handleSort(key) {
        if (sortKey === key) {
            sortDirection *= -1;
        } else {
            sortKey = key;
            sortDirection = 1;
        }
    }

    function handleDelete(row, event) {
        event.stopPropagation();
        dispatch("delete", { id, row });
    }

    function handleAdd() {
        const hasValue = columns.some((col) => (addInputs[col.key] || "").trim());
        if (!hasValue) return;
        const newRow = { id: `added_${Date.now()}` };
        columns.forEach((col) => {
            newRow[col.key] = (addInputs[col.key] || "").trim();
        });
        dispatch("add", { id, row: newRow });
        addInputs = {};
    }

    function handleAddKeydown(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            handleAdd();
        }
    }

    function cancelAdd() {
        addInputs = {};
        showAddForm = false;
    }

    function goToPage(page) {
        currentPage = Math.max(0, Math.min(page, totalPages - 1));
    }

    function getVisiblePages(current, total) {
        if (total <= 7) return Array.from({ length: total }, (_, i) => i);
        const pages = [];
        pages.push(0);
        let start = Math.max(1, current - 1);
        let end = Math.min(total - 2, current + 1);
        if (current <= 2) { start = 1; end = Math.min(3, total - 2); }
        if (current >= total - 3) { start = Math.max(1, total - 4); end = total - 2; }
        if (start > 1) pages.push(-1); // ellipsis
        for (let i = start; i <= end; i++) pages.push(i);
        if (end < total - 2) pages.push(-1); // ellipsis
        pages.push(total - 1);
        return pages;
    }

    function requestExpand() {
        dispatch("expand", { id });
    }
</script>

<div class="table-container" class:expanded>
    <div class="table-header">
        {#if title}<h3 class="table-title">{title}</h3>{/if}
        <div class="table-header-actions">
            {#if filteredRows.length > 0}
                <span class="row-count">{filteredRows.length} row{filteredRows.length !== 1 ? 's' : ''}</span>
            {/if}
            {#if !expanded}
                <button class="expand-btn" on:click={requestExpand} title="Expand to full view">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="15 3 21 3 21 9"></polyline>
                        <polyline points="9 21 3 21 3 15"></polyline>
                        <line x1="21" y1="3" x2="14" y2="10"></line>
                        <line x1="3" y1="21" x2="10" y2="14"></line>
                    </svg>
                </button>
            {/if}
        </div>
    </div>
    {#if searchable}
        <div class="search-container">
            <input
                type="text"
                placeholder={internalFilterColumns.size > 0
                    ? `Search ${[...internalFilterColumns].map(k => columns.find(c => c.key === k)?.label).filter(Boolean).join(', ')}...`
                    : "Search all columns..."}
                bind:value={internalFilter}
                class="search-input"
            />
            <div class="filter-wrapper">
                <button
                    class="filter-btn"
                    class:active={internalFilterColumns.size > 0}
                    on:click={() => (showColumnDropdown = !showColumnDropdown)}
                    title="Filter by column"
                >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"></polygon>
                    </svg>
                    {#if internalFilterColumns.size > 0}
                        <span class="filter-badge">{internalFilterColumns.size}</span>
                    {/if}
                </button>
                {#if showColumnDropdown}
                    <div class="column-dropdown">
                        <label class="column-option">
                            <input
                                type="checkbox"
                                checked={internalFilterColumns.size === 0}
                                on:change={toggleAllColumns}
                            />
                            All columns
                        </label>
                        {#each columns as col}
                            <label class="column-option">
                                <input
                                    type="checkbox"
                                    checked={internalFilterColumns.has(col.key)}
                                    on:change={() => toggleColumn(col.key)}
                                />
                                {col.label}
                            </label>
                        {/each}
                    </div>
                {/if}
            </div>
        </div>
    {/if}
    <div class="table-wrapper" class:expanded-wrapper={expanded}>
        <table>
            <thead>
                <tr>
                    {#if select_mode === "multi"}
                        <th class="checkbox-col">
                            <input
                                type="checkbox"
                                checked={allSelected}
                                {indeterminate}
                                on:click|stopPropagation={toggleAll}
                            />
                        </th>
                    {/if}
                    {#each columns as col}
                        <th
                            on:click={() => col.sortable && handleSort(col.key)}
                            class:sortable={col.sortable}
                        >
                            {col.label}
                            {#if sortKey === col.key}
                                <span>{sortDirection === 1 ? "▲" : "▼"}</span>
                            {/if}
                        </th>
                    {/each}
                    {#if deletable}
                        <th class="actions-col">Actions</th>
                    {/if}
                </tr>
            </thead>
            <tbody>
                {#each paginatedRows as row (row.id)}
                    <tr
                        class:selected={selectedIds.has(row.id)}
                        class:clickable={select_mode !== "none"}
                        on:click={(e) => handleSelect(row, e)}
                    >
                        {#if select_mode === "multi"}
                            <td class="checkbox-col">
                                <input
                                    type="checkbox"
                                    checked={selectedIds.has(row.id)}
                                    readonly
                                    style="pointer-events: none;"
                                />
                            </td>
                        {/if}
                        {#each columns as col}
                            {#if col.selectable}
                                <td class="selectable-col">
                                    <input
                                        type="checkbox"
                                        checked={isCellSelected(row.id, col.key)}
                                        on:click={(e) => toggleCellSelection(row.id, col.key, e)}
                                    />
                                </td>
                            {:else}
                                <td>{row[col.key]}</td>
                            {/if}
                        {/each}
                        {#if deletable}
                            <td class="actions-col">
                                <button
                                    class="delete-btn"
                                    on:click={(e) => handleDelete(row, e)}
                                    title="Delete"
                                >
                                    ✕
                                </button>
                            </td>
                        {/if}
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
    {#if needsPagination}
        <div class="pagination">
            <button
                class="page-btn"
                disabled={currentPage === 0}
                on:click={() => goToPage(currentPage - 1)}
                title="Previous page"
            >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="15 18 9 12 15 6"></polyline>
                </svg>
            </button>
            {#each getVisiblePages(currentPage, totalPages) as page}
                {#if page === -1}
                    <span class="page-ellipsis">...</span>
                {:else}
                    <button
                        class="page-btn"
                        class:active={page === currentPage}
                        on:click={() => goToPage(page)}
                    >
                        {page + 1}
                    </button>
                {/if}
            {/each}
            <button
                class="page-btn"
                disabled={currentPage >= totalPages - 1}
                on:click={() => goToPage(currentPage + 1)}
                title="Next page"
            >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <polyline points="9 18 15 12 9 6"></polyline>
                </svg>
            </button>
            <span class="page-info">
                {currentPage * effectivePageSize + 1}–{Math.min((currentPage + 1) * effectivePageSize, filteredRows.length)} of {filteredRows.length}
            </span>
        </div>
    {/if}
    {#if addable}
        {#if showAddForm}
            <div class="add-form">
                {#each columns as col}
                    <div class="add-field">
                        <span class="add-label">{col.label}</span>
                        <input
                            id="add-{id}-{col.key}"
                            type="text"
                            placeholder={col.label}
                            bind:value={addInputs[col.key]}
                            on:keydown={handleAddKeydown}
                            class="add-input"
                        />
                    </div>
                {/each}
                <div class="add-actions">
                    <button class="add-submit-btn" on:click={handleAdd} title="Add row">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                        </svg>
                    </button>
                    <button class="add-cancel-btn" on:click={cancelAdd} title="Cancel">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>
            </div>
        {:else}
            <button class="add-row-btn" on:click={() => (showAddForm = true)}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="12" y1="5" x2="12" y2="19"></line>
                    <line x1="5" y1="12" x2="19" y2="12"></line>
                </svg>
                Add row
            </button>
        {/if}
    {/if}
</div>

<style>
    .table-container {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        width: 100%;
    }
    .table-container.expanded {
        height: 100%;
    }
    .table-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 0.5rem;
    }
    .table-header-actions {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .row-count {
        font-size: 0.75rem;
        color: var(--text-muted, #64748b);
        white-space: nowrap;
    }
    .table-title {
        font-size: 1rem;
        font-weight: 600;
        margin: 0;
        color: var(--text-primary, #e2e8f0);
    }
    .expand-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: var(--radius-md, 0.5rem);
        border: 1px solid var(--border-strong);
        background: var(--bg-primary, #020617);
        color: var(--text-muted, #64748b);
        cursor: pointer;
        transition: all 0.15s;
        flex-shrink: 0;
    }
    .expand-btn:hover {
        background: var(--bg-hover);
        color: var(--text-primary, #e2e8f0);
        border-color: var(--border-strong);
    }
    .search-container {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
        align-items: center;
    }
    .search-input {
        flex: 1;
        min-width: 0;
        padding: 0.5rem 0.75rem;
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-xl, 1rem);
        font-size: 0.875rem;
        box-sizing: border-box;
        background: var(--bg-primary, #020617);
        color: var(--text-primary, #e2e8f0);
        transition: border-color 0.2s, box-shadow 0.2s;
    }
    .search-input::placeholder {
        color: var(--text-muted, #64748b);
    }
    .search-input:focus {
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
        border-color: var(--border-strong);
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
    .table-wrapper {
        overflow-x: auto;
        overflow-y: auto;
        max-height: 400px;
        border: 1px solid var(--border-color, #1e293b);
        border-radius: var(--radius-md, 0.5rem);
        background: var(--bg-card, #0f172a);
    }
    .table-wrapper.expanded-wrapper {
        max-height: none;
        flex: 1;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.875rem;
    }
    th,
    td {
        padding: 0.75rem 1rem;
        text-align: left;
        border-bottom: 1px solid var(--border-color, #1e293b);
        color: var(--text-primary, #e2e8f0);
    }
    .checkbox-col {
        width: 40px;
        text-align: center;
        padding-right: 0.5rem;
    }
    .selectable-col {
        text-align: center;
        width: 60px;
    }
    .selectable-col input[type="checkbox"] {
        cursor: pointer;
        width: 16px;
        height: 16px;
        accent-color: var(--primary-accent, #e11d48);
    }
    th {
        background-color: var(--bg-primary, #020617);
        font-weight: 600;
        color: var(--text-muted, #64748b);
        position: sticky;
        top: 0;
        z-index: 1;
        text-transform: uppercase;
        font-size: 0.75rem;
        letter-spacing: 0.04em;
    }
    th.sortable {
        cursor: pointer;
        user-select: none;
    }
    th.sortable:hover {
        background-color: var(--bg-hover);
        color: var(--text-primary, #e2e8f0);
    }
    tr.selected {
        background-color: var(--accent-glow, rgba(225, 29, 72, 0.1));
    }
    tr.clickable:hover {
        cursor: pointer;
        background-color: var(--bg-hover);
    }
    tr.selected:hover {
        background-color: rgba(225, 29, 72, 0.15);
    }
    .actions-col {
        width: 60px;
        text-align: center;
    }
    .delete-btn {
        background: none;
        border: 1px solid #ef4444;
        color: #ef4444;
        border-radius: var(--radius-sm, 0.375rem);
        padding: 0.25rem 0.5rem;
        cursor: pointer;
        font-size: 0.75rem;
        line-height: 1;
        transition:
            background-color 0.15s,
            color 0.15s;
    }
    .delete-btn:hover {
        background-color: #ef4444;
        color: #fff;
    }

    /* Pagination */
    .pagination {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.25rem;
        padding: 0.5rem 0;
        flex-wrap: wrap;
    }
    .page-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 32px;
        height: 32px;
        padding: 0 0.5rem;
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-md, 0.5rem);
        background: var(--bg-primary, #020617);
        color: var(--text-secondary, #94a3b8);
        font-size: 0.8125rem;
        cursor: pointer;
        transition: all 0.15s;
    }
    .page-btn:hover:not(:disabled) {
        background: var(--bg-hover);
        border-color: var(--border-strong);
        color: var(--text-primary, #e2e8f0);
    }
    .page-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
    .page-btn.active {
        background: var(--primary-accent, #e11d48);
        color: white;
        border-color: var(--primary-accent, #e11d48);
    }
    .page-ellipsis {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 28px;
        height: 32px;
        color: var(--text-muted, #64748b);
        font-size: 0.875rem;
    }
    .page-info {
        font-size: 0.75rem;
        color: var(--text-muted, #64748b);
        margin-left: 0.5rem;
        white-space: nowrap;
    }

    .add-row-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 0.375rem;
        width: 100%;
        padding: 0.5rem;
        border: 1px dashed var(--border-strong);
        border-radius: var(--radius-md, 0.5rem);
        background: none;
        color: var(--text-muted, #64748b);
        font-size: 0.8125rem;
        cursor: pointer;
        transition: all 0.15s;
    }
    .add-row-btn:hover {
        border-color: var(--primary-accent, #e11d48);
        color: var(--primary-accent, #e11d48);
        background: var(--accent-glow, rgba(225, 29, 72, 0.1));
    }
    .add-form {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0.625rem;
        border: 1px solid var(--border-color, #1e293b);
        border-radius: var(--radius-md, 0.5rem);
        background: var(--bg-card, #0f172a);
    }
    .add-field {
        display: flex;
        align-items: center;
        gap: 0.375rem;
        flex: 1;
        min-width: 0;
    }
    .add-label {
        font-size: 0.75rem;
        font-weight: 500;
        color: var(--text-muted, #64748b);
        white-space: nowrap;
        flex-shrink: 0;
    }
    .add-input {
        flex: 1;
        min-width: 0;
        padding: 0.35rem 0.5rem;
        border: 1px solid var(--border-strong);
        border-radius: var(--radius-sm, 0.375rem);
        font-size: 0.8125rem;
        background: var(--bg-primary, #020617);
        color: var(--text-primary, #e2e8f0);
    }
    .add-input:focus {
        outline: none;
        border-color: var(--primary-accent, #e11d48);
        box-shadow: 0 0 0 2px rgba(225, 29, 72, 0.15);
    }
    .add-actions {
        display: flex;
        gap: 0.25rem;
        flex-shrink: 0;
    }
    .add-submit-btn,
    .add-cancel-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: var(--radius-sm, 0.375rem);
        cursor: pointer;
        transition: all 0.15s;
        padding: 0;
    }
    .add-submit-btn {
        border: 1px solid var(--primary-accent, #e11d48);
        background: var(--primary-accent, #e11d48);
        color: white;
    }
    .add-submit-btn:hover {
        background: var(--primary-accent-hover, #f43f5e);
    }
    .add-cancel-btn {
        border: 1px solid var(--border-strong);
        background: var(--bg-primary, #020617);
        color: var(--text-muted, #64748b);
    }
    .add-cancel-btn:hover {
        background: var(--bg-hover);
        color: var(--text-primary, #e2e8f0);
        border-color: var(--border-strong);
    }
</style>
