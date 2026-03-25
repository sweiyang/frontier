<script>
  import ChatArea from "./ChatArea.svelte";

  let {
    comp,
    interactive = true,
    project = null,
    user = null,
    onbuttonclick = null,
    onformsubmit = null,
    ontableaction = null,
  } = $props();

  let formSuccess = $state(false);
  /** @type {Record<string, File[]>} */
  let fileFields = $state({});
  /** @type {Record<string, boolean>} */
  let dragOver = $state({});
  /** @type {Record<string, boolean>} - track expanded/collapsed state of sections */
  let expandedSections = $state({});
  const p = $derived(comp.props || {});

  /**
   * Groups form fields into sections.
   * Returns an array where each element is either a field or a section object
   * containing grouped fields.
   */
  function groupFieldsBySection(fields) {
    if (!fields || fields.length === 0) return [];
    const result = [];
    let currentSection = null;
    let currentSectionFields = [];

    for (const field of fields) {
      if (field.type === "section") {
        // If we have accumulated fields, save them to the current section
        if (currentSectionFields.length > 0 && currentSection) {
          currentSection.fields = currentSectionFields;
          result.push(currentSection);
          currentSectionFields = [];
        }
        // Create new section
        currentSection = { ...field, fields: [] };
        // Initialize expanded state: if startCollapsed is true, start collapsed (false), otherwise expanded (true)
        const sectionId = field.id ?? field.name ?? `section_${result.length}`;
        if (!(sectionId in expandedSections)) {
          expandedSections[sectionId] = !field.startCollapsed;
        }
      } else {
        // Regular field - add to current section or to top-level
        if (currentSection) {
          currentSectionFields.push(field);
        } else {
          result.push(field);
        }
      }
    }

    // Don't forget the last section
    if (currentSection) {
      currentSection.fields = currentSectionFields;
      result.push(currentSection);
    }

    return result;
  }

  function toggleSection(sectionId) {
    expandedSections[sectionId] = !expandedSections[sectionId];
  }

  // Table data fetching
  let tableData = $state([]);
  let tableColumns = $state([]);
  let tableLoading = $state(false);
  let tableError = $state("");
  let tableRetryCount = $state(0);
  const TABLE_MAX_RETRIES = 3;

  function buildTableAuthHeaders(props) {
    const headers = {};
    if (props?.authType === "bearer" && props.authCredentials) {
      headers["Authorization"] = `Bearer ${props.authCredentials}`;
    } else if (props?.authType === "basic" && props.authCredentials) {
      headers["Authorization"] = `Basic ${btoa((props.authUsername ?? "") + ":" + props.authCredentials)}`;
    } else if (props?.authType === "api_key" && props.authCredentials) {
      headers[props.authHeader ?? "X-API-Key"] = props.authCredentials;
    }
    return headers;
  }

  function resolveDataPath(obj, path) {
    if (!path) return obj;
    return path.split(".").reduce((o, k) => o?.[k], obj);
  }

  async function fetchTableData(isRetry = false) {
    const endpoint = comp.props?.dataEndpoint;
    if (!endpoint) { tableData = []; tableColumns = []; return; }
    if (isRetry) {
      tableRetryCount += 1;
    } else {
      tableRetryCount = 0;
    }
    tableLoading = true;
    tableError = "";
    try {
      const method = comp.props?.dataMethod ?? "GET";
      const res = await fetch(endpoint, {
        method,
        headers: { "Content-Type": "application/json", ...buildTableAuthHeaders(comp.props) },
      });
      if (!res.ok) { tableError = `Error ${res.status}`; tableData = []; tableColumns = []; return; }
      const json = await res.json();
      const df = resolveDataPath(json, comp.props?.dataPath ?? "data");

      if (!df || !Array.isArray(df.columns) || !Array.isArray(df.data)) {
        tableError = "Invalid dataframe format";
        tableData = [];
        tableColumns = [];
        return;
      }

      tableColumns = df.columns.map((col) => ({ key: col, label: col }));
      tableData = df.data.map((row) =>
        Object.fromEntries(df.columns.map((col, i) => [col, row[i] ?? null]))
      );
    } catch (err) {
      tableError = "Failed to fetch data";
      tableData = [];
      tableColumns = [];
    } finally {
      tableLoading = false;
    }
  }

  $effect(() => {
    if (comp.type !== "table" || !interactive) return;
    fetchTableData();
    const interval = comp.props?.refreshInterval;
    if (interval && interval > 0) {
      const timer = setInterval(fetchTableData, interval * 1000);
      return () => clearInterval(timer);
    }
  });

  function getActionIconSvg(icon) {
    const attrs = 'width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"';
    switch (icon) {
      case "view": return `<svg ${attrs}><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>`;
      case "edit": return `<svg ${attrs}><path d="M17 3a2.85 2.85 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/></svg>`;
      case "delete": return `<svg ${attrs}><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>`;
      case "download": return `<svg ${attrs}><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>`;
      case "link": return `<svg ${attrs}><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`;
      default: return `<svg ${attrs}><circle cx="12" cy="12" r="1"/></svg>`;
    }
  }

  function fileFieldKey(field, fi) {
    return field.name ?? field.id ?? `file_${fi}`;
  }

  let linkFields = $state({});

  function linkFieldKey(field, fallback) {
    return field.name ?? field.id ?? `link_${fallback}`;
  }

  function getLinks(key) {
    return linkFields[key]?.length ? linkFields[key] : [''];
  }

  function addLink(key) {
    linkFields[key] = [...getLinks(key), ''];
  }

  function removeLink(key, index) {
    const filtered = getLinks(key).filter((_, i) => i !== index);
    linkFields[key] = filtered.length ? filtered : [''];
  }

  function updateLink(key, index, value) {
    const arr = [...getLinks(key)];
    arr[index] = value;
    linkFields[key] = arr;
  }

  function handleFileDrop(e, key) {
    e.preventDefault();
    dragOver[key] = false;
    const dt = e.dataTransfer;
    if (!dt?.files?.length) return;
    const existing = fileFields[key] ?? [];
    fileFields[key] = [...existing, ...Array.from(dt.files)];
  }

  function handleFileSelect(e, key) {
    const input = e.currentTarget;
    if (!input.files?.length) return;
    const existing = fileFields[key] ?? [];
    fileFields[key] = [...existing, ...Array.from(input.files)];
    input.value = "";
  }

  function removeFile(key, index) {
    fileFields[key] = (fileFields[key] ?? []).filter((_, i) => i !== index);
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  function collectFormData(formEl) {
    const data = {};
    const fd = new FormData(formEl);
    for (const [key, value] of fd.entries()) {
      if (value instanceof File && value.size > 0) {
        data[key] = value;
      } else if (!(value instanceof File)) {
        data[key] = value;
      }
    }
    // Merge drag-and-drop files
    for (const [key, files] of Object.entries(fileFields)) {
      if (files.length === 1) {
        data[key] = files[0];
      } else if (files.length > 1) {
        data[key] = files;
      }
    }
    // Merge link fields
    for (const [key, links] of Object.entries(linkFields)) {
      const filtered = (links ?? []).filter(v => v.trim());
      if (filtered.length) {
        data[key] = filtered;
      }
    }
    return data;
  }
</script>

<div class="component-preview" class:non-interactive={!interactive}>
  {#if comp.type === "heading"}
    <div class="card heading-card" style="text-align: {p.alignment ?? 'left'};">
      {#if p.level === "h1"}
        <h1>{p.text ?? "Heading"}</h1>
      {:else if p.level === "h3"}
        <h3>{p.text ?? "Heading"}</h3>
      {:else}
        <h2>{p.text ?? "Heading"}</h2>
      {/if}
    </div>
  {:else if comp.type === "text"}
    <div class="card text-card" style="text-align: {p.alignment ?? 'left'};">
      <p style="white-space: pre-wrap;">{p.text ?? "Text"}</p>
    </div>
  {:else if comp.type === "image"}
    <div class="card image-card">
      {#if p.src}
        <img src={p.src} alt={p.alt ?? ""} style="width: 100%; height: 100%; object-fit: {p.objectFit ?? 'cover'}; border-radius: var(--radius-md);" />
      {:else}
        <div class="image-placeholder">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="M21 15l-5-5L5 21"/></svg>
        </div>
      {/if}
    </div>
  {:else if comp.type === "divider"}
    <div class="card divider-card">
      <hr style="border: none; border-top: {p.thickness ?? 1}px {p.style ?? 'solid'} {p.color ?? 'var(--border-color)'}; width: 100%;" />
    </div>
  {:else if comp.type === "spacer"}
    <div style="width: 100%; height: 100%;"></div>
  {:else if comp.type === "button"}
    <div class="card button-card">
      <button
        type="button"
        class="btn-variant-{p.variant ?? 'primary'}"
        onclick={() => onbuttonclick?.(comp)}
      >
        {p.label ?? "Button"}
      </button>
    </div>
  {:else if comp.type === "form"}
    <div class="card form-card">
      {#if formSuccess}
        <div class="form-success">Submitted successfully!</div>
      {/if}
      <form
        class="site-form"
        class:hidden={formSuccess}
        onsubmit={(e) => {
          e.preventDefault();
          if (onformsubmit) {
            const data = collectFormData(e.currentTarget);
            onformsubmit(comp, data);
            formSuccess = true;
            setTimeout(() => { formSuccess = false; }, 3000);
          }
        }}
      >
        {#if true}
        {@const groupedFields = groupFieldsBySection(p.fields ?? [])}
        {#each groupedFields as item, idx}
          {#if item.type === "section"}
            {@const sectionId = item.id ?? item.name ?? `section_${idx}`}
            {@const isExpanded = expandedSections[sectionId] ?? true}
            <div class="form-section">
              <button
                type="button"
                class="form-section-header"
                onclick={() => toggleSection(sectionId)}
                title={isExpanded ? "Collapse" : "Expand"}
              >
                <svg class="form-section-chevron" class:expanded={isExpanded} width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polyline points="6 9 12 15 18 9"></polyline>
                </svg>
                <span class="form-section-title">{item.label ?? "Section"}</span>
              </button>
              {#if isExpanded}
                <div class="form-section-content">
                  {#each (item.fields ?? []) as field, fi}
                    <div class="form-field" class:form-field-paragraph={field.type === "paragraph"}>
                      {#if field.type === "paragraph"}
                        <p class="form-paragraph">{field.label ?? field.content ?? ""}</p>
                      {:else}
                        <label for="{comp.id}-{field.name ?? `s${idx}f${fi}`}">{field.label ?? field.name}</label>
                        {#if field.type === "email" || field.type === "text" || field.type === "phone"}
                          <input
                            id="{comp.id}-{field.name ?? `s${idx}f${fi}`}"
                            type={field.type === "phone" ? "tel" : field.type}
                            name={field.name ?? field.id}
                            value={field.defaultValue ?? ''}
                            required={field.required ?? false}
                            placeholder={field.placeholder}
                          />
                        {:else if field.type === "textarea"}
                          <textarea
                            id="{comp.id}-{field.name ?? `s${idx}f${fi}`}"
                            name={field.name ?? field.id}
                            required={field.required ?? false}
                            placeholder={field.placeholder}
                            rows="3"
                          >{field.defaultValue ?? ''}</textarea>
                        {:else if field.type === "select"}
                          <select
                            id="{comp.id}-{field.name ?? `s${idx}f${fi}`}"
                            name={field.name ?? field.id}
                            value={field.defaultValue ?? ''}
                            required={field.required ?? false}
                          >
                            <option value="">{field.placeholder ?? "Select..."}</option>
                            {#each (field.options ?? []) as opt}
                              <option value={opt}>{opt}</option>
                            {/each}
                          </select>
                        {:else if field.type === "checkbox"}
                          <input
                            type="checkbox"
                            id="{comp.id}-{field.name ?? `s${idx}f${fi}`}"
                            name={field.name ?? field.id}
                            checked={field.defaultValue ?? false}
                          />
                        {:else if field.type === "file"}
                          {@const fkey = fileFieldKey(field, `s${idx}f${fi}`)}
                          <div
                            class="file-dropzone"
                            class:file-dragover={dragOver[fkey]}
                            class:has-files={(fileFields[fkey] ?? []).length > 0}
                            ondragover={(e) => { e.preventDefault(); dragOver[fkey] = true; }}
                            ondragleave={() => { dragOver[fkey] = false; }}
                            ondrop={(e) => handleFileDrop(e, fkey)}
                            onclick={(e) => {
                              if (e.target.closest('.file-remove')) return;
                              e.currentTarget.querySelector('input[type="file"]')?.click();
                            }}
                            role="button"
                            tabindex="0"
                            onkeydown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.currentTarget.querySelector('input[type="file"]')?.click(); } }}
                          >
                            <input
                              type="file"
                              id="{comp.id}-{field.name ?? `s${idx}f${fi}`}"
                              name={field.name ?? field.id}
                              required={(field.required ?? false) && !(fileFields[fkey] ?? []).length}
                              multiple
                              style="display: none;"
                              onchange={(e) => handleFileSelect(e, fkey)}
                            />
                            {#if (fileFields[fkey] ?? []).length > 0}
                              <div class="file-list">
                                {#each fileFields[fkey] as file, jdx}
                                  <div class="file-item">
                                    <svg class="file-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                    <span class="file-name">{file.name}</span>
                                    <span class="file-size">{formatFileSize(file.size)}</span>
                                    <button type="button" class="file-remove" onclick={() => removeFile(fkey, jdx)} title="Remove">
                                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                                    </button>
                                  </div>
                                {/each}
                              </div>
                              <p class="file-hint">Drop more files or click to add</p>
                            {:else}
                              <svg class="file-upload-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                              <p class="file-dropzone-text">Drag & drop files here</p>
                              <p class="file-dropzone-hint">or click to browse</p>
                            {/if}
                          </div>
                        {:else if field.type === "links"}
                          {@const lkey = linkFieldKey(field, `s${idx}f${fi}`)}
                          {@const links = getLinks(lkey)}
                          <div class="links-field">
                            {#each links as link, li}
                              <div class="link-entry">
                                <input
                                  type="text"
                                  value={link}
                                  oninput={(e) => updateLink(lkey, li, e.currentTarget.value)}
                                  placeholder={field.placeholder ?? "https://..."}
                                />
                                <button type="button" class="link-remove" onclick={() => removeLink(lkey, li)} title="Remove">
                                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                                </button>
                              </div>
                            {/each}
                            <button type="button" class="link-add" onclick={() => addLink(lkey)}>+</button>
                          </div>
                        {:else}
                          <input
                            id="{comp.id}-{field.name ?? `s${idx}f${fi}`}"
                            type="text"
                            name={field.name ?? field.id}
                            required={field.required ?? false}
                            placeholder={field.placeholder}
                          />
                        {/if}
                      {/if}
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {:else if item.type === "paragraph"}
            <div class="form-field form-field-paragraph">
              <p class="form-paragraph">{item.label ?? item.content ?? ""}</p>
            </div>
          {:else}
            <div class="form-field" class:form-field-paragraph={item.type === "paragraph"}>
              <label for="{comp.id}-{item.name ?? idx}">{item.label ?? item.name}</label>
              {#if item.type === "email" || item.type === "text" || item.type === "phone"}
                <input
                  id="{comp.id}-{item.name ?? idx}"
                  type={item.type === "phone" ? "tel" : item.type}
                  name={item.name ?? item.id}
                  value={item.defaultValue ?? ''}
                  required={item.required ?? false}
                  placeholder={item.placeholder}
                />
              {:else if item.type === "textarea"}
                <textarea
                  id="{comp.id}-{item.name ?? idx}"
                  name={item.name ?? item.id}
                  required={item.required ?? false}
                  placeholder={item.placeholder}
                  rows="3"
                >{item.defaultValue ?? ''}</textarea>
              {:else if item.type === "select"}
                <select
                  id="{comp.id}-{item.name ?? idx}"
                  name={item.name ?? item.id}
                  value={item.defaultValue ?? ''}
                  required={item.required ?? false}
                >
                  <option value="">{item.placeholder ?? "Select..."}</option>
                  {#each (item.options ?? []) as opt}
                    <option value={opt}>{opt}</option>
                  {/each}
                </select>
              {:else if item.type === "checkbox"}
                <input
                  type="checkbox"
                  id="{comp.id}-{item.name ?? idx}"
                  name={item.name ?? item.id}
                  checked={item.defaultValue ?? false}
                />
              {:else if item.type === "file"}
                {@const fkey = fileFieldKey(item, idx)}
                <div
                  class="file-dropzone"
                  class:file-dragover={dragOver[fkey]}
                  class:has-files={(fileFields[fkey] ?? []).length > 0}
                  ondragover={(e) => { e.preventDefault(); dragOver[fkey] = true; }}
                  ondragleave={() => { dragOver[fkey] = false; }}
                  ondrop={(e) => handleFileDrop(e, fkey)}
                  onclick={(e) => {
                    if (e.target.closest('.file-remove')) return;
                    e.currentTarget.querySelector('input[type="file"]')?.click();
                  }}
                  role="button"
                  tabindex="0"
                  onkeydown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.currentTarget.querySelector('input[type="file"]')?.click(); } }}
                >
                  <input
                    type="file"
                    id="{comp.id}-{item.name ?? idx}"
                    name={item.name ?? item.id}
                    required={(item.required ?? false) && !(fileFields[fkey] ?? []).length}
                    multiple
                    style="display: none;"
                    onchange={(e) => handleFileSelect(e, fkey)}
                  />
                  {#if (fileFields[fkey] ?? []).length > 0}
                    <div class="file-list">
                      {#each fileFields[fkey] as file, jdx}
                        <div class="file-item">
                          <svg class="file-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                          <span class="file-name">{file.name}</span>
                          <span class="file-size">{formatFileSize(file.size)}</span>
                          <button type="button" class="file-remove" onclick={() => removeFile(fkey, jdx)} title="Remove">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                          </button>
                        </div>
                      {/each}
                    </div>
                    <p class="file-hint">Drop more files or click to add</p>
                  {:else}
                    <svg class="file-upload-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                    <p class="file-dropzone-text">Drag & drop files here</p>
                    <p class="file-dropzone-hint">or click to browse</p>
                  {/if}
                </div>
              {:else if item.type === "links"}
                {@const lkey = linkFieldKey(item, idx)}
                {@const links = getLinks(lkey)}
                <div class="links-field">
                  {#each links as link, li}
                    <div class="link-entry">
                      <input
                        type="text"
                        value={link}
                        oninput={(e) => updateLink(lkey, li, e.currentTarget.value)}
                        placeholder={item.placeholder ?? "https://..."}
                      />
                      <button type="button" class="link-remove" onclick={() => removeLink(lkey, li)} title="Remove">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                      </button>
                    </div>
                  {/each}
                  <button type="button" class="link-add" onclick={() => addLink(lkey)}>+</button>
                </div>
              {:else}
                <input
                  id="{comp.id}-{item.name ?? idx}"
                  type="text"
                  name={item.name ?? item.id}
                  required={item.required ?? false}
                  placeholder={item.placeholder}
                />
              {/if}
            </div>
          {/if}
        {/each}
        <button type="submit" class="btn-variant-primary">
          {p.submitLabel ?? "Submit"}
        </button>
        {/if}
      </form>
    </div>
  {:else if comp.type === "chat_window"}
    {#if interactive && project}
      <div class="chat-window-live">
        <ChatArea
          currentUser={user?.username ?? null}
          currentUserDisplayName={user?.display_name ?? null}
          {project}
          agentId={p.agentId ?? null}
        />
      </div>
    {:else}
      <div class="card chat-window-card">
        <div class="chat-placeholder-ui">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          <span class="chat-placeholder-name">{p.botName || "Chat"}</span>
          <span class="chat-placeholder-hint">Live chat in preview / published site</span>
        </div>
      </div>
    {/if}
  {:else if comp.type === "table"}
    <div class="card table-card">
      {#if !interactive}
        <!-- Static placeholder for canvas preview -->
        <div class="table-scroll">
          <table class="site-table">
            <thead>
              <tr>
                <th>Column 1</th><th>Column 2</th><th>Column 3</th>
                {#if (p.actions ?? []).length}
                  <th class="actions-col">Actions</th>
                {/if}
              </tr>
            </thead>
            <tbody>
              {#each [0, 1, 2] as ri}
                <tr class="table-placeholder-row">
                  <td><span class="placeholder-cell"></span></td>
                  <td><span class="placeholder-cell"></span></td>
                  <td><span class="placeholder-cell"></span></td>
                  {#if (p.actions ?? []).length}
                    <td class="actions-cell">
                      {#each (p.actions ?? []) as act}
                        <span class="row-action-btn placeholder-action" title={act.label}>
                          {@html getActionIconSvg(act.icon)}
                        </span>
                      {/each}
                    </td>
                  {/if}
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {:else}
        <!-- Interactive table toolbar -->
        <div class="table-toolbar">
          {#if tableLoading}
            <span class="table-row-count">Loading…</span>
          {:else if tableError}
            <span class="table-row-count table-error-msg">{tableError}</span>
            {#if tableRetryCount < TABLE_MAX_RETRIES}
              <button type="button" class="table-retry-btn" onclick={() => fetchTableData(true)}>Retry</button>
            {/if}
          {:else}
            <span class="table-row-count">{tableData.length} row{tableData.length !== 1 ? "s" : ""}</span>
          {/if}
          <button type="button" class="table-refresh-btn" onclick={fetchTableData} title="Refresh" disabled={tableLoading}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
          </button>
        </div>
        {#if tableError && tableRetryCount >= TABLE_MAX_RETRIES}
          <div class="table-status table-error-msg">Failed to load data after {TABLE_MAX_RETRIES} attempts. Check the endpoint configuration.</div>
        {:else if !tableData.length && !tableLoading && !tableError}
          <div class="table-status">{p.emptyMessage ?? "No data found"}</div>
        {:else if tableColumns.length}
          <div class="table-scroll">
            <table class="site-table">
              {#if p.showHeader !== false}
                <thead>
                  <tr>
                    {#each tableColumns as col}
                      <th style="width: {col.width ?? 150}px">{col.label || col.key}</th>
                    {/each}
                    {#if (p.actions ?? []).length}
                      <th class="actions-col">Actions</th>
                    {/if}
                  </tr>
                </thead>
              {/if}
              <tbody>
                {#each tableData as row, ri}
                  <tr>
                    {#each tableColumns as col}
                      <td>{row[col.key] ?? ""}</td>
                    {/each}
                    {#if (p.actions ?? []).length}
                      <td class="actions-cell">
                        {#each (p.actions ?? []) as act}
                          <button type="button" class="row-action-btn" title={act.label}
                            onclick={() => ontableaction?.(comp, act, row)}>
                            {@html getActionIconSvg(act.icon)}
                          </button>
                        {/each}
                      </td>
                    {/if}
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {/if}
      {/if}
    </div>
  {:else}
    <div class="card unknown-card">
      <pre>{JSON.stringify(comp, null, 2)}</pre>
    </div>
  {/if}
</div>

<style>
  .component-preview {
    width: 100%;
    height: 100%;
  }

  .component-preview.non-interactive {
    pointer-events: none;
  }

  .card {
    width: 100%;
    height: 100%;
    border-radius: var(--radius-lg);
    border: none;
    background-color: transparent;
    padding: var(--spacing-md);
    box-shadow: none;
    overflow: auto;
  }

  .heading-card {
    display: flex;
    align-items: center;
    padding: var(--spacing-sm) var(--spacing-md);
    background: transparent;
    border: none;
    box-shadow: none;
  }

  .heading-card h1,
  .heading-card h2,
  .heading-card h3 {
    margin: 0;
    font-family: var(--font-display);
    color: var(--text-primary);
    width: 100%;
  }

  .heading-card h1 { font-size: 2rem; }
  .heading-card h2 { font-size: 1.5rem; }
  .heading-card h3 { font-size: 1.15rem; }

  .text-card {
    background: transparent;
    border: none;
    box-shadow: none;
  }

  .text-card p {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-primary);
    line-height: 1.6;
  }

  .image-card {
    padding: 0;
    overflow: hidden;
    background: transparent;
  }

  .image-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-secondary);
    color: var(--text-secondary);
    opacity: 0.5;
  }

  .divider-card {
    display: flex;
    align-items: center;
    padding: 0 var(--spacing-md);
    background: transparent;
    border: none;
    box-shadow: none;
  }

  .button-card {
    display: flex;
    align-items: center;
    justify-content: center;
    background: transparent;
    border: none;
    box-shadow: none;
  }

  .button-card button,
  .btn-variant-primary {
    padding: 6px 24px;
    height: 36px;
    border-radius: var(--radius-full);
    border: none;
    background-color: var(--primary-accent);
    color: white;
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.12s ease;
  }

  .button-card button:hover,
  .btn-variant-primary:hover {
    background-color: var(--primary-accent-hover);
  }

  .btn-variant-secondary {
    padding: 6px 24px;
    height: 36px;
    border-radius: var(--radius-full);
    border: 1px solid var(--border-color);
    background: transparent;
    color: var(--text-primary);
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
  }

  .btn-variant-outline {
    padding: 6px 24px;
    height: 36px;
    border-radius: var(--radius-full);
    border: 2px solid var(--text-primary);
    background: transparent;
    color: var(--text-primary);
    font-size: 0.875rem;
    font-weight: 600;
    cursor: pointer;
  }

  .form-card {
    background: var(--bg-primary);
  }

  .form-card .site-form {
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
  }

  .form-card .form-field {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .form-card .form-field label {
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-secondary);
  }

  .form-card .form-field-paragraph {
    margin-bottom: 0.5rem;
  }

  .form-card .form-paragraph {
    margin: 0;
    font-size: 0.875rem;
    color: var(--text-primary);
    line-height: 1.5;
    white-space: pre-wrap;
  }

  .form-card .form-field input[type="checkbox"] {
    width: auto;
    margin-right: 0.5rem;
  }

  .form-card .form-field select {
    padding: 0.5rem 0.75rem;
    border: 1px solid #334155;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    width: 100%;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .form-card .form-field input,
  .form-card .form-field textarea {
    padding: 0.5rem 0.75rem;
    border: 1px solid #334155;
    border-radius: var(--radius-md);
    font-size: 0.875rem;
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  .form-card .form-field input:focus,
  .form-card .form-field textarea:focus,
  .form-card .form-field select:focus {
    outline: none;
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
  }

  .form-card .form-field input::placeholder,
  .form-card .form-field textarea::placeholder {
    color: var(--text-muted);
  }

  .chat-window-card {
    background: var(--bg-primary);
  }

  .chat-window-live {
    width: 100%;
    height: 100%;
    border-radius: var(--radius-lg);
    overflow: hidden;
    border: 1px solid var(--border-color);
  }

  .chat-placeholder-ui {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: var(--spacing-xs);
    height: 100%;
    color: var(--text-secondary);
    opacity: 0.6;
  }

  .chat-placeholder-name {
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text-primary);
  }

  .chat-placeholder-hint {
    font-size: 0.75rem;
  }

  .unknown-card pre {
    margin: 0;
    font-size: 0.75rem;
    white-space: pre-wrap;
    word-break: break-word;
    color: var(--text-secondary);
  }

  .file-dropzone {
    border: 2px dashed var(--border-color);
    border-radius: var(--radius-md);
    padding: var(--spacing-md);
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    cursor: pointer;
    transition: border-color 0.15s ease, background 0.15s ease;
    background: var(--bg-secondary);
    min-height: 80px;
    justify-content: center;
  }

  .file-dropzone:hover {
    border-color: var(--primary-accent);
    background: var(--accent-glow);
  }

  .file-dropzone.file-dragover {
    border-color: var(--primary-accent);
    background: rgba(225, 29, 72, 0.08);
    border-style: solid;
  }

  .file-dropzone.has-files {
    align-items: stretch;
    gap: var(--spacing-xs);
  }

  .file-upload-icon {
    color: var(--text-secondary);
    opacity: 0.6;
  }

  .file-dropzone-text {
    margin: 0;
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--text-primary);
  }

  .file-dropzone-hint {
    margin: 0;
    font-size: 0.7rem;
    color: var(--text-secondary);
  }

  .file-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
    width: 100%;
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
    padding: 4px 8px;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    font-size: 0.75rem;
  }

  .file-icon {
    color: var(--text-secondary);
    flex-shrink: 0;
  }

  .file-name {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: var(--text-primary);
    font-weight: 500;
  }

  .file-size {
    color: var(--text-secondary);
    flex-shrink: 0;
  }

  .file-remove {
    background: none;
    border: none;
    padding: 2px;
    cursor: pointer;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    border-radius: var(--radius-sm);
    transition: color 0.12s ease, background 0.12s ease;
    flex-shrink: 0;
  }

  .file-remove:hover {
    color: #f87171;
    background: rgba(220, 38, 38, 0.1);
  }

  .file-hint {
    margin: 0;
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-align: center;
  }

  /* Links field (multi-add) */
  .links-field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .link-entry {
    display: flex;
    align-items: center;
    gap: var(--spacing-xs);
  }

  .link-entry input {
    flex: 1;
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    font-size: 0.85rem;
    font-family: var(--font-sans);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .link-entry input:focus {
    outline: none;
    border-color: var(--text-primary);
    box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.05);
  }

  .link-remove {
    background: none;
    border: none;
    padding: 4px;
    cursor: pointer;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    border-radius: var(--radius-sm);
    transition: color 0.12s ease, background 0.12s ease;
    flex-shrink: 0;
  }

  .link-remove:hover {
    color: #f87171;
    background: rgba(220, 38, 38, 0.1);
  }

  .link-add {
    width: 100%;
    background: none;
    border: 1px dashed var(--border-color);
    border-radius: var(--radius-sm);
    padding: 0.4rem 0;
    font-size: 1rem;
    color: var(--text-secondary);
    cursor: pointer;
    font-family: var(--font-sans);
    transition: color 0.12s ease, border-color 0.12s ease;
  }

  .link-add:hover {
    color: var(--text-primary);
    border-color: var(--text-primary);
  }

  /* Form section (collapsible) */
  .form-section {
    margin: 0;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    overflow: hidden;
  }

  .form-section-header {
    width: 100%;
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
    padding: 0.75rem var(--spacing-md);
    background: var(--bg-secondary);
    border: none;
    cursor: pointer;
    font-family: var(--font-sans);
    font-size: 0.9rem;
    font-weight: 500;
    color: var(--text-primary);
    transition: background 0.2s ease;
  }

  .form-section-header:hover {
    background: rgba(255, 255, 255, 0.04);
  }

  .form-section-chevron {
    flex-shrink: 0;
    transition: transform 0.2s ease;
    color: var(--text-secondary);
  }

  .form-section-chevron.expanded {
    transform: rotate(180deg);
  }

  .form-section-title {
    flex: 1;
    text-align: left;
  }

  .form-section-content {
    padding: var(--spacing-md);
    display: flex;
    flex-direction: column;
    gap: var(--spacing-sm);
    animation: sectionSlideDown 0.2s ease;
  }

  @keyframes sectionSlideDown {
    from {
      opacity: 0;
      max-height: 0;
    }
    to {
      opacity: 1;
      max-height: 1000px;
    }
  }

  /* Table component */
  .table-card {
    padding: 0;
    overflow: hidden;
    background: var(--bg-primary);
  }

  .table-scroll {
    width: 100%;
    height: 100%;
    overflow: auto;
  }

  .site-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8rem;
    color: var(--text-primary);
  }

  .site-table thead {
    position: sticky;
    top: 0;
    z-index: 1;
  }

  .site-table th {
    background: var(--bg-secondary);
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: var(--text-secondary);
    padding: 8px 12px;
    text-align: left;
    border-bottom: 1px solid var(--border-color);
    white-space: nowrap;
  }

  .site-table td {
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-color);
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .site-table tbody tr:hover {
    background: rgba(255, 255, 255, 0.03);
  }

  .actions-col {
    text-align: right;
    width: 1%;
  }

  .actions-cell {
    text-align: right;
    white-space: nowrap;
  }

  .row-action-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 28px;
    height: 28px;
    border: none;
    background: transparent;
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
    padding: 0;
  }

  .row-action-btn:hover {
    background: rgba(255, 255, 255, 0.06);
    color: var(--text-primary);
  }

  .placeholder-action {
    cursor: default;
    opacity: 0.4;
  }

  .table-placeholder-row td {
    color: transparent;
  }

  .placeholder-cell {
    display: inline-block;
    width: 60%;
    height: 12px;
    background: var(--bg-secondary);
    border-radius: 4px;
  }

  .table-toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 12px;
    border-bottom: 1px solid var(--border-color);
    background: var(--bg-secondary);
    flex-shrink: 0;
  }

  .table-row-count {
    font-size: 0.75rem;
    color: var(--text-secondary);
    font-weight: 500;
  }

  .table-refresh-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    border: none;
    background: transparent;
    border-radius: var(--radius-sm);
    color: var(--text-secondary);
    cursor: pointer;
    transition: color 0.12s ease, background 0.12s ease;
    padding: 0;
  }

  .table-refresh-btn:hover:not(:disabled) {
    color: var(--text-primary);
    background: rgba(255, 255, 255, 0.06);
  }

  .table-refresh-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .table-status {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 80px;
    font-size: 0.85rem;
    color: var(--text-secondary);
    padding: var(--spacing-md);
  }

  .table-error-msg {
    color: #dc2626;
  }

  .table-retry-btn {
    background: none;
    border: 1px solid #dc2626;
    color: #dc2626;
    border-radius: var(--radius-sm);
    padding: 0.15rem 0.5rem;
    font-size: 0.75rem;
    cursor: pointer;
    transition: background 0.12s ease;
  }
  .table-retry-btn:hover {
    background: rgba(220, 38, 38, 0.08);
  }

  .form-success {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: var(--spacing-md);
    font-size: 0.875rem;
    font-weight: 500;
    color: #16a34a;
  }

  .site-form.hidden {
    display: none;
  }
</style>
