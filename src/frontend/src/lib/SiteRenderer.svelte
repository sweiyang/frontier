<script>
  import { onMount, onDestroy, untrack } from "svelte";
  import { Sun, Moon } from "lucide-svelte";
  import { executeAction } from "./ActionExecutor.js";
  import ComponentPreview from "./ComponentPreview.svelte";
  import { toggleTheme, getStoredTheme } from "./theme.js";
  import {
    initTracker,
    destroyTracker,
    trackPageView,
    trackButtonClick,
    trackFormSubmit,
    trackTableAction,
  } from "./siteAnalytics.js";

  let {
    site = null,
    project = null,
    user = null,
    pageId = null,
    pagePath = "/",
  } = $props();

  let currentTheme = $state(getStoredTheme());

  function handleToggleTheme() {
    currentTheme = toggleTheme();
  }

  /** @type {{ pageId: string; title: string; path?: string; components: any[] }[]} */
  let pages = $state([]);
  /** @type {{ pageId: string; title: string; path?: string; components: any[] } | null} */
  let currentPage = $state(null);
  /** @type {any[]} */
  let components = $state([]);

  // --- Page transition state ---
  let prevPageId = $state(null);
  let transitionPhase = $state("idle"); // "idle" | "exit" | "enter"
  let transitionTimer = null;
  const TRANSITION_MS = 380;

  $effect(() => {
    if (project) initTracker(project);
  });
  onDestroy(() => {
    destroyTracker();
    if (transitionTimer) clearTimeout(transitionTimer);
  });

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
    const nextPage = found ?? pages[0] ?? null;

    // Read transition state without creating reactive dependency
    const prev = untrack(() => prevPageId);
    const phase = untrack(() => transitionPhase);

    // Slide-and-fade transition when navigating between pages
    if (prev && nextPage && nextPage.pageId !== prev && phase === "idle") {
      transitionPhase = "exit";
      if (transitionTimer) clearTimeout(transitionTimer);
      transitionTimer = setTimeout(() => {
        // Swap to new page content and start enter animation
        currentPage = nextPage;
        components = nextPage?.components ?? [];
        transitionPhase = "enter";
        transitionTimer = setTimeout(() => {
          transitionPhase = "idle";
          transitionTimer = null;
        }, TRANSITION_MS);
      }, TRANSITION_MS);
    } else if (phase === "idle") {
      // Initial load or same page — apply immediately
      currentPage = nextPage;
      components = nextPage?.components ?? [];
    }

    prevPageId = nextPage?.pageId ?? null;

    // Track page view
    if (nextPage) {
      trackPageView(nextPage.pageId, nextPage.path ?? "/");
    }
  });

  function fetchWithTimeout(url, options = {}, timeoutMs = 15000) {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), timeoutMs);
    return fetch(url, { ...options, signal: controller.signal }).finally(() => clearTimeout(id));
  }

  function resolveRoute(route) {
    if (!route) return route;
    const prefix = project ? `/${encodeURIComponent(project)}` : "";
    const normalized = route.startsWith("/") ? route : "/" + route;
    return normalized.startsWith(prefix) ? normalized : prefix + normalized;
  }

  function handleButtonClick(comp) {
    trackButtonClick(comp.id, comp.props?.label);
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
    trackFormSubmit(comp.id);
    const actions = comp.props?.submitActions ?? [];

    // Fallback: if no actions configured, save internally
    if (!actions.length) {
      try {
        // Strip File entries — default path only supports JSON
        const jsonData = {};
        let hasStrippedFiles = false;
        for (const [k, v] of Object.entries(data)) {
          if (v instanceof File || (Array.isArray(v) && v.some(item => item instanceof File))) {
            hasStrippedFiles = true;
          } else {
            jsonData[k] = v;
          }
        }
        if (hasStrippedFiles) {
          console.warn('Form files were stripped — configure an HTTP submit action to send files to an external endpoint.');
        }
        const res = await fetchWithTimeout(
          `/projects/${encodeURIComponent(project)}/dashboard/forms/${encodeURIComponent(comp.id)}/submit`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ fields: jsonData }),
          }
        );
        const text = await res.text();
        return { ok: res.ok, responseText: text };
      } catch (e) {
        console.error('Form submission failed:', e);
        return { ok: false, responseText: e.message || 'Submission failed' };
      }
    }

    // Execute each action sequentially — stop on first HTTP failure
    let lastResponseText = '';
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
          const hasFiles = Object.values(data).some(
            (v) => v instanceof File || (Array.isArray(v) && v.some(item => item instanceof File))
          );

          let res;
          if (method === "GET") {
            res = await fetchWithTimeout(act.url, { method: "GET", headers: authHeaders });
          } else if (hasFiles) {
            const fd = new FormData();
            for (const [k, v] of Object.entries(data)) {
              if (Array.isArray(v)) {
                v.forEach(item => fd.append(k, item));
              } else {
                fd.append(k, v);
              }
            }
            if (act.additionalBodyJson) {
              try {
                const extra = JSON.parse(act.additionalBodyJson);
                for (const [k, v] of Object.entries(extra)) {
                  fd.append(k, typeof v === "object" ? JSON.stringify(v) : String(v));
                }
              } catch (e) {
                console.warn("Invalid additional body JSON:", e);
              }
            }
            res = await fetchWithTimeout(act.url, { method, headers: authHeaders, body: fd });
          } else {
            let bodyData = { ...data };
            if (act.additionalBodyJson) {
              try {
                const extra = JSON.parse(act.additionalBodyJson);
                bodyData = { ...bodyData, ...extra };
              } catch (e) {
                console.warn("Invalid additional body JSON:", e);
              }
            }
            res = await fetchWithTimeout(act.url, {
              method,
              headers: { "Content-Type": "application/json", ...authHeaders },
              body: JSON.stringify(bodyData),
            });
          }

          const text = await res.text();
          if (!res.ok) {
            return { ok: false, responseText: text };
          }
          lastResponseText = text;
        }
      } catch (e) {
        return { ok: false, responseText: e.message || 'Action failed' };
      }
    }
    return { ok: true, responseText: lastResponseText || 'Submitted successfully' };
  }

  function interpolateRowUrl(template, row) {
    if (!template) return template;
    return template.replace(/\{\{\s*row\.(\w+)\s*\}\}/g, (_, key) =>
      encodeURIComponent(row?.[key] ?? "")
    );
  }

  async function handleTableAction(comp, action, row) {
    trackTableAction(comp.id, action?.label || action?.icon);
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

        // Download actions: trigger browser download instead of fetch
        if (action.icon === "download") {
          const a = document.createElement("a");
          a.href = url;
          a.download = "";
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          return;
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

        await fetchWithTimeout(url, {
          method,
          headers: { "Content-Type": "application/json", ...authHeaders },
          ...(body !== undefined ? { body: JSON.stringify(body) } : {}),
        });
      } else if (action.action) {
        executeAction(action.action, { project, user, row });
      }
    } catch (err) {
      console.error('Table action failed:', err);
    }
  }
