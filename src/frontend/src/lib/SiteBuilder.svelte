<script>
  import { onMount } from "svelte";
  import { authFetch } from "./utils.js";
  import ComponentPreview from "./ComponentPreview.svelte";
  import SiteRenderer from "./SiteRenderer.svelte";
  import AgentManager from "./AgentManager.svelte";

  const GRID = 8;

  let { project, fullPage = false, ondelete = () => {} } = $props();

  let loading = $state(true);
  let saving = $state(false);

  let toasts = $state([]);
  let toastCounter = 0;

  function showToast(message, type = "success") {
    const id = ++toastCounter;
    toasts = [...toasts, { id, message, type }];
    setTimeout(() => {
      toasts = toasts.filter(t => t.id !== id);
    }, 3000);
  }

  /** @type {{ siteId?: string; name: string; pages: { pageId: string; title: string; components: any[] }[] }} */
  let site = $state({
    name: "",
    pages: [{ pageId: "home", title: "Home", path: "/", components: [] }],
  });

  let currentPageIndex = $state(0);
  let selectedId = $state(null);
  let saveTimer = null;
  let dragState = $state(null);
  let resizeState = $state(null);
  let dragAnnouncement = $state("");

  /** @type {typeof site[]} */
  let history = $state([]);
  let historyIndex = $state(-1);

  let previewMode = $state(false);
  let showTableEndpointInfo = $state(false);
  let paletteSearch = $state("");
  let activeCategory = $state("all");
  let canvasEl = $state(null);
  let canvasWidth = $state(800);

  let canvasMinHeight = $derived.by(() => {
    const comps = getCurrentComponents();
    if (comps.length === 0) return 600;
    let maxBottom = 0;
    for (const c of comps) {
      const bottom = (c.y ?? 0) + (c.h ?? 44);
      if (bottom > maxBottom) maxBottom = bottom;
    }
    return Math.max(600, maxBottom + GRID * 4);
  });

  /** @param {Event} e */
  function inputVal(e) {
    const t = e.currentTarget;
    return t && "value" in t ? String(t.value) : "";
  }
  /** @param {Event} e */
  function inputNum(e) {
    return Number(inputVal(e)) || 0;
  }

  const paletteItems = [
    { type: "heading", label: "Heading", category: "text", section: "basic", icon: "heading" },
    { type: "text", label: "Paragraph", category: "text", section: "basic", icon: "text" },
    { type: "button", label: "Button", category: "button", section: "basic", icon: "button" },
    { type: "image", label: "Image", category: "image", section: "basic", icon: "image" },
    { type: "divider", label: "Divider", category: "all", section: "basic", icon: "divider" },
    { type: "spacer", label: "Spacer", category: "all", section: "basic", icon: "spacer" },
    { type: "form", label: "Form", category: "form", section: "advanced", icon: "form" },
    { type: "chat_window", label: "Chat Window", category: "chat", section: "advanced", icon: "chat" },
    { type: "table", label: "Table", category: "data", section: "advanced", icon: "table" },
  ];

  const categories = [
    { id: "all", label: "All" },
    { id: "text", label: "Text" },
    { id: "form", label: "Form" },
    { id: "button", label: "Button" },
    { id: "image", label: "Image" },
    { id: "chat", label: "Chat" },
    { id: "data", label: "Data" },
  ];

  function getFilteredPaletteItems() {
    return paletteItems.filter((item) => {
      const matchesCategory = activeCategory === "all" || item.category === activeCategory || item.category === "all";
      const matchesSearch = !paletteSearch || item.label.toLowerCase().includes(paletteSearch.toLowerCase());
      return matchesCategory && matchesSearch;
    });
  }

  function getGroupedPaletteItems() {
    const filtered = getFilteredPaletteItems();
    const groups = {};
    for (const item of filtered) {
      const section = item.section;
      if (!groups[section]) groups[section] = [];
      groups[section].push(item);
    }
    return groups;
  }

  const TABLE_ACTION_ICONS = [
    { value: "view", label: "View (eye)" },
    { value: "edit", label: "Edit (pencil)" },
    { value: "delete", label: "Delete (trash)" },
    { value: "download", label: "Download" },
    { value: "link", label: "Link (external)" },
  ];

  const FORM_FIELD_TYPES = [
    { value: "section", label: "Collapsible section" },
    { value: "paragraph", label: "Text (paragraph)" },
    { value: "text", label: "Text input" },
    { value: "email", label: "Email" },
    { value: "phone", label: "Phone" },
    { value: "textarea", label: "Text area" },
    { value: "select", label: "Dropdown" },
    { value: "checkbox", label: "Checkbox" },
    { value: "file", label: "File attachment" },
    { value: "links", label: "Links (multi-add)" },
    { value: "user_metadata", label: "User metadata" },
  ];

  const USER_METADATA_KEYS = [
    { value: "username", label: "Username" },
    { value: "display_name", label: "Display name" },
    { value: "email", label: "Email" },
  ];

  function getCurrentPage() {
    const p = site.pages[currentPageIndex];
    return p ? { ...p, components: p.components || [] } : null;
  }

  function setCurrentPageComponents(components) {
    const next = site.pages.map((pg, i) =>
      i === currentPageIndex ? { ...pg, components } : pg
    );
    site = { ...site, pages: next };
  }

  function getCurrentComponents() {
    const page = getCurrentPage();
    return page?.components ?? [];
  }

  function pushHistory() {
    const snapshot = JSON.parse(JSON.stringify(site));
    if (historyIndex < history.length - 1) {
      history = history.slice(0, historyIndex + 1);
    }
    history = [...history, snapshot];
    if (history.length > 50) history = history.slice(-50);
    historyIndex = history.length - 1;
  }

  function undo() {
    if (historyIndex <= 0) return;
    historyIndex--;
    site = JSON.parse(JSON.stringify(history[historyIndex]));
  }

  function redo() {
    if (historyIndex >= history.length - 1) return;
    historyIndex++;
    site = JSON.parse(JSON.stringify(history[historyIndex]));
  }

  function snap(v) {
    return Math.round(v / GRID) * GRID;
  }

  onMount(async () => {
    await loadSite();
  });

  $effect(() => {
    if (typeof window === "undefined") return;
    const onKeyDown = (e) => {
      const tag = document.activeElement?.tagName;
      if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;

      if (e.metaKey || e.ctrlKey) {
        if (e.key === "z") {
          e.preventDefault();
          if (e.shiftKey) redo();
          else undo();
        }
        if (e.key === "d") {
          e.preventDefault();
          duplicateSelected();
        }
      }
      if (e.key === "Delete" || e.key === "Backspace") {
        e.preventDefault();
        removeSelected();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });


  async function loadSite() {
    loading = true;
    try {
      const response = await authFetch(
        `/projects/${encodeURIComponent(project)}/dashboard`
      );
      if (response.ok) {
        const data = await response.json();
        if (data?.site && Array.isArray(data.site.pages) && data.site.pages.length > 0) {
          site = {
            siteId: data.site.siteId,
            name: data.site.name ?? "",
            pages: data.site.pages,
          };
        }
      } else {
        showToast("Failed to load site", "error");
      }
    } catch (e) {
      console.error("Failed to load site:", e);
      showToast("Failed to load site", "error");
    } finally {
      loading = false;
      history = [JSON.parse(JSON.stringify(site))];
      historyIndex = 0;
    }
  }

  function getNextPosition() {
    const comps = getCurrentComponents();
    if (comps.length === 0) return { x: GRID * 2, y: GRID * 2 };
    let maxY = 0;
    for (const c of comps) {
      const bottom = (c.y ?? 0) + (c.h ?? 40);
      if (bottom > maxY) maxY = bottom;
    }
    return { x: GRID * 2, y: maxY + GRID };
  }

  function makeNewComponent(type) {
    const id = crypto.randomUUID?.() ?? String(Date.now());
    const { x, y } = getNextPosition();
    const defaults = {
      heading: {
        w: 400, h: 64,
        props: { text: "Heading", level: "h2", alignment: "left" },
      },
      text: {
        w: 400, h: 80,
        props: { text: "Enter your text here.", alignment: "left" },
      },
      button: {
        w: 200, h: 48,
        props: { label: "Click Me", href: "", variant: "primary", size: "medium" },
      },
      image: {
        w: 400, h: 280,
        props: { src: "", alt: "", objectFit: "cover" },
      },
      divider: {
        w: 400, h: 8,
        props: { style: "solid", color: "var(--border-color)", thickness: 1 },
      },
      spacer: {
        w: 400, h: 40,
        props: { height: 40 },
      },
      form: {
        w: 400,
        h: 320,
        props: {
          fields: [{ id: crypto.randomUUID?.() ?? "f1", name: "email", type: "email", label: "Email", required: true }],
          submitLabel: "Submit",
          submitTo: "",
        },
      },
      chat_window: {
        w: 360,
        h: 480,
        props: { systemPrompt: "", botName: "Assistant", colorTheme: "light", agentId: null },
      },
      table: {
        w: 600,
        h: 320,
        props: {
          dataEndpoint: "",
          dataMethod: "GET",
          dataPath: "data",
          refreshInterval: 0,
          authType: "none",
          authCredentials: "",
          authUsername: "",
          authHeader: "X-API-Key",
          actions: [],
          emptyMessage: "No data found",
          showHeader: true,
        },
      },
    };
    const d = defaults[type] ?? { w: 400, h: 320, props: {} };
    return {
      id,
      type,
      x: snap(x),
      y: snap(y),
      w: d.w,
      h: d.h,
      props: d.props ?? {},
    };
  }

  function addComponent(type) {
    pushHistory();
    const comp = makeNewComponent(type);
    const comps = [...getCurrentComponents(), comp];
    setCurrentPageComponents(comps);
    selectedId = comp.id;
    queueSave();
  }

  function selectComponent(id) {
    selectedId = id;
  }

  function getSelectedComponent() {
    const comps = getCurrentComponents();
    return comps.find((c) => c.id === selectedId) ?? null;
  }

  function updateComponent(id, patch) {
    const comps = getCurrentComponents().map((c) =>
      c.id === id ? { ...c, ...patch } : c
    );
    setCurrentPageComponents(comps);
    queueSave();
  }

  function updateSelectedProps(partial) {
    if (!selectedId) return;
    const comp = getSelectedComponent();
    if (!comp) return;
    updateComponent(selectedId, {
      props: { ...(comp.props || {}), ...partial },
    });
  }

  function addFormField(compId) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "form") return;
    const fields = [...(comp.props?.fields ?? [])];
    fields.push({
      id: crypto.randomUUID?.() ?? "f_" + Date.now(),
      name: "field_" + fields.length,
      type: "text",
      label: "New field",
      required: false,
    });
    updateComponent(compId, { props: { ...(comp.props || {}), fields } });
  }

  function removeFormField(compId, fieldIndex) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "form") return;
    const fields = (comp.props?.fields ?? []).filter((_, i) => i !== fieldIndex);
    updateComponent(compId, { props: { ...(comp.props || {}), fields } });
  }

  function moveFormField(compId, fieldIndex, direction) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "form") return;
    const fields = [...(comp.props?.fields ?? [])];
    const target = fieldIndex + direction;
    if (target < 0 || target >= fields.length) return;
    [fields[fieldIndex], fields[target]] = [fields[target], fields[fieldIndex]];
    updateComponent(compId, { props: { ...(comp.props || {}), fields } });
  }

  function updateFormField(compId, fieldIndex, patch) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "form") return;
    const fields = (comp.props?.fields ?? []).map((f, i) =>
      i === fieldIndex ? { ...f, ...patch } : f
    );
    updateComponent(compId, { props: { ...(comp.props || {}), fields } });
  }

  // --- Form submit action management ---
  function addFormSubmitAction(compId) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "form") return;
    const submitActions = [...(comp.props?.submitActions ?? [])];
    submitActions.push({ id: crypto.randomUUID?.() ?? "sa_" + Date.now(), type: "http_request", method: "POST", url: "", authType: "none", authCredentials: "", authUsername: "", authHeader: "X-API-Key" });
    updateComponent(compId, { props: { ...(comp.props || {}), submitActions } });
  }

  function removeFormSubmitAction(compId, index) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "form") return;
    const submitActions = (comp.props?.submitActions ?? []).filter((_, i) => i !== index);
    updateComponent(compId, { props: { ...(comp.props || {}), submitActions } });
  }

  function moveFormSubmitAction(compId, index, direction) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "form") return;
    const submitActions = [...(comp.props?.submitActions ?? [])];
    const target = index + direction;
    if (target < 0 || target >= submitActions.length) return;
    [submitActions[index], submitActions[target]] = [submitActions[target], submitActions[index]];
    updateComponent(compId, { props: { ...(comp.props || {}), submitActions } });
  }

  function updateFormSubmitAction(compId, index, patch) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "form") return;
    const submitActions = (comp.props?.submitActions ?? []).map((a, i) => i === index ? { ...a, ...patch } : a);
    updateComponent(compId, { props: { ...(comp.props || {}), submitActions } });
  }

  // --- Table action management ---
  function addTableAction(compId) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "table") return;
    const actions = [...(comp.props?.actions ?? [])];
    actions.push({ id: crypto.randomUUID?.() ?? "a_" + Date.now(), icon: "view", label: "View", mode: "action", action: { type: "open_url", config: { url: "" } }, queryParams: "", bodyParams: "" });
    updateComponent(compId, { props: { ...(comp.props || {}), actions } });
  }

  function removeTableAction(compId, index) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "table") return;
    const actions = (comp.props?.actions ?? []).filter((_, i) => i !== index);
    updateComponent(compId, { props: { ...(comp.props || {}), actions } });
  }

  function moveTableAction(compId, index, direction) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "table") return;
    const actions = [...(comp.props?.actions ?? [])];
    const target = index + direction;
    if (target < 0 || target >= actions.length) return;
    [actions[index], actions[target]] = [actions[target], actions[index]];
    updateComponent(compId, { props: { ...(comp.props || {}), actions } });
  }

  function updateTableAction(compId, index, patch) {
    const comp = getCurrentComponents().find((c) => c.id === compId);
    if (!comp || comp.type !== "table") return;
    const actions = (comp.props?.actions ?? []).map((a, i) => i === index ? { ...a, ...patch } : a);
    updateComponent(compId, { props: { ...(comp.props || {}), actions } });
  }

  function bringToFront() {
    if (!selectedId) return;
    const comps = getCurrentComponents();
    const maxZ = Math.max(0, ...comps.map((c) => c.z ?? 0));
    updateComponent(selectedId, { z: maxZ + 1 });
  }

  function sendToBack() {
    if (!selectedId) return;
    const comps = getCurrentComponents();
    const minZ = Math.min(0, ...comps.map((c) => c.z ?? 0));
    updateComponent(selectedId, { z: minZ - 1 });
  }

  function removeSelected() {
    if (!selectedId) return;
    pushHistory();
    const comps = getCurrentComponents().filter((c) => c.id !== selectedId);
    setCurrentPageComponents(comps);
    selectedId = comps.length ? comps[comps.length - 1].id : null;
    queueSave();
  }

  async function handleImageUpload(e, compId) {
    const file = e.currentTarget?.files?.[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await authFetch(
        `/projects/${encodeURIComponent(project)}/dashboard/upload`,
        { method: "POST", body: formData }
      );
      if (res.ok) {
        const data = await res.json();
        if (data.url) {
          const comp = getCurrentComponents().find((c) => c.id === compId);
          if (comp) {
            updateComponent(compId, { props: { ...(comp.props || {}), src: data.url } });
            queueSave();
          }
          showToast("Image uploaded");
        }
      } else {
        showToast("Image upload failed", "error");
      }
    } catch (err) {
      showToast("Image upload failed", "error");
    }
  }

  function duplicateSelected() {
    if (!selectedId) return;
    const comp = getCurrentComponents().find((c) => c.id === selectedId);
    if (!comp) return;
    pushHistory();
    const clone = {
      ...JSON.parse(JSON.stringify(comp)),
      id: crypto.randomUUID(),
      x: (comp.x ?? 0) + 16,
      y: (comp.y ?? 0) + 16,
    };
    setCurrentPageComponents([...getCurrentComponents(), clone]);
    selectedId = clone.id;
    queueSave();
  }

  function onCanvasPointerDown(e, id) {
    if (e.button !== 0) return;
    e.preventDefault();
    const comp = getCurrentComponents().find((c) => c.id === id);
    if (!comp) return;
    const canvas = e.currentTarget.closest(".site-canvas");
    if (!canvas) return;
    selectedId = id;
    const rect = canvas.getBoundingClientRect();
    dragState = {
      id,
      startX: e.clientX,
      startY: e.clientY,
      originX: comp.x ?? 0,
      originY: comp.y ?? 0,
      rectLeft: rect.left,
      rectTop: rect.top,
    };
    dragAnnouncement = `Moving ${comp.type} element`;
    window.addEventListener("pointermove", onCanvasPointerMove);
    window.addEventListener("pointerup", onCanvasPointerUp);
  }

  function onCanvasPointerMove(e) {
    if (!dragState) return;
    e.preventDefault();
    const dx = e.clientX - dragState.startX;
    const dy = e.clientY - dragState.startY;
    const newX = snap(dragState.originX + dx);
    const newY = snap(Math.max(0, dragState.originY + dy));
    const comps = getCurrentComponents().map((c) =>
      c.id === dragState.id ? { ...c, x: newX, y: newY } : c
    );
    setCurrentPageComponents(comps);
  }

  function onCanvasPointerUp() {
    if (dragState) {
      pushHistory();
      dragAnnouncement = "Element placed";
      dragState = null;
      queueSave();
    }
    window.removeEventListener("pointermove", onCanvasPointerMove);
    window.removeEventListener("pointerup", onCanvasPointerUp);
  }

  function onResizeHandleDown(e, id, direction = 'corner') {
    if (e.button !== 0) return;
    e.stopPropagation();
    e.preventDefault();
    const comp = getCurrentComponents().find((c) => c.id === id);
    if (!comp) return;
    resizeState = {
      id,
      startX: e.clientX,
      startY: e.clientY,
      originW: comp.w ?? 160,
      originH: comp.h ?? 44,
      direction,
    };
    window.addEventListener("pointermove", onResizePointerMove);
    window.addEventListener("pointerup", onResizePointerUp);
  }

  function onResizePointerMove(e) {
    if (!resizeState) return;
    e.preventDefault();
    const dw = e.clientX - resizeState.startX;
    const dh = e.clientY - resizeState.startY;
    const dir = resizeState.direction;
    const newW = dir === 'bottom' ? resizeState.originW : Math.max(GRID * 4, resizeState.originW + dw);
    const newH = dir === 'right' ? resizeState.originH : Math.max(GRID * 4, resizeState.originH + dh);
    const comps = getCurrentComponents().map((c) =>
      c.id === resizeState.id ? { ...c, w: snap(newW), h: snap(newH) } : c
    );
    setCurrentPageComponents(comps);
  }

  function onResizePointerUp() {
    if (resizeState) {
      pushHistory();
      resizeState = null;
      queueSave();
    }
    window.removeEventListener("pointermove", onResizePointerMove);
    window.removeEventListener("pointerup", onResizePointerUp);
  }

  function addPage() {
    pushHistory();
    const id = "page_" + Date.now();
    const slug = "page-" + (site.pages.length + 1);
    site = {
      ...site,
      pages: [...site.pages, { pageId: id, title: "New Page", path: "/" + slug, components: [] }],
    };
    currentPageIndex = site.pages.length - 1;
    selectedId = null;
    queueSave();
  }

  function removePage(index) {
    if (site.pages.length <= 1) return;
    pushHistory();
    site = {
      ...site,
      pages: site.pages.filter((_, i) => i !== index),
    };
    if (currentPageIndex >= site.pages.length) currentPageIndex = site.pages.length - 1;
    selectedId = null;
    queueSave();
  }

  function setPageTitle(index, title) {
    const next = site.pages.map((p, i) => (i === index ? { ...p, title } : p));
    site = { ...site, pages: next };
    queueSave();
  }

  function setPagePath(index, path) {
    // Ensure path starts with /
    const normalized = path.startsWith("/") ? path : "/" + path;
    const next = site.pages.map((p, i) => (i === index ? { ...p, path: normalized } : p));
    site = { ...site, pages: next };
    queueSave();
  }

  function queueSave() {
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(saveSite, 500);
  }

  async function saveSite() {
    saving = true;
    try {
      const response = await authFetch(
        `/projects/${encodeURIComponent(project)}/dashboard`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ ...site, canvasWidth: canvasWidth || 800 }),
        }
      );
      if (response.ok) {
        showToast("Site saved successfully");
      } else {
        showToast("Failed to save site", "error");
      }
    } catch (e) {
      console.error("Failed to save site:", e);
      showToast("Failed to save site", "error");
    } finally {
      saving = false;
    }
  }

  async function deleteSite() {
    if (!confirm("Delete this site? This cannot be undone.")) return;
    try {
      const response = await authFetch(
        `/projects/${encodeURIComponent(project)}/dashboard`,
        { method: "DELETE" }
      );
      if (response.ok) {
        showToast("Site deleted");
        ondelete();
      } else {
        showToast("Failed to delete site", "error");
      }
    } catch (e) {
      console.error("Failed to delete site:", e);
      showToast("Failed to delete site", "error");
    }
  }

