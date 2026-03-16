<script>
    /** @type {string} */
    export let id;
    /** @type {string} */
    export let title = "";
    /** @type {{ label: string, value: string | number, unit?: string, color?: string, trend?: string }[]} */
    export let stats = [];
    /** @type {'row' | 'grid'} */
    export let layout = "row";

    const colorClass = (color) => {
        if (!color) return "";
        const c = String(color).toLowerCase();
        if (["green", "yellow", "red", "blue", "neutral"].includes(c)) return c;
        return "";
    };

    const trendIcon = (trend) => {
        if (!trend) return null;
        const t = String(trend).toLowerCase();
        if (t === "up") return "↑";
        if (t === "down") return "↓";
        return null;
    };
</script>

<div class="stats-container" data-layout={layout} data-element-id={id}>
    {#if title}
        <h3 class="stats-title">{title}</h3>
    {/if}
    <div class="stats-list">
        {#each stats as stat, i (i)}
            <div class="stat-card {stat.color ? 'colored ' + colorClass(stat.color) : ''}">
                <div class="stat-value-wrap">
                    <span class="stat-value">{stat.value}</span>
                    {#if stat.unit}
                        <span class="stat-unit">{stat.unit}</span>
                    {/if}
                    {#if stat.trend}
                        {@const icon = trendIcon(stat.trend)}
                        {#if icon}
                            <span class="stat-trend" class:up={stat.trend === "up"} class:down={stat.trend === "down"}>{icon}</span>
                        {/if}
                    {/if}
                </div>
                {#if stat.label}
                    <div class="stat-label">{stat.label}</div>
                {/if}
            </div>
        {/each}
    </div>
</div>

<style>
    .stats-container {
        display: flex;
        flex-direction: column;
        gap: 0.75rem;
        width: 100%;
    }
    .stats-title {
        font-size: 0.875rem;
        font-weight: 600;
        color: #374151;
        margin: 0 0 0.25rem 0;
    }
    .stats-list {
        display: flex;
        flex-wrap: wrap;
        gap: 0.75rem;
    }
    .stats-container[data-layout="row"] .stats-list {
        flex-direction: row;
    }
    .stats-container[data-layout="grid"] .stats-list {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
    }
    .stat-card {
        flex: 1;
        min-width: 0;
        padding: 0.75rem 1rem;
        background: #f9fafb;
        border: 1px solid #e5e7eb;
        border-radius: 0.5rem;
        border-left-width: 3px;
    }
    .stat-card.colored.green {
        border-left-color: #10b981;
        background: #ecfdf5;
    }
    .stat-card.colored.yellow {
        border-left-color: #f59e0b;
        background: #fffbeb;
    }
    .stat-card.colored.red {
        border-left-color: #ef4444;
        background: #fef2f2;
    }
    .stat-card.colored.blue {
        border-left-color: #3b82f6;
        background: #eff6ff;
    }
    .stat-card.colored.neutral {
        border-left-color: #6b7280;
        background: #f3f4f6;
    }
    .stat-value-wrap {
        display: flex;
        align-items: baseline;
        gap: 0.25rem;
        flex-wrap: wrap;
    }
    .stat-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #111827;
        font-variant-numeric: tabular-nums;
    }
    .stat-card.colored.green .stat-value { color: #047857; }
    .stat-card.colored.yellow .stat-value { color: #b45309; }
    .stat-card.colored.red .stat-value { color: #b91c1c; }
    .stat-card.colored.blue .stat-value { color: #1d4ed8; }
    .stat-card.colored.neutral .stat-value { color: #374151; }
    .stat-unit {
        font-size: 0.875rem;
        font-weight: 500;
        color: #6b7280;
    }
    .stat-trend {
        font-size: 0.875rem;
        font-weight: 600;
    }
    .stat-trend.up { color: #10b981; }
    .stat-trend.down { color: #ef4444; }
    .stat-label {
        font-size: 0.75rem;
        color: #6b7280;
        margin-top: 0.25rem;
    }
</style>