</script>

<div class="site-renderer" class:transitioning={transitionPhase !== "idle"}>
  <button class="site-theme-toggle" onclick={handleToggleTheme} title="Toggle theme">
    {#if currentTheme === 'dark'}
      <Sun size={16} />
    {:else}
      <Moon size={16} />
    {/if}
  </button>
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
    {@const isFs = (c) => c.fullscreen || c.type === "hero_form"}
    {@const hasFs = components.some(c => isFs(c))}
    {@const nonFsComps = components.filter(c => !isFs(c))}
    {@const contentHeight = !hasFs && nonFsComps.length ? Math.max(400, ...nonFsComps.map(c => (c.y ?? 0) + (c.h ?? 44))) + 20 : 0}
    <div class="canvas">
      <div class="page-transition {transitionPhase === 'exit' ? 'page-exit' : transitionPhase === 'enter' ? 'page-enter' : ''}">
        {#each components as comp (comp.id)}
          {#if isFs(comp)}
            <div class="component component-fullscreen" style="z-index: {comp.z ?? 0};">
              <ComponentPreview {comp} interactive={true} {project} {user} onbuttonclick={handleButtonClick} onformsubmit={handleFormSubmit} ontableaction={handleTableAction} />
            </div>
          {:else}
            {@const leftPct = ((comp.x ?? 0) / refWidth) * 100}
            {@const widthPct = ((comp.w ?? 160) / refWidth) * 100}
            <div
              class="component"
              style="position: absolute; left: {leftPct}%; top: {comp.y ?? 0}px; width: {widthPct}%; height: {comp.h ?? 44}px; z-index: {comp.type === 'back_nav' ? (comp.z ?? 50) : (comp.z ?? 0)};"
            >
              <ComponentPreview {comp} interactive={true} {project} {user} onbuttonclick={handleButtonClick} onformsubmit={handleFormSubmit} ontableaction={handleTableAction} />
            </div>
          {/if}
        {/each}
        {#if contentHeight > 0}
          <div style="position: relative; min-height: {contentHeight}px;"></div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .site-renderer {
    position: relative;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
    overflow-y: auto;
    overflow-x: hidden;
  }

  .site-renderer :global(.card) {
    border-radius: 0;
  }

  .site-theme-toggle {
    position: absolute;
    top: 12px;
    right: 12px;
    z-index: 50;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(0, 0, 0, 0.08);
    border-radius: var(--radius-full);
    color: var(--text-secondary);
    cursor: pointer;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
    opacity: 0.6;
  }

  .site-theme-toggle:hover {
    background: rgba(255, 255, 255, 0.95);
    color: var(--text-primary);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    opacity: 1;
  }

  :global([data-theme="dark"]) .site-theme-toggle {
    background: rgba(15, 23, 42, 0.85);
    border-color: rgba(255, 255, 255, 0.1);
  }

  :global([data-theme="dark"]) .site-theme-toggle:hover {
    background: rgba(30, 41, 59, 0.95);
  }

  .site-renderer.transitioning {
    overflow: hidden;
  }

  .site-renderer:not(:has(.component-fullscreen)) {
    padding: var(--spacing-lg);
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
    position: relative;
    width: 100%;
  }

  .component {
    box-sizing: border-box;
  }

  .component-fullscreen {
    position: relative;
    width: 100%;
    height: 100%;
    box-sizing: border-box;
  }

  .site-renderer:has(.component-fullscreen) {
    overflow: hidden;
  }

  .site-renderer:has(.component-fullscreen) .canvas,
  .site-renderer:has(.component-fullscreen) .page-transition {
    height: 100%;
  }

  /* --- Slide-and-Fade page transitions --- */
  .page-transition {
    width: 100%;
    min-height: 100%;
    will-change: transform, opacity;
  }

  .page-exit {
    animation: pageSlideOut 380ms cubic-bezier(0.4, 0, 0.2, 1) forwards;
    pointer-events: none;
  }

  .page-enter {
    animation: pageSlideIn 380ms cubic-bezier(0.4, 0, 0.2, 1) forwards;
  }

  @keyframes pageSlideOut {
    0% {
      opacity: 1;
      transform: translateX(0) scale(1);
    }
    100% {
      opacity: 0;
      transform: translateX(-60px) scale(0.98);
    }
  }

  @keyframes pageSlideIn {
    0% {
      opacity: 0;
      transform: translateX(60px) scale(0.98);
    }
    100% {
      opacity: 1;
      transform: translateX(0) scale(1);
    }
  }

</style>
