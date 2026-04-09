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
  let activePageIdx = $state(0);
  let rendererEl;
  let sectionEls = [];
  let observer = null;
  let isScrollingTo = false;
  let hoveredDotIdx = $state(-1);

  const scrollable = $derived(pages.length > 1);

  $effect(() => {
    if (project) initTracker(project);
  });

  $effect(() => {
    pages = site?.pages ?? [];
    if (pages.length && pages[0]) {
      trackPageView(pages[0].pageId, pages[0].path ?? "/");
    }
  });

  // Scroll to page by prop changes (path or pageId)
  $effect(() => {
    if (!pages.length) return;
    let targetIdx = resolveTargetIdx();
    scrollToPage(targetIdx);
  });

  function resolveTargetIdx() {
    let targetIdx = 0;
    if (pagePath) {
      const idx = pages.findIndex((p) => (p.path ?? "/") === pagePath);
      if (idx >= 0) targetIdx = idx;
    }
    if (targetIdx === 0 && pageId) {
      const idx = pages.findIndex((p) => p.pageId === pageId);
      if (idx >= 0) targetIdx = idx;
    }
    return targetIdx;
  }

  function scrollToPage(idx) {
    if (idx < 0 || idx >= pages.length) return;
    const el = sectionEls[idx];
    if (el && rendererEl) {
      isScrollingTo = true;
      el.scrollIntoView({ behavior: "smooth", block: "start" });
      setTimeout(() => { isScrollingTo = false; }, 800);
    }
    activePageIdx = idx;
  }

  let scrollSnapTimeout = null;

  function handleScrollEnd() {
    if (!rendererEl || isScrollingTo || !scrollable) return;
    const scrollTop = rendererEl.scrollTop;
    const viewportH = rendererEl.clientHeight;

    for (let i = 0; i < sectionEls.length; i++) {
      const el = sectionEls[i];
      if (!el) continue;
      const sectionTop = el.offsetTop;
      const sectionH = el.offsetHeight;
      if (scrollTop >= sectionTop && scrollTop < sectionTop + sectionH) {
        const progress = (scrollTop - sectionTop) / sectionH;
        let targetIdx;
        if (progress > 0.5 && i < sectionEls.length - 1) {
          targetIdx = i + 1;
        } else {
          targetIdx = i;
        }
        const targetTop = sectionEls[targetIdx]?.offsetTop ?? 0;
        if (Math.abs(scrollTop - targetTop) > 2) {
          scrollToPage(targetIdx);
        } else {
          activePageIdx = targetIdx;
        }
        break;
      }
    }
  }

  // Listen for popstate to handle same-page navigation (when pagePath doesn't change)
  function handlePopStateNav() {
    if (!pages.length) return;
    const targetIdx = resolveTargetIdx();
    scrollToPage(targetIdx);
  }

  onMount(() => {
    if (!rendererEl) return;

    window.addEventListener("popstate", handlePopStateNav);

    // Debounced scroll-end snap
    rendererEl.addEventListener("scroll", () => {
      if (isScrollingTo) return;
      if (scrollSnapTimeout) clearTimeout(scrollSnapTimeout);
      scrollSnapTimeout = setTimeout(handleScrollEnd, 120);
    }, { passive: true });

    observer = new IntersectionObserver(
      (entries) => {
        if (isScrollingTo) return;
        for (const entry of entries) {
          if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
            const idx = Number(entry.target.dataset.pageIdx);
            if (!isNaN(idx)) {
              activePageIdx = idx;
              if (pages[idx]) {
                trackPageView(pages[idx].pageId, pages[idx].path ?? "/");
              }
            }
          }
        }
      },
      { root: rendererEl, threshold: 0.5 },
    );
    // Observe sections after a tick so they exist in the DOM
    setTimeout(() => {
      for (const el of sectionEls) {
        if (el) observer.observe(el);
      }
    }, 100);
  });

  onDestroy(() => {
    destroyTracker();
    if (observer) observer.disconnect();
    if (scrollSnapTimeout) clearTimeout(scrollSnapTimeout);
    window.removeEventListener("popstate", handlePopStateNav);
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

<div class="site-renderer" class:scroll-snap={scrollable} bind:this={rendererEl}>
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
  {:else}
    {@const allComps = pages.flatMap(p => p.components ?? [])}
    {@const inferredWidth = allComps.reduce((max, c) => Math.max(max, (c.x ?? 0) + (c.w ?? 160)), 0)}
    {@const refWidth = site?.canvasWidth || Math.max(800, inferredWidth)}
    {@const isFs = (c) => c.fullscreen || c.type === "hero_form" || c.type === "compliance_form"}

    {#each pages as page, pageIdx}
      {@const pageComps = page.components ?? []}
      {@const hasFs = pageComps.some(c => isFs(c))}
      {@const nonFsComps = pageComps.filter(c => !isFs(c))}
      {@const contentHeight = !hasFs && nonFsComps.length ? Math.max(400, ...nonFsComps.map(c => (c.y ?? 0) + (c.h ?? 44))) + 20 : 0}
      <section
        class="page-section"
        class:page-section-fullscreen={hasFs}
        data-page-idx={pageIdx}
        bind:this={sectionEls[pageIdx]}
      >
        <div class="canvas">
          {#each pageComps as comp (comp.id)}
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
        {#if pageIdx < pages.length - 1}
          <button class="scroll-hint" onclick={() => scrollToPage(pageIdx + 1)} title="Scroll to next section">
            <div class="scroll-hint-capsule">
              <div class="scroll-hint-line"></div>
            </div>
            <span class="scroll-hint-label">{pages[pageIdx + 1]?.title?.toUpperCase() || 'SCROLL DOWN'}</span>
          </button>
        {/if}
      </section>
    {/each}

    {#if scrollable}
      <nav class="page-dots">
        {#each pages as page, idx}
          <div class="page-dot-wrapper"
            onmouseenter={() => hoveredDotIdx = idx}
            onmouseleave={() => hoveredDotIdx = -1}
          >
            <span class="page-dot-label" class:visible={hoveredDotIdx === idx}>{page.title || `Page ${idx + 1}`}</span>
            <button
              class="page-dot"
              class:active={activePageIdx === idx}
              onclick={() => scrollToPage(idx)}
            ></button>
          </div>
        {/each}
      </nav>
    {/if}
  {/if}
</div>

<style>
  .site-renderer {
    position: relative;
    width: 100%;
    height: 100vh;
    box-sizing: border-box;
    overflow-y: auto;
    overflow-x: hidden;
    scroll-behavior: smooth;
  }

  .site-renderer.scroll-snap {
    /* JS handles snap at 50% threshold — no CSS scroll-snap needed */
  }

  .site-renderer :global(.card) {
    border-radius: 0;
  }

  .site-theme-toggle {
    position: fixed;
    top: 12px;
    right: 12px;
    z-index: 60;
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

  .empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-sm);
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
    min-height: 100vh;
    justify-content: center;
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

  /* --- Page sections (full-page scroll snap) --- */
  .page-section {
    position: relative;
    box-sizing: border-box;
  }

  .scroll-snap .page-section {
    min-height: 100vh;
  }

  .page-section:not(.page-section-fullscreen) {
    padding: var(--spacing-lg);
  }

  .page-section-fullscreen {
    overflow: hidden;
  }

  .canvas {
    position: relative;
    width: 100%;
    min-height: 100%;
  }

  .page-section-fullscreen .canvas {
    height: 100vh;
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

  /* --- Page dot indicators --- */
  .page-dots {
    position: fixed;
    right: 1.5rem;
    top: 50%;
    transform: translateY(-50%);
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    z-index: 55;
  }

  .page-dot-wrapper {
    position: relative;
    display: flex;
    align-items: center;
    justify-content: flex-end;
  }

  .page-dot-label {
    position: absolute;
    right: calc(100% + 0.5rem);
    white-space: nowrap;
    font-size: 0.78rem;
    font-weight: 500;
    color: var(--text-primary, #333);
    background: var(--bg-primary, #fff);
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: var(--radius-sm);
    padding: 0.25rem 0.55rem;
    box-shadow: var(--shadow-sm);
    opacity: 0;
    pointer-events: none;
    transition: opacity 0.15s ease;
  }

  .page-dot-label.visible {
    opacity: 1;
  }

  .page-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    border: 2px solid var(--text-secondary, #999);
    background: transparent;
    cursor: pointer;
    padding: 0;
    transition: all 0.3s ease;
  }

  .page-dot:hover {
    border-color: var(--text-primary, #333);
    transform: scale(1.2);
  }

  .page-dot.active {
    background: #dc2626;
    border-color: #dc2626;
    transform: scale(1.3);
  }

  :global([data-theme="dark"]) .page-dot {
    border-color: rgba(255, 255, 255, 0.35);
  }

  :global([data-theme="dark"]) .page-dot:hover {
    border-color: rgba(255, 255, 255, 0.7);
  }

  :global([data-theme="dark"]) .page-dot.active {
    background: #ef4444;
    border-color: #ef4444;
  }

  :global([data-theme="dark"]) .page-dot-label {
    background: #1e293b;
    border-color: rgba(255, 255, 255, 0.1);
    color: #f1f5f9;
  }

  /* --- Scroll-down hint --- */
  .scroll-hint {
    position: absolute;
    bottom: 1.5rem;
    left: 50%;
    transform: translateX(-50%);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.5rem;
    cursor: pointer;
    background: none;
    border: none;
    padding: 0.5rem;
    z-index: 10;
    animation: hintBreath 4s ease-in-out infinite;
  }

  .scroll-hint:hover {
    animation: none;
    opacity: 1;
  }

  .scroll-hint-capsule {
    position: relative;
    width: 22px;
    height: 36px;
    border-radius: 11px;
    border: 1.5px solid var(--text-secondary, #999);
    opacity: 0.5;
    overflow: hidden;
    transition: border-color 0.2s ease, opacity 0.2s ease;
  }

  .scroll-hint:hover .scroll-hint-capsule {
    border-color: var(--primary-accent, #f59e0b);
    opacity: 1;
  }

  .scroll-hint-line {
    position: absolute;
    left: 50%;
    transform: translateX(-50%);
    width: 4px;
    height: 10px;
    border-radius: 2px;
    background: var(--primary-accent, #f59e0b);
    box-shadow: 0 0 6px rgba(245, 158, 11, 0.35);
    animation: scanDown 2s linear infinite;
  }

  .scroll-hint-label {
    font-size: 0.625rem;
    font-weight: 500;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--text-secondary, #999);
    transition: color 0.2s ease;
  }

  .scroll-hint:hover .scroll-hint-label {
    color: var(--text-primary, #333);
  }

  @keyframes scanDown {
    0% { top: 15%; opacity: 0; }
    15% { opacity: 1; }
    85% { opacity: 1; }
    100% { top: 70%; opacity: 0; }
  }

  @keyframes hintBreath {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }

  :global([data-theme="dark"]) .scroll-hint-capsule {
    border-color: rgba(255, 255, 255, 0.25);
  }

  :global([data-theme="dark"]) .scroll-hint:hover .scroll-hint-capsule {
    border-color: var(--primary-accent, #f59e0b);
  }

  :global([data-theme="dark"]) .scroll-hint-label {
    color: rgba(255, 255, 255, 0.4);
  }

  :global([data-theme="dark"]) .scroll-hint:hover .scroll-hint-label {
    color: rgba(255, 255, 255, 0.85);
  }
</style>
