<script>
  import { executeAction } from "./ActionExecutor.js";
  import ComponentPreview from "./ComponentPreview.svelte";

  let {
    site = null,
    project = null,
    user = null,
    pageId = null,
    pagePath = "/",
  } = $props();

  /** @type {{ pageId: string; title: string; path?: string; components: any[] }[]} */
  let pages = $state([]);
  /** @type {{ pageId: string; title: string; path?: string; components: any[] } | null} */
  let currentPage = $state(null);
  /** @type {any[]} */
  let components = $state([]);
  // containerWidth/containerHeight removed — layout is now percentage-based

  $effect(() => {
    pages = site?.pages ?? [];

    // Resolve page: by path first, then by pageId, then fallback to first page
    let found = null;
    if (pagePath) {
      found = pages.find((p) => (p.path ?? "/") === pagePath);
    }
    if (!found && pageId) {
      found = pages.find((p) => p.pageId === pageId);
    }
    currentPage = found ?? pages[0] ?? null;
    components = currentPage?.components ?? [];
  });

  function resolveRoute(route) {
    if (!route) return route;
    const prefix = project ? `/${encodeURIComponent(project)}` : "";
    const normalized = route.startsWith("/") ? route : "/" + route;
    return normalized.startsWith(prefix) ? normalized : prefix + normalized;
  }

  function handleButtonClick(comp) {
    if (comp.props?.action) {
      executeAction(comp.props.action, { project, user });
      return;
    }
    // Legacy: plain href without action object
    const href = comp.props?.href;
    if (href) {
      const target = comp.props?.target === "_self" ? "_self" : "_blank";
      window.open(href, target);
    }
  }

  function buildAuthHeaders(props) {
    const headers = {};
    const authType = props?.authType;
    if (authType === "bearer" && props.authCredentials) {
      headers["Authorization"] = `Bearer ${props.authCredentials}`;
    } else if (authType === "basic" && props.authCredentials) {
      headers["Authorization"] = `Basic ${btoa((props.authUsername ?? "") + ":" + props.authCredentials)}`;
    } else if (authType === "api_key" && props.authCredentials) {
      headers[props.authHeader ?? "X-API-Key"] = props.authCredentials;
    }
    return headers;
  }

  async function handleFormSubmit(comp, data) {
    const actions = comp.props?.submitActions ?? [];

    // Fallback: if no actions configured, save internally
    if (!actions.length) {
      try {
        await fetch(
          `/projects/${encodeURIComponent(project)}/dashboard/forms/${encodeURIComponent(comp.id)}/submit`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ fields: data }),
          }
        );
      } catch {}
      return;
    }

    // Execute each action sequentially
    for (const act of actions) {
      try {
        if (act.type === "navigate") {
          const target = act.target ?? "_self";
          const fullRoute = resolveRoute(act.route);
          if (target === "_blank") {
            window.open(fullRoute, "_blank");
          } else {
            window.history.pushState({}, "", fullRoute);
            window.dispatchEvent(new PopStateEvent("popstate"));
          }
        } else if (act.type === "http_request" && act.url) {
          const method = act.method ?? "POST";
          const authHeaders = buildAuthHeaders(act);
          const hasFiles = Object.values(data).some((v) => v instanceof File);

          if (method === "GET") {
            await fetch(act.url, { method: "GET", headers: authHeaders });
          } else if (hasFiles) {
            const fd = new FormData();
            for (const [k, v] of Object.entries(data)) fd.append(k, v);
            await fetch(act.url, { method, headers: authHeaders, body: fd });
          } else {
            await fetch(act.url, {
              method,
              headers: { "Content-Type": "application/json", ...authHeaders },
              body: JSON.stringify(data),
            });
          }
        }
      } catch {
        // Continue to next action even if one fails
      }
    }
  }

  function interpolateRowUrl(template, row) {
    if (!template) return template;
    return template.replace(/\{\{\s*row\.(\w+)\s*\}\}/g, (_, key) =>
      encodeURIComponent(row?.[key] ?? "")
    );
  }

  async function handleTableAction(comp, action, row) {
    try {
      if (action.mode === "api" && action.apiEndpoint) {
        let url = interpolateRowUrl(action.apiEndpoint, row);
        const method = action.apiMethod ?? "POST";
        const authHeaders = buildAuthHeaders(comp.props);

        // Build query params from configured columns
        if (action.queryParams) {
          const qpCols = action.queryParams.split(",").map(s => s.trim()).filter(Boolean);
          const params = new URLSearchParams();
          for (const col of qpCols) {
            if (row[col] !== undefined && row[col] !== null) {
              params.append(col, String(row[col]));
            }
          }
          const qs = params.toString();
          if (qs) {
            url += (url.includes("?") ? "&" : "?") + qs;
          }
        }

        // Build body from configured columns (or entire row if not specified)
        let body = undefined;
        if (method !== "GET" && method !== "DELETE") {
          if (action.bodyParams) {
            const bpCols = action.bodyParams.split(",").map(s => s.trim()).filter(Boolean);
            body = {};
            for (const col of bpCols) {
              if (col in row) body[col] = row[col];
            }
          } else {
            body = row;
          }
        }

        await fetch(url, {
          method,
          headers: { "Content-Type": "application/json", ...authHeaders },
          ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
        });
      } else if (action.action) {
        executeAction(action.action, { project, user, row });
      }
    } catch (err) {
      // Silently fail
    }
  }
</script>

<div class="site-renderer">
  {#if !site || !pages.length}
    <div class="empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>
      </svg>
      <h3>No custom page yet</h3>
      <p>Use the Site Builder to create a landing page for this project.</p>
    </div>
  {:else if !components.length}
    <div class="empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>
      </svg>
      <h3>This page is empty</h3>
      <p>Add components in the Site Builder.</p>
    </div>
  {:else}
    {@const allComps = pages.flatMap(p => p.components ?? [])}
    {@const inferredWidth = allComps.reduce((max, c) => Math.max(max, (c.x ?? 0) + (c.w ?? 160)), 0)}
    {@const refWidth = site?.canvasWidth || Math.max(800, inferredWidth)}
    {@const contentHeight = Math.max(400, ...components.map(c => (c.y ?? 0) + (c.h ?? 44))) + 20}
    <div class="canvas" style="position: relative; width: 100%; min-height: {contentHeight}px;">
      {#each components as comp (comp.id)}
        {@const leftPct = ((comp.x ?? 0) / refWidth) * 100}
        {@const widthPct = ((comp.w ?? 160) / refWidth) * 100}
        <div
          class="component"
          style="position: absolute; left: {leftPct}%; top: {comp.y ?? 0}px; width: {widthPct}%; height: {comp.h ?? 44}px; z-index: {comp.z ?? 0};"
        >
          <ComponentPreview {comp} interactive={true} {project} {user} onbuttonclick={handleButtonClick} onformsubmit={handleFormSubmit} ontableaction={handleTableAction} />
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .site-renderer {
    width: 100%;
    height: 100%;
    padding: var(--spacing-lg);
    box-sizing: border-box;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
  }

  .empty svg {
    opacity: 0.4;
    margin-bottom: var(--spacing-xs);
  }

  .empty h3 {
    margin: 0;
    font-size: 0.95rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .empty p {
    margin: 0;
    font-size: 0.875rem;
  }

  .canvas {
    /* dimensions set inline via scaled values */
  }

  .component {
    box-sizing: border-box;
  }
</style>