</script>

<div class="site-builder" class:fullpage={fullPage}>
  <div class="builder-toolbar">
    <div class="toolbar-left">
      <button type="button" class="btn-icon" onclick={() => window.history.back()} title="Back">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 12H5"/><path d="M12 19l-7-7 7-7"/></svg>
      </button>
      <input
        type="text"
        class="site-name-input"
        placeholder="Site name"
        value={site.name}
        oninput={(e) => (site = { ...site, name: inputVal(e) })}
        onblur={queueSave}
      />
    </div>
    <div class="toolbar-center">
      {#if saving}
        <span class="status saving">Saving…</span>
      {:else}
        <span class="status"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"/></svg> Saved</span>
      {/if}
    </div>
    <div class="toolbar-right">
      <button type="button" class="btn-icon" onclick={undo} title="Undo (Cmd+Z)" disabled={historyIndex <= 0}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 7v6h6"/><path d="M21 17a9 9 0 0 0-9-9 9 9 0 0 0-6.69 3L3 13"/></svg>
      </button>
      <button type="button" class="btn-icon" onclick={redo} title="Redo (Cmd+Shift+Z)" disabled={historyIndex >= history.length - 1}>
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 7v6h-6"/><path d="M3 17a9 9 0 0 1 9-9 9 9 0 0 1 6.69 3L21 13"/></svg>
      </button>
      {#if previewMode}
        <button type="button" class="btn-preview active" onclick={() => previewMode = false}>Exit Preview</button>
      {:else}
        <button type="button" class="btn-preview" onclick={() => previewMode = true}>Preview</button>
      {/if}
      <button type="button" class="btn-publish" onclick={saveSite}>Publish</button>
      <button type="button" class="btn-delete-site" onclick={deleteSite} title="Delete site">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="3 6 5 6 21 6" />
          <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
        </svg>
      </button>
    </div>
  </div>

  {#if toasts.length > 0}
    <div class="toast-container">
      {#each toasts as toast (toast.id)}
        <div class="toast toast-{toast.type}">
          <span>{toast.message}</span>
          <button class="toast-close" onclick={() => toasts = toasts.filter(t => t.id !== toast.id)}>&times;</button>
        </div>
      {/each}
    </div>
  {/if}

  {#if loading}
    <div class="builder-loading">
      <div class="builder-spinner" aria-label="Loading site"></div>
      <p class="builder-loading-text">Loading site…</p>
    </div>
  {:else if previewMode}
    <div class="preview-container">
      <SiteRenderer {site} {project} />
    </div>
  {:else}
    <div class="builder-body">
      <div class="builder-column palette">
        <div class="palette-header">Add Elements</div>

        <div class="palette-search-wrap">
          <svg class="palette-search-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><path d="M21 21l-4.35-4.35"/></svg>
          <input
            type="text"
            class="palette-search"
            placeholder="Search elements…"
            value={paletteSearch}
            oninput={(e) => (paletteSearch = inputVal(e))}
          />
        </div>

        <div class="category-tabs">
          {#each categories as cat}
            <button
              type="button"
              class="category-tab"
              class:active={activeCategory === cat.id}
              onclick={() => (activeCategory = cat.id)}
            >{cat.label}</button>
          {/each}
        </div>

        {#each Object.entries(getGroupedPaletteItems()) as [section, items]}
          <div class="palette-section">
            <div class="section-header">{section === "basic" ? "Basic Elements" : "Advanced Elements"}</div>
            <div class="palette-grid">
              {#each items as item}
                <button type="button" class="palette-card" onclick={() => addComponent(item.type)} title={item.label}>
                  <div class="palette-card-preview">
                    {#if item.icon === "heading"}
                      <span class="preview-heading">Aa</span>
                    {:else if item.icon === "text"}
                      <div class="preview-lines">
                        <div class="preview-line" style="width: 80%;"></div>
                        <div class="preview-line" style="width: 60%;"></div>
                        <div class="preview-line" style="width: 70%;"></div>
                      </div>
                    {:else if item.icon === "button"}
                      <div class="preview-btn">Click</div>
                    {:else if item.icon === "image"}
                      <svg class="preview-image-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
                    {:else if item.icon === "divider"}
                      <div class="preview-divider"></div>
                    {:else if item.icon === "spacer"}
                      <span class="preview-spacer">↕</span>
                    {:else if item.icon === "form"}
                      <div class="preview-form">
                        <div class="preview-line" style="width: 90%;"></div>
                        <div class="preview-line" style="width: 90%;"></div>
                        <div class="preview-form-btn"></div>
                      </div>
                    {:else if item.icon === "chat"}
                      <svg class="preview-chat-icon" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                    {:else if item.icon === "table"}
                      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="15" x2="21" y2="15"/><line x1="9" y1="3" x2="9" y2="21"/></svg>
                    {/if}
                  </div>
                  <span class="palette-card-label">{item.label}</span>
                </button>
              {/each}
            </div>
          </div>
        {/each}

        {#if getFilteredPaletteItems().length === 0}
          <p class="hint">No elements match your search.</p>
        {/if}
      </div>

      <div class="builder-column canvas-column" role="application" aria-label="Site builder canvas">
        <!-- Visually hidden live region for drag-and-drop announcements -->
        <div class="sr-only" aria-live="polite" aria-atomic="true">{dragAnnouncement}</div>
        <div class="page-tabs">
          {#each site.pages as page, i}
            <button
              type="button"
              class="page-tab"
              class:active={i === currentPageIndex}
              onclick={() => (currentPageIndex = i)}
              aria-label="Page: {page.title}"
            >
              <div class="page-tab-row">
                <input
                  type="text"
                  class="page-tab-input"
                  value={page.title}
                  oninput={(e) => setPageTitle(i, inputVal(e))}
                  onclick={(e) => e.stopPropagation()}
                />
                {#if site.pages.length > 1}
                  <span
                    class="page-tab-delete"
                    role="button"
                    tabindex="0"
                    onclick={(e) => { e.stopPropagation(); removePage(i); }}
                    onkeydown={(e) => { if (e.key === "Enter" || e.key === " ") { e.stopPropagation(); e.preventDefault(); removePage(i); } }}
                    title="Delete page"
                    aria-label="Delete page"
                  >&times;</span>
                {/if}
              </div>
              <input
                type="text"
                class="page-tab-path"
                value={page.path ?? "/"}
                oninput={(e) => setPagePath(i, inputVal(e))}
                onclick={(e) => e.stopPropagation()}
                placeholder="/path"
                title={"/{project}" + (page.path ?? "/")}
              />
            </button>
          {/each}
          <button type="button" class="page-tab-add" onclick={addPage} title="Add page" aria-label="Add page">+</button>
        </div>

        {#if getCurrentComponents().length === 0}
          <div class="canvas-empty">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="opacity: 0.3;">
              <rect x="3" y="3" width="18" height="18" rx="2"/><path d="M12 8v8"/><path d="M8 12h8"/>
            </svg>
            <p>Click an element from the left panel to add it here.</p>
          </div>
        {:else}
          <div
            bind:this={canvasEl}
            bind:clientWidth={canvasWidth}
            class="site-canvas site-canvas-snap"
            style={fullPage
              ? `position: relative; flex: 1; min-height: ${canvasMinHeight}px; width: 100%; background: var(--bg-secondary); border-radius: var(--radius-lg);`
              : `position: relative; width: 800px; min-height: ${canvasMinHeight}px; background: var(--bg-secondary); border-radius: var(--radius-lg);`}
          >
            {#each getCurrentComponents() as comp (comp.id)}
              <div
                class="canvas-item"
                class:selected={comp.id === selectedId}
                style="position: absolute; left: {comp.x}px; top: {comp.y}px; width: {comp.w}px; height: {comp.h}px; z-index: {comp.z ?? 0};"
                role="button"
                tabindex="0"
                aria-label="{comp.type} element{comp.id === selectedId ? ' (selected)' : ''}"
                aria-grabbed={dragState?.id === comp.id ? 'true' : 'false'}
                onclick={() => selectComponent(comp.id)}
                onkeydown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); selectComponent(comp.id); } }}
                onpointerdown={(e) => onCanvasPointerDown(e, comp.id)}
              >
                <div class="canvas-item-inner">
                  <ComponentPreview {comp} interactive={false} />
                </div>
                <div class="resize-handle-right" onpointerdown={(e) => onResizeHandleDown(e, comp.id, 'right')}></div>
                <div class="resize-handle-bottom" onpointerdown={(e) => onResizeHandleDown(e, comp.id, 'bottom')}></div>
                <div
                  class="resize-handle"
                  onpointerdown={(e) => onResizeHandleDown(e, comp.id, 'corner')}
                ></div>
              </div>
            {/each}
          </div>
        {/if}

        <div class="canvas-actions">
          <button type="button" class="btn-secondary" onclick={bringToFront} disabled={!selectedId} title="Bring to front">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="8" y="2" width="14" height="14" rx="2"/><rect x="2" y="8" width="14" height="14" rx="2" opacity="0.4"/></svg>
          </button>
          <button type="button" class="btn-secondary" onclick={sendToBack} disabled={!selectedId} title="Send to back">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="2" width="14" height="14" rx="2" opacity="0.4"/><rect x="8" y="8" width="14" height="14" rx="2"/></svg>
          </button>
          <button type="button" class="btn-secondary" onclick={duplicateSelected} disabled={!selectedId}>
            Duplicate
          </button>
          <button type="button" class="btn-secondary btn-danger" onclick={removeSelected} disabled={!selectedId}>
            Remove
          </button>
        </div>
      </div>

      <div class="builder-column inspector">
        <div class="section-header">Properties</div>
        {#if !selectedId || !getSelectedComponent()}
          <p class="hint">Select a component to edit.</p>
        {:else}
          {#key selectedId}
            {@const comp = getSelectedComponent()}
            {@const p = comp?.props ?? {}}
            <div class="field-group">
              <div class="field">
                <label for="insp-x-{comp.id}">X</label>
                <input id="insp-x-{comp.id}" type="number" value={comp?.x ?? 0} step={GRID} oninput={(e) => updateComponent(comp.id, { x: snap(inputNum(e)) })} />
              </div>
              <div class="field">
                <label for="insp-y-{comp.id}">Y</label>
                <input id="insp-y-{comp.id}" type="number" value={comp?.y ?? 0} step={GRID} oninput={(e) => updateComponent(comp.id, { y: snap(inputNum(e)) })} />
              </div>
              <div class="field">
                <label for="insp-w-{comp.id}">Width</label>
                <input id="insp-w-{comp.id}" type="number" value={comp?.w ?? 160} step={GRID} oninput={(e) => updateComponent(comp.id, { w: Math.max(GRID * 4, snap(inputNum(e) || 160)) })} />
              </div>
              <div class="field">
                <label for="insp-h-{comp.id}">Height</label>
                <input id="insp-h-{comp.id}" type="number" value={comp?.h ?? 44} step={GRID} oninput={(e) => updateComponent(comp.id, { h: Math.max(GRID * 4, snap(inputNum(e) || 44)) })} />
              </div>
            </div>

            {#if comp?.type === "heading"}
              <div class="field">
                <label for="insp-text-{comp.id}">Text</label>
                <input id="insp-text-{comp.id}" type="text" value={p.text ?? ""} oninput={(e) => updateSelectedProps({ text: inputVal(e) })} placeholder="Heading text" />
              </div>
              <div class="field">
                <label for="insp-level-{comp.id}">Level</label>
                <select id="insp-level-{comp.id}" value={p.level ?? "h2"} oninput={(e) => updateSelectedProps({ level: inputVal(e) })}>
                  <option value="h1">H1</option>
                  <option value="h2">H2</option>
                  <option value="h3">H3</option>
                </select>
              </div>
              <div class="field">
                <label for="insp-align-{comp.id}">Alignment</label>
                <select id="insp-align-{comp.id}" value={p.alignment ?? "left"} oninput={(e) => updateSelectedProps({ alignment: inputVal(e) })}>
                  <option value="left">Left</option>
                  <option value="center">Center</option>
                  <option value="right">Right</option>
                </select>
              </div>
            {:else if comp?.type === "text"}
              <div class="field">
                <label for="insp-text-{comp.id}">Text</label>
                <textarea id="insp-text-{comp.id}" rows="4" value={p.text ?? ""} oninput={(e) => updateSelectedProps({ text: inputVal(e) })} placeholder="Enter text…"></textarea>
              </div>
              <div class="field">
                <label for="insp-align-{comp.id}">Alignment</label>
                <select id="insp-align-{comp.id}" value={p.alignment ?? "left"} oninput={(e) => updateSelectedProps({ alignment: inputVal(e) })}>
                  <option value="left">Left</option>
                  <option value="center">Center</option>
                  <option value="right">Right</option>
                </select>
              </div>
            {:else if comp?.type === "button"}
              <div class="field">
                <label for="insp-label-{comp.id}">Label</label>
                <input id="insp-label-{comp.id}" type="text" value={p.label ?? ""} oninput={(e) => updateSelectedProps({ label: inputVal(e) })} placeholder="Button text" />
              </div>
              <div class="field">
                <label for="insp-action-type-{comp.id}">Action</label>
                <select id="insp-action-type-{comp.id}" value={p.action?.type ?? "open_url"} oninput={(e) => {
                  const type = inputVal(e);
                  updateSelectedProps({ action: { type, config: p.action?.config ?? {} }, href: undefined });
                }}>
                  <option value="open_url">Open Link</option>
                  <option value="navigate">Navigate (SPA)</option>
                  <option value="download">Download File</option>
                  <option value="send_chat_message">Send Chat Message</option>
                </select>
              </div>
              {#if (p.action?.type ?? "open_url") === "open_url"}
                <div class="field">
                  <label for="insp-action-url-{comp.id}">URL</label>
                  <input id="insp-action-url-{comp.id}" type="text" value={p.action?.config?.url ?? p.href ?? ""} oninput={(e) => updateSelectedProps({ action: { type: "open_url", config: { ...p.action?.config, url: inputVal(e) } } })} placeholder="https://…" />
                </div>
                <div class="field">
                  <label for="insp-action-target-{comp.id}">Target</label>
                  <select id="insp-action-target-{comp.id}" value={p.action?.config?.target ?? "_blank"} oninput={(e) => updateSelectedProps({ action: { type: "open_url", config: { ...p.action?.config, target: inputVal(e) } } })}>
                    <option value="_blank">New Tab</option>
                    <option value="_self">Same Tab</option>
                  </select>
                </div>
              {:else if (p.action?.type) === "navigate"}
                <div class="field">
                  <label for="insp-action-route-{comp.id}">Route</label>
                  <input id="insp-action-route-{comp.id}" type="text" value={p.action?.config?.route ?? ""} oninput={(e) => updateSelectedProps({ action: { type: "navigate", config: { route: inputVal(e) } } })} placeholder="/path" />
                </div>
              {:else if (p.action?.type) === "download"}
                <div class="field">
                  <label for="insp-action-dl-url-{comp.id}">File URL</label>
                  <input id="insp-action-dl-url-{comp.id}" type="text" value={p.action?.config?.url ?? ""} oninput={(e) => updateSelectedProps({ action: { type: "download", config: { ...p.action?.config, url: inputVal(e) } } })} placeholder="https://…" />
                </div>
                <div class="field">
                  <label for="insp-action-dl-name-{comp.id}">Filename</label>
                  <input id="insp-action-dl-name-{comp.id}" type="text" value={p.action?.config?.filename ?? ""} oninput={(e) => updateSelectedProps({ action: { type: "download", config: { ...p.action?.config, filename: inputVal(e) } } })} placeholder="file.pdf" />
                </div>
              {:else if (p.action?.type) === "send_chat_message"}
                <div class="field">
                  <label for="insp-action-msg-{comp.id}">Message</label>
                  <textarea id="insp-action-msg-{comp.id}" rows="3" value={p.action?.config?.message ?? ""} oninput={(e) => updateSelectedProps({ action: { type: "send_chat_message", config: { ...p.action?.config, message: inputVal(e) } } })} placeholder="Message to send…"></textarea>
                </div>
              {/if}
              <div class="field">
                <label for="insp-variant-{comp.id}">Variant</label>
                <select id="insp-variant-{comp.id}" value={p.variant ?? "primary"} oninput={(e) => updateSelectedProps({ variant: inputVal(e) })}>
                  <option value="primary">Primary</option>
                  <option value="secondary">Secondary</option>
                  <option value="outline">Outline</option>
                </select>
              </div>
              <div class="field">
                <label for="insp-size-{comp.id}">Size</label>
                <select id="insp-size-{comp.id}" value={p.size ?? "medium"} oninput={(e) => updateSelectedProps({ size: inputVal(e) })}>
                  <option value="small">Small</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                </select>
              </div>
            {:else if comp?.type === "image"}
              <div class="field">
                <label>Upload Image</label>
                <input type="file" accept="image/*" onchange={(e) => handleImageUpload(e, comp.id)} />
              </div>
              <div class="field">
                <label for="insp-src-{comp.id}">Image URL</label>
                <input id="insp-src-{comp.id}" type="text" value={p.src ?? ""} oninput={(e) => updateSelectedProps({ src: inputVal(e) })} placeholder="https://…" />
              </div>
              <div class="field">
                <label for="insp-alt-{comp.id}">Alt text</label>
                <input id="insp-alt-{comp.id}" type="text" value={p.alt ?? ""} oninput={(e) => updateSelectedProps({ alt: inputVal(e) })} placeholder="Image description" />
              </div>
              <div class="field">
                <label for="insp-fit-{comp.id}">Object fit</label>
                <select id="insp-fit-{comp.id}" value={p.objectFit ?? "cover"} oninput={(e) => updateSelectedProps({ objectFit: inputVal(e) })}>
                  <option value="cover">Cover</option>
                  <option value="contain">Contain</option>
                  <option value="fill">Fill</option>
                  <option value="none">None</option>
                </select>
              </div>
            {:else if comp?.type === "divider"}
              <div class="field">
                <label for="insp-style-{comp.id}">Style</label>
                <select id="insp-style-{comp.id}" value={p.style ?? "solid"} oninput={(e) => updateSelectedProps({ style: inputVal(e) })}>
                  <option value="solid">Solid</option>
                  <option value="dashed">Dashed</option>
                  <option value="dotted">Dotted</option>
                </select>
              </div>
              <div class="field">
                <label for="insp-color-{comp.id}">Color</label>
                <input id="insp-color-{comp.id}" type="color" value={p.color ?? "#e5e5e5"} oninput={(e) => updateSelectedProps({ color: inputVal(e) })} title="Divider color" />
              </div>
              <div class="field">
                <label for="insp-thickness-{comp.id}">Thickness (px)</label>
                <input id="insp-thickness-{comp.id}" type="number" value={p.thickness ?? 1} min="1" max="10" oninput={(e) => updateSelectedProps({ thickness: inputNum(e) })} />
              </div>
            {:else if comp?.type === "spacer"}
              <div class="field">
                <label for="insp-height-{comp.id}">Height (px)</label>
                <input id="insp-height-{comp.id}" type="number" value={p.height ?? comp?.h ?? 40} step={GRID} min={GRID} oninput={(e) => { const h = Math.max(GRID, inputNum(e)); updateSelectedProps({ height: h }); updateComponent(comp.id, { h }); }} />
              </div>
            {:else if comp?.type === "form"}
              <div class="field">
                <label for="insp-submitlabel-{comp.id}">Submit label</label>
                <input id="insp-submitlabel-{comp.id}" type="text" value={p.submitLabel ?? "Submit"} oninput={(e) => updateSelectedProps({ submitLabel: inputVal(e) })} />
              </div>

              <!-- On Submit Actions -->
              <div class="form-fields-editor">
                <div class="section-header">On Submit Actions</div>
                {#each (p.submitActions ?? []) as act, ai (act.id ?? "sa" + ai)}
                  <div class="form-field-card">
                    <div class="form-field-card-header">
                      <span class="form-field-card-type">{act.type === "http_request" ? "HTTP" : "Navigate"}</span>
                      <button type="button" class="form-field-move" onclick={() => moveFormSubmitAction(comp.id, ai, -1)} disabled={ai === 0} title="Move up">↑</button>
                      <button type="button" class="form-field-move" onclick={() => moveFormSubmitAction(comp.id, ai, 1)} disabled={ai === (p.submitActions ?? []).length - 1} title="Move down">↓</button>
                      <button type="button" class="form-field-remove" onclick={() => removeFormSubmitAction(comp.id, ai)} title="Remove">×</button>
                    </div>
                    <div class="field">
                      <label for="fsa-type-{comp.id}-{ai}">Type</label>
                      <select id="fsa-type-{comp.id}-{ai}" value={act.type ?? "http_request"} oninput={(e) => updateFormSubmitAction(comp.id, ai, { type: inputVal(e) })}>
                        <option value="http_request">HTTP Request</option>
                        <option value="navigate">Navigate to Page</option>
                      </select>
                    </div>
                    {#if act.type === "navigate"}
                      <div class="field">
                        <label for="fsa-route-{comp.id}-{ai}">Route</label>
                        <input id="fsa-route-{comp.id}-{ai}" type="text" value={act.route ?? ""} oninput={(e) => updateFormSubmitAction(comp.id, ai, { route: inputVal(e) })} placeholder="/path or URL" />
                      </div>
                      <div class="field">
                        <label for="fsa-target-{comp.id}-{ai}">Target</label>
                        <select id="fsa-target-{comp.id}-{ai}" value={act.target ?? "_self"} oninput={(e) => updateFormSubmitAction(comp.id, ai, { target: inputVal(e) })}>
                          <option value="_self">Same tab</option>
                          <option value="_blank">New tab</option>
                        </select>
                      </div>
                    {:else}
                      <div class="field">
                        <label for="fsa-url-{comp.id}-{ai}">URL</label>
                        <input id="fsa-url-{comp.id}-{ai}" type="text" value={act.url ?? ""} oninput={(e) => updateFormSubmitAction(comp.id, ai, { url: inputVal(e) })} placeholder="https://api.example.com/submit" />
                      </div>
                      <div class="field">
                        <label for="fsa-method-{comp.id}-{ai}">Method</label>
                        <select id="fsa-method-{comp.id}-{ai}" value={act.method ?? "POST"} oninput={(e) => updateFormSubmitAction(comp.id, ai, { method: inputVal(e) })}>
                          <option value="POST">POST</option>
                          <option value="PUT">PUT</option>
                          <option value="GET">GET</option>
                        </select>
                      </div>
                      <div class="field">
                        <label for="fsa-auth-{comp.id}-{ai}">Authentication</label>
                        <select id="fsa-auth-{comp.id}-{ai}" value={act.authType ?? "none"} oninput={(e) => updateFormSubmitAction(comp.id, ai, { authType: inputVal(e) })}>
                          <option value="none">None</option>
                          <option value="bearer">Bearer Token</option>
                          <option value="basic">Basic Auth</option>
                          <option value="api_key">API Key</option>
                        </select>
                      </div>
                      {#if act.authType === "bearer"}
                        <div class="field">
                          <label for="fsa-token-{comp.id}-{ai}">Token</label>
                          <input id="fsa-token-{comp.id}-{ai}" type="password" value={act.authCredentials ?? ""} oninput={(e) => updateFormSubmitAction(comp.id, ai, { authCredentials: inputVal(e) })} placeholder="Bearer token" />
                        </div>
                      {:else if act.authType === "basic"}
                        <div class="field">
                          <label for="fsa-user-{comp.id}-{ai}">Username</label>
                          <input id="fsa-user-{comp.id}-{ai}" type="text" value={act.authUsername ?? ""} oninput={(e) => updateFormSubmitAction(comp.id, ai, { authUsername: inputVal(e) })} />
                        </div>
                        <div class="field">
                          <label for="fsa-pass-{comp.id}-{ai}">Password</label>
                          <input id="fsa-pass-{comp.id}-{ai}" type="password" value={act.authCredentials ?? ""} oninput={(e) => updateFormSubmitAction(comp.id, ai, { authCredentials: inputVal(e) })} />
                        </div>
                      {:else if act.authType === "api_key"}
                        <div class="field">
                          <label for="fsa-header-{comp.id}-{ai}">Header name</label>
                          <input id="fsa-header-{comp.id}-{ai}" type="text" value={act.authHeader ?? "X-API-Key"} oninput={(e) => updateFormSubmitAction(comp.id, ai, { authHeader: inputVal(e) })} />
                        </div>
                        <div class="field">
                          <label for="fsa-key-{comp.id}-{ai}">Key</label>
                          <input id="fsa-key-{comp.id}-{ai}" type="password" value={act.authCredentials ?? ""} oninput={(e) => updateFormSubmitAction(comp.id, ai, { authCredentials: inputVal(e) })} />
                        </div>
                      {/if}
                      <div class="field">
                        <label for="fsa-extrabody-{comp.id}-{ai}">Additional body JSON</label>
                        <textarea
                          id="fsa-extrabody-{comp.id}-{ai}"
                          rows="3"
                          value={act.additionalBodyJson ?? ""}
                          oninput={(e) => updateFormSubmitAction(comp.id, ai, { additionalBodyJson: inputVal(e) })}
                          placeholder='&#123;"key": "value"&#125;'
                        ></textarea>
                      </div>
                    {/if}
                  </div>
                {/each}
                <button type="button" class="btn-add-field" onclick={() => addFormSubmitAction(comp.id)}>+ Add action</button>
              </div>

              <div class="form-fields-editor">
                <div class="section-header">Fields</div>
                {#each (p.fields ?? []) as field, fi (field.id ?? field.name ?? "f" + fi)}
                  <div class="form-field-card">
                    <div class="form-field-card-header">
                      <span class="form-field-card-type">{field.type}</span>
                      <button type="button" class="form-field-move" onclick={() => moveFormField(comp.id, fi, -1)} disabled={fi === 0} title="Move up">↑</button>
                      <button type="button" class="form-field-move" onclick={() => moveFormField(comp.id, fi, 1)} disabled={fi === (p.fields ?? []).length - 1} title="Move down">↓</button>
                      <button type="button" class="form-field-remove" onclick={() => removeFormField(comp.id, fi)} title="Remove">×</button>
                    </div>
                    <div class="field">
                      <label for="ff-type-{comp.id}-{fi}">Type</label>
                      <select id="ff-type-{comp.id}-{fi}" value={field.type} oninput={(e) => updateFormField(comp.id, fi, { type: inputVal(e) })}>
                        {#each FORM_FIELD_TYPES as opt}
                          <option value={opt.value}>{opt.label}</option>
                        {/each}
                      </select>
                    </div>
                    {#if field.type !== "paragraph" && field.type !== "section"}
                      <div class="field">
                        <label for="ff-name-{comp.id}-{fi}">Name (key)</label>
                        <input id="ff-name-{comp.id}-{fi}" type="text" value={field.name ?? ""} oninput={(e) => updateFormField(comp.id, fi, { name: inputVal(e) })} placeholder="field_name" />
                      </div>
                    {/if}
                    <div class="field">
                      <label for="ff-label-{comp.id}-{fi}">{field.type === "paragraph" || field.type === "section" ? "Title" : field.type === "paragraph" ? "Content" : "Label"}</label>
                      {#if field.type === "paragraph"}
                        <textarea id="ff-label-{comp.id}-{fi}" rows="2" value={field.label ?? field.content ?? ""} oninput={(e) => updateFormField(comp.id, fi, { label: inputVal(e), content: inputVal(e) })}></textarea>
                      {:else}
                        <input id="ff-label-{comp.id}-{fi}" type="text" value={field.label ?? ""} oninput={(e) => updateFormField(comp.id, fi, { label: inputVal(e) })} placeholder={field.type === "section" ? "Section title" : "Field label"} />
                      {/if}
                    </div>
                    {#if field.type === "section"}
                      <div class="field field-inline">
                        <label><input type="checkbox" checked={field.startCollapsed ?? false} onchange={(e) => updateFormField(comp.id, fi, { startCollapsed: e.currentTarget?.checked ?? false })} /> Start collapsed</label>
                      </div>
                    {/if}
                    {#if field.type !== "paragraph" && field.type !== "checkbox"}
                      <div class="field">
                        <label for="ff-placeholder-{comp.id}-{fi}">Placeholder</label>
                        <input id="ff-placeholder-{comp.id}-{fi}" type="text" value={field.placeholder ?? ""} oninput={(e) => updateFormField(comp.id, fi, { placeholder: inputVal(e) })} />
                      </div>
                    {/if}
                    {#if field.type === "select"}
                      <div class="field">
                        <label for="ff-options-{comp.id}-{fi}">Options (one per line)</label>
                        <textarea id="ff-options-{comp.id}-{fi}" rows="3" value={(field.options ?? []).join("\n")} oninput={(e) => updateFormField(comp.id, fi, { options: inputVal(e).split("\n").map((s) => s.trim()).filter(Boolean) })} placeholder="Option 1&#10;Option 2"></textarea>
                      </div>
                      <div class="field">
                        <label for="ff-default-{comp.id}-{fi}">Default value</label>
                        <select id="ff-default-{comp.id}-{fi}" value={field.defaultValue ?? ''} oninput={(e) => updateFormField(comp.id, fi, { defaultValue: inputVal(e) || undefined })}>
                          <option value="">None</option>
                          {#each (field.options ?? []) as opt}
                            <option value={opt}>{opt}</option>
                          {/each}
                        </select>
                      </div>
                    {:else if field.type === "text" || field.type === "email" || field.type === "phone"}
                      <div class="field">
                        <label for="ff-default-{comp.id}-{fi}">Default value</label>
                        <input id="ff-default-{comp.id}-{fi}" type="text" value={field.defaultValue ?? ""} oninput={(e) => updateFormField(comp.id, fi, { defaultValue: inputVal(e) || undefined })} placeholder="e.g., John Doe" />
                      </div>
                    {:else if field.type === "textarea"}
                      <div class="field">
                        <label for="ff-default-{comp.id}-{fi}">Default value</label>
                        <textarea id="ff-default-{comp.id}-{fi}" rows="2" value={field.defaultValue ?? ""} oninput={(e) => updateFormField(comp.id, fi, { defaultValue: inputVal(e) || undefined })} placeholder="Default text content..."></textarea>
                      </div>
                    {:else if field.type === "checkbox"}
                      <div class="field field-inline">
                        <label><input type="checkbox" checked={field.defaultValue ?? false} onchange={(e) => updateFormField(comp.id, fi, { defaultValue: e.currentTarget?.checked ?? false })} /> Checked by default</label>
                      </div>
                    {:else if field.type === "user_metadata"}
                      <div class="field">
                        <label for="ff-metakey-{comp.id}-{fi}">Metadata key</label>
                        <select id="ff-metakey-{comp.id}-{fi}" value={field.metadataKey ?? "username"} oninput={(e) => updateFormField(comp.id, fi, { metadataKey: inputVal(e) })}>
                          {#each USER_METADATA_KEYS as opt}
                            <option value={opt.value}>{opt.label}</option>
                          {/each}
                        </select>
                      </div>
                      <div class="field field-inline">
                        <label><input type="checkbox" checked={field.editable ?? true} onchange={(e) => updateFormField(comp.id, fi, { editable: e.currentTarget?.checked ?? false })} /> Editable</label>
                      </div>
                    {/if}
                    {#if field.type !== "paragraph"}
                      <div class="field field-inline">
                        <label><input type="checkbox" checked={field.required ?? false} onchange={(e) => updateFormField(comp.id, fi, { required: e.currentTarget?.checked ?? false })} /> Required</label>
                      </div>
                    {/if}
                  </div>
                {/each}
                <button type="button" class="btn-add-field" onclick={() => addFormField(comp.id)}>+ Add field</button>
              </div>
            {:else if comp?.type === "chat_window"}
              <div class="field">
                <label for="insp-botname-{comp.id}">Bot name</label>
                <input id="insp-botname-{comp.id}" type="text" value={p.botName ?? ""} oninput={(e) => updateSelectedProps({ botName: inputVal(e) })} />
              </div>
              <div class="field">
                <label for="insp-systemprompt-{comp.id}">System prompt</label>
                <textarea id="insp-systemprompt-{comp.id}" rows="4" value={p.systemPrompt ?? ""} oninput={(e) => updateSelectedProps({ systemPrompt: inputVal(e) })} placeholder="Instructions for the assistant..."></textarea>
              </div>
              <div class="section-header">Agent Configuration</div>
              <AgentManager
                {project}
                selectedAgentId={p.agentId ?? null}
                onselect={(agentId) => updateSelectedProps({ agentId })}
                compact={true}
              />
            {:else if comp?.type === "table"}
              <!-- Data Source -->
              <div class="section-header">Data Source</div>
              <div class="field">
                <label for="insp-dataendpoint-{comp.id}" class="label-with-action">
                  Endpoint URL
                  <button type="button" class="info-icon-btn" onclick={() => showTableEndpointInfo = !showTableEndpointInfo} title="Show expected formats">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                  </button>
                </label>
                <input id="insp-dataendpoint-{comp.id}" type="text" value={p.dataEndpoint ?? ""} oninput={(e) => updateSelectedProps({ dataEndpoint: inputVal(e) })} placeholder="https://api.example.com/jobs" />
                {#if showTableEndpointInfo}
                  {@const sampleDf = { columns: ["id", "name", "status"], data: [[1, "Job A", "running"]] }}
                  {@const authLine = p.authType === "bearer" ? "Authorization: Bearer <token>\n" : p.authType === "basic" ? "Authorization: Basic <base64>\n" : p.authType === "api_key" ? (p.authHeader ?? "X-API-Key") + ": <key>\n" : ""}
                  <div class="info-popover">
                    <div class="info-popover-title">Expected response (dataframe)</div>
                    <pre class="info-popover-code">{p.dataMethod ?? "GET"} {p.dataEndpoint || "/your-endpoint"}{"\n"}{authLine}Content-Type: application/json{"\n\n"}Response:{"\n"}{JSON.stringify({ [p.dataPath || "data"]: sampleDf }, null, 2)}</pre>
                    {#if (p.actions ?? []).some(a => a.mode === "api")}
                      <div class="info-popover-title">Action payload (API mode)</div>
                      <pre class="info-popover-code">POST /your-action-endpoint{"\n"}Content-Type: application/json{"\n"}{authLine}{"\n"}// Row object sent as body:{"\n"}{JSON.stringify({ id: 1, name: "Job A", status: "running" }, null, 2)}</pre>
                    {/if}
                    <p class="info-popover-note">Columns and rows are derived from the dataframe response.</p>
                  </div>
                {/if}
              </div>
              <div class="field">
                <label for="insp-datamethod-{comp.id}">Method</label>
                <select id="insp-datamethod-{comp.id}" value={p.dataMethod ?? "GET"} oninput={(e) => updateSelectedProps({ dataMethod: inputVal(e) })}>
                  <option value="GET">GET</option>
                  <option value="POST">POST</option>
                </select>
              </div>
              <div class="field">
                <label for="insp-datapath-{comp.id}">JSON path to array</label>
                <input id="insp-datapath-{comp.id}" type="text" value={p.dataPath ?? "data"} oninput={(e) => updateSelectedProps({ dataPath: inputVal(e) })} placeholder="data (or empty for root)" />
              </div>
              <div class="field">
                <label for="insp-refresh-{comp.id}">Refresh interval (seconds, 0=manual)</label>
                <input id="insp-refresh-{comp.id}" type="number" value={p.refreshInterval ?? 0} min="0" oninput={(e) => updateSelectedProps({ refreshInterval: inputNum(e) })} />
              </div>

              <!-- Auth (reuse form pattern) -->
              <div class="section-header">Authentication</div>
              <div class="field">
                <label for="insp-tbl-authtype-{comp.id}">Auth type</label>
                <select id="insp-tbl-authtype-{comp.id}" value={p.authType ?? "none"} oninput={(e) => updateSelectedProps({ authType: inputVal(e) })}>
                  <option value="none">None</option>
                  <option value="bearer">Bearer Token</option>
                  <option value="basic">Basic Auth</option>
                  <option value="api_key">API Key</option>
                </select>
              </div>
              {#if p.authType === "bearer"}
                <div class="field">
                  <label for="insp-tbl-authtoken-{comp.id}">Token</label>
                  <input id="insp-tbl-authtoken-{comp.id}" type="password" value={p.authCredentials ?? ""} oninput={(e) => updateSelectedProps({ authCredentials: inputVal(e) })} placeholder="Bearer token" />
                </div>
              {:else if p.authType === "basic"}
                <div class="field">
                  <label for="insp-tbl-authuser-{comp.id}">Username</label>
                  <input id="insp-tbl-authuser-{comp.id}" type="text" value={p.authUsername ?? ""} oninput={(e) => updateSelectedProps({ authUsername: inputVal(e) })} />
                </div>
                <div class="field">
                  <label for="insp-tbl-authpass-{comp.id}">Password</label>
                  <input id="insp-tbl-authpass-{comp.id}" type="password" value={p.authCredentials ?? ""} oninput={(e) => updateSelectedProps({ authCredentials: inputVal(e) })} />
                </div>
              {:else if p.authType === "api_key"}
                <div class="field">
                  <label for="insp-tbl-authheader-{comp.id}">Header name</label>
                  <input id="insp-tbl-authheader-{comp.id}" type="text" value={p.authHeader ?? "X-API-Key"} oninput={(e) => updateSelectedProps({ authHeader: inputVal(e) })} />
                </div>
                <div class="field">
                  <label for="insp-tbl-authkey-{comp.id}">Key</label>
                  <input id="insp-tbl-authkey-{comp.id}" type="password" value={p.authCredentials ?? ""} oninput={(e) => updateSelectedProps({ authCredentials: inputVal(e) })} />
                </div>
              {/if}

              <!-- Row Actions -->
              <div class="form-fields-editor">
                <div class="section-header">Row Actions</div>
                {#each (p.actions ?? []) as act, ai (act.id ?? "a" + ai)}
                  <div class="form-field-card">
                    <div class="form-field-card-header">
                      <span class="form-field-card-type">{act.label || act.icon}</span>
                      <button type="button" class="form-field-move" onclick={() => moveTableAction(comp.id, ai, -1)} disabled={ai === 0} title="Move up">↑</button>
                      <button type="button" class="form-field-move" onclick={() => moveTableAction(comp.id, ai, 1)} disabled={ai === (p.actions ?? []).length - 1} title="Move down">↓</button>
                      <button type="button" class="form-field-remove" onclick={() => removeTableAction(comp.id, ai)} title="Remove">×</button>
                    </div>
                    <div class="field">
                      <label for="ta-icon-{comp.id}-{ai}">Icon</label>
                      <select id="ta-icon-{comp.id}-{ai}" value={act.icon ?? "view"} oninput={(e) => updateTableAction(comp.id, ai, { icon: inputVal(e) })}>
                        {#each TABLE_ACTION_ICONS as opt}
                          <option value={opt.value}>{opt.label}</option>
                        {/each}
                      </select>
                    </div>
                    <div class="field">
                      <label for="ta-label-{comp.id}-{ai}">Label</label>
                      <input id="ta-label-{comp.id}-{ai}" type="text" value={act.label ?? ""} oninput={(e) => updateTableAction(comp.id, ai, { label: inputVal(e) })} placeholder="Action label" />
                    </div>
                    <div class="field">
                      <label for="ta-mode-{comp.id}-{ai}">Mode</label>
                      <select id="ta-mode-{comp.id}-{ai}" value={act.mode ?? "action"} oninput={(e) => updateTableAction(comp.id, ai, { mode: inputVal(e) })}>
                        <option value="action">Action (navigate/open URL)</option>
                        <option value="api">API call</option>
                      </select>
                    </div>
                    {#if act.mode === "api"}
                      <div class="field">
                        <label for="ta-apiendpoint-{comp.id}-{ai}">API endpoint</label>
                        <input id="ta-apiendpoint-{comp.id}-{ai}" type="text" value={act.apiEndpoint ?? ""} oninput={(e) => updateTableAction(comp.id, ai, { apiEndpoint: inputVal(e) })} placeholder={"/api/jobs/{{row.id}}"} />
                      </div>
                      <div class="field">
                        <label for="ta-apimethod-{comp.id}-{ai}">HTTP method</label>
                        <select id="ta-apimethod-{comp.id}-{ai}" value={act.apiMethod ?? "POST"} oninput={(e) => updateTableAction(comp.id, ai, { apiMethod: inputVal(e) })}>
                          <option value="GET">GET</option>
                          <option value="POST">POST</option>
                          <option value="PUT">PUT</option>
                          <option value="DELETE">DELETE</option>
                        </select>
                      </div>
                      <div class="field">
                        <label for="ta-queryparams-{comp.id}-{ai}" class="label-with-action">
                          Query Params
                          <span class="info-tooltip-wrap">
                            <button type="button" class="info-icon-btn">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                            </button>
                            <span class="info-tooltip">Comma-separated column names to send as URL query parameters</span>
                          </span>
                        </label>
                        <input id="ta-queryparams-{comp.id}-{ai}" type="text" value={act.queryParams ?? ""} placeholder="e.g. id, status" oninput={(e) => updateTableAction(comp.id, ai, { queryParams: inputVal(e) })} />
                      </div>
                      <div class="field">
                        <label for="ta-bodyparams-{comp.id}-{ai}" class="label-with-action">
                          Body Params
                          <span class="info-tooltip-wrap">
                            <button type="button" class="info-icon-btn">
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>
                            </button>
                            <span class="info-tooltip">Comma-separated column names for the request body. Leave empty to send the entire row.</span>
                          </span>
                        </label>
                        <input id="ta-bodyparams-{comp.id}-{ai}" type="text" value={act.bodyParams ?? ""} placeholder="e.g. name, email (empty = entire row)" oninput={(e) => updateTableAction(comp.id, ai, { bodyParams: inputVal(e) })} />
                      </div>
                    {:else}
                      <div class="field">
                        <label for="ta-actiontype-{comp.id}-{ai}">Action type</label>
                        <select id="ta-actiontype-{comp.id}-{ai}" value={act.action?.type ?? "open_url"} oninput={(e) => updateTableAction(comp.id, ai, { action: { type: inputVal(e), config: act.action?.config ?? {} } })}>
                          <option value="open_url">Open URL</option>
                          <option value="navigate">Navigate (SPA)</option>
                          <option value="download">Download</option>
                          <option value="send_chat_message">Send Chat Message</option>
                        </select>
                      </div>
                      <div class="field">
                        <label for="ta-actionurl-{comp.id}-{ai}">URL / route / message</label>
                        <input id="ta-actionurl-{comp.id}-{ai}" type="text" value={act.action?.config?.url ?? act.action?.config?.route ?? act.action?.config?.message ?? ""} oninput={(e) => {
                          const t = act.action?.type ?? "open_url";
                          const key = t === "navigate" ? "route" : t === "send_chat_message" ? "message" : "url";
                          updateTableAction(comp.id, ai, { action: { type: t, config: { [key]: inputVal(e) } } });
                        }} placeholder={"Use {{row.field}} for interpolation"} />
                      </div>
                      {#if (act.action?.type) === "download"}
                        <div class="field">
                          <label for="ta-actionfn-{comp.id}-{ai}">Filename</label>
                          <input id="ta-actionfn-{comp.id}-{ai}" type="text"
                            value={act.action?.config?.filename ?? ""}
                            oninput={(e) => updateTableAction(comp.id, ai, { action: { type: "download", config: { ...act.action?.config, filename: inputVal(e) } } })}
                            placeholder="file.pdf" />
                        </div>
                      {/if}
                    {/if}
                  </div>
                {/each}
                <button type="button" class="btn-add-field" onclick={() => addTableAction(comp.id)}>+ Add action</button>
              </div>

              <!-- Display -->
              <div class="section-header">Display</div>
              <div class="field">
                <label for="insp-emptymsg-{comp.id}">Empty message</label>
                <input id="insp-emptymsg-{comp.id}" type="text" value={p.emptyMessage ?? "No data found"} oninput={(e) => updateSelectedProps({ emptyMessage: inputVal(e) })} />
              </div>
              <div class="field field-inline">
                <label><input type="checkbox" checked={p.showHeader !== false} onchange={(e) => updateSelectedProps({ showHeader: e.currentTarget?.checked ?? true })} /> Show header row</label>
              </div>
            {/if}
          {/key}
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .site-builder {
    display: flex;
    flex-direction: column;
    height: 100%;
    box-sizing: border-box;
  }

  .preview-container {
    flex: 1;
    overflow-y: auto;
    background: var(--bg-primary);
  }

  .builder-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 48px;
    padding: 0 var(--spacing-md);
    border-bottom: 1px solid var(--border-color);
    flex-shrink: 0;
    background: var(--bg-primary);
  }

  .toolbar-left {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .toolbar-center {
    display: flex;
    align-items: center;
  }

  .toolbar-right {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .site-name-input {
    width: 180px;
    padding: 4px 10px;
    font-size: 0.9rem;
    font-weight: 500;
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    background: transparent;
    color: var(--text-primary);
  }

  .site-name-input:hover {
    border-color: var(--border-color);
  }

  .site-name-input:focus {
    border-color: var(--primary-accent);
    outline: none;
    background: var(--bg-primary);
  }

  .btn-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    background: transparent;
    color: var(--text-primary);
    cursor: pointer;
    transition: background 0.12s ease;
  }

  .btn-icon:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.06);
  }

  .btn-icon:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .btn-preview {
    padding: 4px 16px;
    font-size: 0.8rem;
    font-weight: 500;
    border-radius: var(--radius-full);
    border: 1px solid var(--border-color);
    background: transparent;
    color: var(--text-primary);
    cursor: pointer;
    transition: background 0.12s ease;
  }

  .btn-preview:hover {
    background: rgba(255, 255, 255, 0.06);
  }

  .btn-preview.active {
    background: var(--primary-accent);
    color: white;
    border-color: var(--primary-accent);
  }

  .btn-preview.active:hover {
    background: var(--primary-accent-hover);
  }

  .btn-publish {
    padding: 4px 16px;
    font-size: 0.8rem;
    font-weight: 600;
    border-radius: var(--radius-full);
    border: none;
    background: var(--primary-accent);
    color: white;
    cursor: pointer;
    transition: background 0.12s ease;
  }

  .btn-publish:hover {
    background: var(--primary-accent-hover);
  }

  .btn-delete-site {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 4px;
    border-radius: var(--radius-sm);
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.12s ease;
  }

  .btn-delete-site:hover {
    background: rgba(239, 68, 68, 0.1);
    color: #ef4444;
  }

  .status.saving {
    color: var(--primary-accent);
    font-size: 0.8rem;
  }

  .status {
    font-size: 0.8rem;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .toast-container {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 9999;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .toast {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 0.75rem 1rem;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    font-weight: 500;
    color: #fff;
    box-shadow: var(--shadow-md);
    animation: toastSlideIn 0.15s ease-out;
  }

  .toast-success {
    background-color: #16a34a;
  }

  .toast-error {
    background-color: #dc2626;
  }

  .toast-close {
    background: none;
    border: none;
    color: inherit;
    font-size: 1.1rem;
    cursor: pointer;
    opacity: 0.8;
    padding: 0;
    line-height: 1;
  }

  .toast-close:hover {
    opacity: 1;
  }

  @keyframes toastSlideIn {
    from {
      opacity: 0;
      transform: translateX(1rem);
    }
    to {
      opacity: 1;
      transform: translateX(0);
    }
  }

  .builder-loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    flex: 1;
    padding: var(--spacing-xl);
    text-align: center;
    color: var(--text-secondary);
    font-size: 0.875rem;
  }

  .builder-loading-text {
    color: var(--text-secondary);
    font-size: 0.875rem;
    margin: 0;
  }

  .builder-spinner {
    width: 36px;
    height: 36px;
    border: 3px solid var(--border-color);
    border-top-color: var(--primary-accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  .builder-body {
    display: grid;
    grid-template-columns: 220px minmax(0, 1fr) 240px;
    gap: 0;
    flex: 1;
    min-height: 0;
  }

  .builder-column {
    border-right: 1px solid var(--border-color);
    background-color: var(--bg-primary);
    padding: var(--spacing-md);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    overflow-y: auto;
  }

  .builder-column:last-child {
    border-right: none;
  }

  .palette {
    border-right: 1px solid var(--border-color);
  }

  .inspector {
    border-left: 1px solid var(--border-color);
    border-right: none;
  }

  .canvas-column {
    border-right: none;
    border-left: none;
    background: var(--bg-secondary);
    align-items: center;
    padding: var(--spacing-md);
  }

  .palette-header {
    font-family: var(--font-display);
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .palette-search-wrap {
    position: relative;
  }

  .palette-search-icon {
    position: absolute;
    left: 10px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-secondary);
    pointer-events: none;
  }

  .palette-search {
    width: 100%;
    padding: 6px 10px 6px 30px;
    font-size: 0.8rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-full);
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  .palette-search:focus {
    outline: none;
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
  }

  .category-tabs {
    display: flex;
    gap: 4px;
    overflow-x: auto;
    flex-wrap: nowrap;
    padding-bottom: 2px;
  }

  .category-tab {
    padding: 3px 10px;
    font-size: 0.7rem;
    font-weight: 500;
    border-radius: var(--radius-full);
    border: 1px solid var(--border-color);
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.12s ease;
  }

  .category-tab.active {
    background: var(--primary-accent);
    color: white;
    border-color: var(--primary-accent);
  }

  .category-tab:hover:not(.active) {
    background: rgba(255, 255, 255, 0.06);
  }

  .palette-section {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
  }

  .section-header {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .hint {
    margin: 0;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .palette-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
  }

  .palette-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    cursor: pointer;
    overflow: hidden;
    transition: border-color 0.12s ease, box-shadow 0.12s ease;
    padding: 0;
  }

  .palette-card:hover {
    border-color: var(--primary-accent);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  }

  .palette-card-preview {
    width: 100%;
    height: 56px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-secondary);
  }

  .palette-card-label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-primary);
    padding: 4px 0;
  }

  .preview-heading {
    font-family: var(--font-display);
    font-size: 1.3rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .preview-lines {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 0 12px;
    width: 100%;
  }

  .preview-line {
    height: 4px;
    background: var(--border-color);
    border-radius: 2px;
  }

  .preview-btn {
    padding: 4px 14px;
    font-size: 0.65rem;
    font-weight: 600;
    background: var(--primary-accent);
    color: white;
    border-radius: var(--radius-full);
  }

  .preview-image-icon {
    color: var(--text-secondary);
    opacity: 0.6;
  }

  .preview-divider {
    width: 60%;
    height: 2px;
    background: var(--border-color);
    border-radius: 1px;
  }

  .preview-spacer {
    font-size: 1.1rem;
    color: var(--text-secondary);
    opacity: 0.5;
  }

  .preview-form {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 0 12px;
    width: 100%;
    align-items: flex-start;
  }

  .preview-form-btn {
    width: 40%;
    height: 6px;
    background: var(--primary-accent);
    border-radius: 3px;
    margin-top: 2px;
  }

  .preview-chat-icon {
    color: var(--text-secondary);
    opacity: 0.6;
  }

  .site-builder.fullpage .canvas-column {
    align-items: stretch;
    display: flex;
    flex-direction: column;
    min-height: 0;
  }

  .site-builder.fullpage .site-canvas {
    flex: 1;
    min-height: 400px;
  }

  .page-tabs {
    display: flex;
    align-items: stretch;
    gap: var(--spacing-xs);
    flex-wrap: wrap;
    margin-bottom: var(--spacing-sm);
    padding: 0 var(--spacing-sm);
  }

  .page-tab {
    padding: 8px 16px;
    border-radius: var(--radius-md);
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    font-size: 0.85rem;
    cursor: pointer;
    color: var(--text-secondary);
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 100px;
    transition: border-color 0.12s ease, background 0.12s ease;
  }

  .page-tab:hover {
    background: rgba(255, 255, 255, 0.04);
    border-color: var(--text-secondary);
  }

  .page-tab.active {
    border-color: var(--primary-accent);
    color: var(--text-primary);
    background: var(--accent-glow);
    font-weight: 500;
  }

  .page-tab-row {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .page-tab-input {
    width: 100%;
    flex: 1;
    padding: 0;
    border: none;
    background: transparent;
    font-size: inherit;
    color: inherit;
  }

  .page-tab-delete {
    display: none;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    padding: 0;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-size: 1rem;
    line-height: 1;
    cursor: pointer;
    border-radius: var(--radius-sm);
    flex-shrink: 0;
    transition: color 0.12s ease, background 0.12s ease;
  }

  .page-tab:hover .page-tab-delete {
    display: flex;
  }

  .page-tab-delete:hover {
    color: #ef4444;
    background: rgba(239, 68, 68, 0.15);
  }

  .page-tab-path {
    width: 100%;
    padding: 0;
    border: none;
    background: transparent;
    font-size: 0.65rem;
    /* Use text-muted directly instead of opacity: 0.7 on text-secondary for WCAG AA compliance */
    color: var(--text-muted);
    font-family: monospace;
  }

  .page-tab-path:focus {
    color: var(--text-secondary);
  }

  .page-tab-add {
    padding: 8px 14px;
    border-radius: var(--radius-md);
    border: 1px dashed var(--border-color);
    background: transparent;
    font-size: 1rem;
    cursor: pointer;
    color: var(--text-secondary);
  }

  .page-tab-add:hover {
    border-color: var(--primary-accent);
    color: var(--primary-accent);
  }

  .canvas-empty {
    padding: var(--spacing-xl);
    border: 2px dashed var(--border-color);
    border-radius: var(--radius-lg);
    text-align: center;
    color: var(--text-secondary);
    width: 100%;
    max-width: 800px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .site-canvas {
    border: 1px solid var(--border-color);
  }

  .site-canvas-snap {
    background-image:
      linear-gradient(to right, var(--border-color) 1px, transparent 1px),
      linear-gradient(to bottom, var(--border-color) 1px, transparent 1px);
    background-size: 8px 8px;
    background-position: 0 0;
    background-color: var(--bg-secondary);
  }

  .form-fields-editor {
    margin-top: var(--spacing-sm);
  }

  .form-fields-editor .section-header {
    margin-bottom: var(--spacing-xs);
  }

  .form-field-card {
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    padding: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
    background: var(--bg-secondary);
  }

  .form-field-card-header {
    display: flex;
    align-items: center;
    gap: 4px;
    margin-bottom: var(--spacing-xs);
  }

  .form-field-card-type {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-secondary);
    flex: 1;
  }

  .form-field-move,
  .form-field-remove {
    width: 24px;
    height: 24px;
    padding: 0;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    font-size: 0.75rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .form-field-move:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .form-field-remove {
    color: #dc2626;
  }

  .form-field-move:hover:not(:disabled),
  .form-field-remove:hover {
    background: rgba(255, 255, 255, 0.08);
  }

  .btn-add-field {
    width: 100%;
    padding: var(--spacing-sm) var(--spacing-md);
    border-radius: var(--radius-md);
    border: 1px dashed var(--border-color);
    background: transparent;
    font-size: 0.875rem;
    color: var(--text-secondary);
    cursor: pointer;
    transition: border-color 0.12s ease, color 0.12s ease;
  }

  .btn-add-field:hover {
    border-color: var(--primary-accent);
    color: var(--primary-accent);
  }

  .field-inline label {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  .sample-request {
    margin-bottom: var(--spacing-sm);
  }

  .sample-request-code {
    margin: var(--spacing-xs) 0 0;
    padding: var(--spacing-sm);
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    font-size: 0.75rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-all;
    color: var(--text-secondary);
    max-height: 200px;
    overflow-y: auto;
  }

  .label-with-action {
    display: flex;
    align-items: center;
    gap: 4px;
  }

  .info-icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 18px;
    height: 18px;
    padding: 0;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    border-radius: 50%;
    transition: color 0.12s ease, background 0.12s ease;
  }

  .info-icon-btn:hover {
    color: var(--primary-accent);
    background: var(--accent-glow);
  }

  .info-tooltip-wrap {
    position: relative;
    display: inline-flex;
  }

  .info-tooltip {
    display: none;
    position: absolute;
    bottom: calc(100% + 6px);
    left: 50%;
    transform: translateX(-50%);
    background: var(--text-primary);
    color: #fff;
    font-size: 0.75rem;
    font-weight: 400;
    line-height: 1.4;
    padding: 6px 10px;
    border-radius: var(--radius-sm);
    white-space: normal;
    width: 200px;
    text-align: center;
    pointer-events: none;
    z-index: 100;
    box-shadow: var(--shadow-md);
  }

  .info-tooltip-wrap:hover .info-tooltip {
    display: block;
  }

  .info-popover {
    margin-top: var(--spacing-xs);
    padding: var(--spacing-sm);
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
  }

  .info-popover-title {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-secondary);
    margin-bottom: 4px;
    margin-top: 8px;
  }

  .info-popover-title:first-child {
    margin-top: 0;
  }

  .info-popover-code {
    margin: 0;
    padding: var(--spacing-xs) var(--spacing-sm);
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    font-size: 0.7rem;
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-all;
    color: var(--text-secondary);
    max-height: 160px;
    overflow-y: auto;
  }

  .info-popover-note {
    margin: 8px 0 0;
    font-size: 0.7rem;
    color: var(--text-secondary);
    font-style: italic;
  }

  .field-inline input[type="checkbox"] {
    width: auto;
  }

  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }

  .canvas-item {
    cursor: grab;
    box-sizing: border-box;
  }

  .canvas-item:active {
    cursor: grabbing;
  }

  .canvas-item-inner {
    width: 100%;
    height: 100%;
    border-radius: var(--radius-md);
    border: 1px solid transparent;
    background: var(--bg-primary);
    overflow: hidden;
  }

  .canvas-item.selected .canvas-item-inner {
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
  }

  .resize-handle {
    position: absolute;
    right: 2px;
    bottom: 2px;
    width: 12px;
    height: 12px;
    border-radius: 2px;
    background: var(--text-secondary);
    opacity: 0.6;
    cursor: nwse-resize;
  }

  .resize-handle-right {
    position: absolute;
    right: -3px;
    top: 20%;
    width: 6px;
    height: 60%;
    cursor: ew-resize;
    border-radius: 3px;
  }

  .resize-handle-bottom {
    position: absolute;
    bottom: -3px;
    left: 20%;
    width: 60%;
    height: 6px;
    cursor: ns-resize;
    border-radius: 3px;
  }

  .canvas-item.selected .resize-handle-right,
  .canvas-item.selected .resize-handle-bottom {
    background: var(--text-secondary);
    opacity: 0.4;
  }

  .canvas-item.selected .resize-handle-right:hover,
  .canvas-item.selected .resize-handle-bottom:hover {
    opacity: 0.7;
  }

  .canvas-actions {
    display: flex;
    gap: var(--spacing-sm);
    margin-top: var(--spacing-sm);
  }

  .btn-secondary {
    font-size: 0.8rem;
    padding: 6px 16px;
    border-radius: var(--radius-full);
    border: 1px solid var(--border-color);
    background: transparent;
    color: var(--text-primary);
    cursor: pointer;
  }

  .btn-secondary:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.06);
  }

  .btn-secondary:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .btn-danger {
    color: #dc2626;
    border-color: #dc2626;
  }

  .btn-danger:hover:not(:disabled) {
    background: rgba(239, 68, 68, 0.15);
  }

  .inspector .field {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-xs);
    margin-bottom: var(--spacing-sm);
  }

  .field-group {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--spacing-sm);
    margin-bottom: var(--spacing-sm);
  }

  .inspector label {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .inspector input,
  .inspector textarea,
  .inspector select {
    font-size: 0.875rem;
    padding: var(--spacing-xs) var(--spacing-sm);
    border-radius: var(--radius-sm);
    border: 1px solid var(--border-strong);
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .inspector input:focus,
  .inspector textarea:focus,
  .inspector select:focus {
    outline: none;
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
  }

  @media (max-width: 1024px) {
    .builder-body {
      grid-template-columns: 1fr;
    }
  }
  .field-warning {
    display: block;
    margin-top: 0.25rem;
    font-size: 0.75rem;
    color: #dc2626;
  }
</style>
