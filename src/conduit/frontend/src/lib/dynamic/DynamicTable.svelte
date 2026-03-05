<script>
    import { createEventDispatcher } from "svelte";

    export let id;
    export let title;
    export let select_mode = "single";
    export let columns = [];
    export let rows = [];
    export let filter = ""; // external search filter text
    export let searchable = false; // enable inbuilt search bar
    export let deletable = false; // enable row deletion
    export let addable = false; // enable adding rows via text input
    export let page_size = 10;
    export let expanded = false; // when true, renders in expanded modal mode

    let addInput = "";

    let internalFilter = "";

    let selectedIds = new Set();

    // Sort state
    let sortKey = "";
    let sortDirection = 1; // 1 for asc, -1 for desc

    // Pagination state
    let currentPage = 0;

    $: effectiveFilter = filter || internalFilter;

    $: filteredRows = rows
        .filter((row) => {
            if (!effectiveFilter) return true;
            return Object.values(row).some((val) =>
                String(val)
                    .toLowerCase()
                    .includes(effectiveFilter.toLowerCase()),
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
        paginatedRows.length > 0 &&
        paginatedRows.every((r) => selectedIds.has(r.id));
    $: indeterminate =
        paginatedRows.length > 0 &&
        !allSelected &&
        paginatedRows.some((r) => selectedIds.has(r.id));

    const dispatch = createEventDispatcher();

    function toggleAll() {
        if (select_mode !== "multi") return;

        if (allSelected) {
            paginatedRows.forEach((r) => selectedIds.delete(r.id));
        } else {
            paginatedRows.forEach((r) => selectedIds.add(r.id));
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
        if (!addInput.trim()) return;
        const key = columns.length > 0 ? columns[0].key : "value";
        const newRow = { id: `added_${Date.now()}`, [key]: addInput.trim() };
        dispatch("add", { id, row: newRow });
        rows = [...rows, newRow];
        addInput = "";
    }

    function handleAddKeydown(e) {
        if (e.key === "Enter") {
            e.preventDefault();
            handleAdd();
        }
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
                placeholder="Search..."
                bind:value={internalFilter}
                class="search-input"
            />
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
                            <td>{row[col.key]}</td>
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
        <div class="add-row">
            <input
                type="text"
                placeholder="Add new entry..."
                bind:value={addInput}
                on:keydown={handleAddKeydown}
                class="add-input"
            />
            <button class="add-btn" on:click={handleAdd} title="Add">+</button>
        </div>
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
        color: #6b7280;
        white-space: nowrap;
    }
    .table-title {
        font-size: 1rem;
        font-weight: 600;
        margin: 0;
    }
    .expand-btn {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 28px;
        height: 28px;
        border-radius: 0.375rem;
        border: 1px solid #d1d5db;
        background: white;
        color: #6b7280;
        cursor: pointer;
        transition: all 0.15s;
        flex-shrink: 0;
    }
    .expand-btn:hover {
        background: #f3f4f6;
        color: #374151;
        border-color: #9ca3af;
    }
    .search-container {
        margin-bottom: 0.5rem;
    }
    .search-input {
        width: 100%;
        padding: 0.5rem;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        font-size: 0.875rem;
        box-sizing: border-box;
    }
    .search-input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 1px #3b82f6;
    }
    .table-wrapper {
        overflow-x: auto;
        overflow-y: auto;
        max-height: 400px;
        border: 1px solid #e5e7eb;
        border-radius: 0.25rem;
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
        border-bottom: 1px solid #e5e7eb;
    }
    .checkbox-col {
        width: 40px;
        text-align: center;
        padding-right: 0.5rem;
    }
    th {
        background-color: #f9fafb;
        font-weight: 600;
        color: #374151;
        position: sticky;
        top: 0;
        z-index: 1;
    }
    th.sortable {
        cursor: pointer;
        user-select: none;
    }
    th.sortable:hover {
        background-color: #f3f4f6;
    }
    tr.selected {
        background-color: #eff6ff;
    }
    tr.clickable:hover {
        cursor: pointer;
        background-color: #f9fafb;
    }
    tr.selected:hover {
        background-color: #dbeafe;
    }
    .actions-col {
        width: 60px;
        text-align: center;
    }
    .delete-btn {
        background: none;
        border: 1px solid #ef4444;
        color: #ef4444;
        border-radius: 0.25rem;
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
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        background: white;
        color: #374151;
        font-size: 0.8125rem;
        cursor: pointer;
        transition: all 0.15s;
    }
    .page-btn:hover:not(:disabled) {
        background: #f3f4f6;
        border-color: #9ca3af;
    }
    .page-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
    .page-btn.active {
        background: #3b82f6;
        color: white;
        border-color: #3b82f6;
    }
    .page-ellipsis {
        display: flex;
        align-items: center;
        justify-content: center;
        min-width: 28px;
        height: 32px;
        color: #9ca3af;
        font-size: 0.875rem;
    }
    .page-info {
        font-size: 0.75rem;
        color: #6b7280;
        margin-left: 0.5rem;
        white-space: nowrap;
    }

    .add-row {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    .add-input {
        flex: 1;
        padding: 0.5rem;
        border: 1px solid #d1d5db;
        border-radius: 0.375rem;
        font-size: 0.875rem;
    }
    .add-input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 1px #3b82f6;
    }
    .add-btn {
        background: none;
        border: 1px solid #3b82f6;
        color: #3b82f6;
        border-radius: 0.375rem;
        padding: 0.5rem 0.75rem;
        cursor: pointer;
        font-size: 1rem;
        font-weight: 600;
        line-height: 1;
        transition:
            background-color 0.15s,
            color 0.15s;
    }
    .add-btn:hover {
        background-color: #3b82f6;
        color: #fff;
    }
</style>
