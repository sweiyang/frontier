<script>
    /** @type {string} */
    export let id;
    /** @type {string} */
    export let title = "";
    /** @type {{ label: string, color?: string, icon?: string }[]} */
    export let items = [];
</script>

<div class="status-container" data-element-id={id}>
    {#if title}
        <h3 class="status-title">{title}</h3>
    {/if}
    <div class="status-list">
        {#each items as item, i (i)}
            <span class="status-pill {item.color ? item.color : 'neutral'}">
                {#if item.icon}<span class="status-icon">{item.icon}</span>{/if}
                {item.label}
            </span>
        {/each}
    </div>
</div>

<style>
    .status-container {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        width: 100%;
    }
    .status-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #374151;
        margin: 0;
    }
    .status-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
    }
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
        padding: 0.35rem 0.85rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.01em;
        white-space: nowrap;
        line-height: 1.4;
    }
    .status-icon {
        font-size: 0.85rem;
    }

    /* Color variants */
    .status-pill.yellow {
        background: #fbbf24;
        color: #1c1917;
    }
    .status-pill.green {
        background: #86efac;
        color: #14532d;
    }
    .status-pill.red {
        background: #fca5a5;
        color: #7f1d1d;
    }
    .status-pill.blue {
        background: #93c5fd;
        color: #1e3a5f;
    }
    .status-pill.purple {
        background: #c4b5fd;
        color: #3b0764;
    }
    .status-pill.orange {
        background: #fdba74;
        color: #431407;
    }
    .status-pill.neutral {
        background: #e5e7eb;
        color: #374151;
    }
</style>
