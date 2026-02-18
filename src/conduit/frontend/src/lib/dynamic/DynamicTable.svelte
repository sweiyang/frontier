<script>
    import { createEventDispatcher } from "svelte";

    export let id;
    export let title;
    export let select_mode = "single";
    export let columns = [];
    export let rows = [];
    export let filter = ""; // external search filter text
    export let searchable = false; // enable inbuilt search bar

    let internalFilter = "";

    let selectedIds = new Set();

    // Sort state
    let sortKey = "";
    let sortDirection = 1; // 1 for asc, -1 for desc

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
            // Deselect all visible
            filteredRows.forEach((r) => selectedIds.delete(r.id));
        } else {
            // Select all visible
            filteredRows.forEach((r) => selectedIds.add(r.id));
        }
        selectedIds = selectedIds; // trigger update
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
            // multi
            if (selectedIds.has(row.id)) {
                selectedIds.delete(row.id);
            } else {
                selectedIds.add(row.id);
            }
        }
        selectedIds = selectedIds; // trigger update
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
</script>

<div class="table-container">
    {#if title}<h3 class="table-title">{title}</h3>{/if}
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
    <div class="table-wrapper">
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
                </tr>
            </thead>
            <tbody>
                {#each filteredRows as row (row.id)}
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
                    </tr>
                {/each}
            </tbody>
        </table>
    </div>
</div>

<style>
    .table-container {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        width: 100%;
    }
    .table-title {
        font-size: 1rem;
        font-weight: 600;
        margin: 0;
        margin: 0;
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
    }
    .search-input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 1px #3b82f6;
    }
    .table-wrapper {
        overflow-x: auto;
        border: 1px solid #e5e7eb;
        border-radius: 0.25rem;
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
</style>
