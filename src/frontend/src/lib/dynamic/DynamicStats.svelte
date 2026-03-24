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
        if (t === "up") return "\u2191";
        if (t === "down") return "\u2193";
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
        font-size: 0.8125rem;
        font-weight: 600;
        color: var(--text-secondary, #94a3b8);
        margin: 0 0 0.25rem 0;
        text-transform: uppercase;
        letter-spacing: 0.04em;
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
        padding: 0.875rem 1rem;
        background: var(--bg-card, #0f172a);
        border: 1px solid var(--border-color, #1e293b);
        border-radius: var(--radius-2xl, 1.5rem);
        border-left-width: 3px;
    }
    .stat-card.colored.green {
        border-left-color: #10b981;
        background: rgba(16, 185, 129, 0.08);
    }
    .stat-card.colored.yellow {
        border-left-color: #f59e0b;
        background: rgba(245, 158, 11, 0.08);
    }
    .stat-card.colored.red {
        border-left-color: #ef4444;
        background: rgba(239, 68, 68, 0.08);
    }
    .stat-card.colored.blue {
        border-left-color: #3b82f6;
        background: rgba(59, 130, 246, 0.08);
    }
    .stat-card.colored.neutral {
        border-left-color: #64748b;
        background: rgba(100, 116, 139, 0.08);
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
        color: var(--text-primary, #e2e8f0);
        font-variant-numeric: tabular-nums;
    }
    .stat-card.colored.green .stat-value { color: #34d399; }
    .stat-card.colored.yellow .stat-value { color: #fbbf24; }
    .stat-card.colored.red .stat-value { color: #f87171; }
    .stat-card.colored.blue .stat-value { color: #60a5fa; }
    .stat-card.colored.neutral .stat-value { color: #94a3b8; }
    .stat-unit {
        font-size: 0.875rem;
        font-weight: 500;
        color: var(--text-muted, #64748b);
    }
    .stat-trend {
        font-size: 0.875rem;
        font-weight: 600;
    }
    .stat-trend.up { color: #34d399; }
    .stat-trend.down { color: #f87171; }
    .stat-label {
        font-size: 0.75rem;
        color: var(--text-muted, #64748b);
        margin-top: 0.25rem;
    }
</style>
