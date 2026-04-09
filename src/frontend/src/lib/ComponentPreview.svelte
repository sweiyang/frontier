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

  let formSubmitting = $state(false);
  let formResponse = $state('');
  let formResponseOk = $state(false);
  let showSuccessPopup = $state(false);
  let submittedFormData = $state({});
  /** @type {Record<string, File[]>} */
  let fileFields = $state({});
  /** @type {Record<string, boolean>} */
  let dragOver = $state({});
  /** @type {Record<string, boolean>} - track expanded/collapsed state of sections */
  let expandedSections = $state({});
  const p = $derived(comp.props || {});

  // Initialize expanded state for sections via $effect (not during render)
  $effect(() => {
    const fields = p.fields ?? [];
    const patch = {};
    let needsUpdate = false;
    let sectionIndex = 0;
    for (const field of fields) {
      if (field.type === "section") {
        const sectionId = field.id ?? field.name ?? `section_${sectionIndex}`;
        if (!(sectionId in expandedSections)) {
          patch[sectionId] = !field.startCollapsed;
          needsUpdate = true;
        }
        sectionIndex++;
      }
    }
    if (needsUpdate) {
      expandedSections = { ...expandedSections, ...patch };
    }
  });

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
    expandedSections = { ...expandedSections, [sectionId]: !expandedSections[sectionId] };
  }

  function interpolatePopupBody(template, data) {
    return template.replace(/\{\{(\w+)\}\}/g, (_, key) =>
      data[key] !== undefined ? `<strong>${String(data[key])}</strong>` : `{{${key}}}`
    );
  }

  // Table data fetching
  let tableData = $state([]);
  let tableColumns = $state([]);
  let tableLoading = $state(false);
  let tableError = $state("");
  let tableRetryCount = $state(0);
  const TABLE_MAX_RETRIES = 3;
  const activeCount = $derived(
    p.activeCountCol
      ? tableData.filter(r => String(r[p.activeCountCol] ?? "").toLowerCase() === (p.activeCountVal ?? "active").toLowerCase()).length
      : 0
  );

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

  function getFeatureIconSvg(icon) {
    const attrs = 'width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"';
    switch (icon) {
      case "mic": return `<svg ${attrs}><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></svg>`;
      case "brain": return `<svg ${attrs}><path d="M9.5 2A2.5 2.5 0 0 1 12 4.5v15a2.5 2.5 0 0 1-4.96.44 2.5 2.5 0 0 1-2.96-3.08 3 3 0 0 1-.34-5.58 2.5 2.5 0 0 1 1.32-4.24 2.5 2.5 0 0 1 1.98-3A2.5 2.5 0 0 1 9.5 2z"/><path d="M14.5 2A2.5 2.5 0 0 0 12 4.5v15a2.5 2.5 0 0 0 4.96.44 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 14.5 2z"/></svg>`;
      case "shield": return `<svg ${attrs}><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>`;
      case "chart": return `<svg ${attrs}><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>`;
      case "globe": return `<svg ${attrs}><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>`;
      case "lock": return `<svg ${attrs}><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`;
      case "zap": return `<svg ${attrs}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`;
      case "star": return `<svg ${attrs}><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>`;
      case "check": return `<svg ${attrs}><polyline points="20 6 9 17 4 12"/></svg>`;
      case "users": return `<svg ${attrs}><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`;
      default: return `<svg ${attrs}><circle cx="12" cy="12" r="10"/></svg>`;
    }
  }

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

  // Compliance form state
  let complianceTab = $state("new");
  let complianceInternalMode = $state("url");
  let complianceExternalMode = $state("url");
  let complianceAdvancedOpen = $state(false);
  let complianceRecursiveLevel = $state(p.recursiveSearchLevel ?? 2);
  let complianceHistoryItems = $state(p.historyItems ?? []);
  let complianceHistoryLoading = $state(false);

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
  {:else if comp.type === "back_nav"}
    <div class="back-nav-bar">
      <button
        class="back-nav-btn"
        type="button"
        onclick={() => {
          if (!interactive) return;
          const route = p.route ?? "/";
          const prefix = project ? `/${encodeURIComponent(project)}` : "";
          const normalized = route.startsWith("/") ? route : "/" + route;
          const full = normalized.startsWith(prefix) ? normalized : prefix + normalized;
          window.history.pushState({}, "", full);
          window.dispatchEvent(new PopStateEvent("popstate"));
        }}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
        {p.label ?? "Back"}
      </button>
    </div>
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
      <form
        class="site-form"
        onsubmit={async (e) => {
          e.preventDefault();
          if (onformsubmit) {
            formSubmitting = true;
            formResponse = '';
            const formEl = e.currentTarget;
            const data = collectFormData(formEl);
            try {
              const result = await onformsubmit(comp, data);
              formResponseOk = result?.ok ?? false;
              formResponse = result?.responseText ?? (result?.ok ? 'Submitted successfully' : 'Submission failed');
              if (result?.ok) {
                formEl.reset();
                fileFields = {};
                linkFields = {};
              }
            } catch (err) {
              formResponseOk = false;
              formResponse = err.message || 'Submission failed';
            } finally {
              formSubmitting = false;
            }
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
                        {:else if field.type === "user_metadata"}
                          <input
                            id="{comp.id}-{field.name ?? `s${idx}f${fi}`}"
                            type="text"
                            name={field.name ?? field.id}
                            value={user?.[field.metadataKey ?? "username"] ?? ""}
                            readonly={!(field.editable ?? true)}
                            required={field.required ?? false}
                            placeholder={field.placeholder}
                            style={!(field.editable ?? true) ? "background: var(--bg-secondary); color: var(--text-secondary); cursor: not-allowed;" : ""}
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
              {:else if item.type === "user_metadata"}
                <input
                  id="{comp.id}-{item.name ?? idx}"
                  type="text"
                  name={item.name ?? item.id}
                  value={user?.[item.metadataKey ?? "username"] ?? ""}
                  readonly={!(item.editable ?? true)}
                  required={item.required ?? false}
                  placeholder={item.placeholder}
                  style={!(item.editable ?? true) ? "background: var(--bg-secondary); color: var(--text-secondary); cursor: not-allowed;" : ""}
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
        <button type="submit" class="btn-variant-primary" disabled={formSubmitting}>
          {#if formSubmitting}
            Submitting...
          {:else}
            {p.submitLabel ?? "Submit"}
          {/if}
        </button>
        {#if formResponse}
          <div class="form-response" class:form-response-ok={formResponseOk} class:form-response-error={!formResponseOk}>
            {formResponse}
          </div>
        {/if}
        {/if}
      </form>
    </div>
  {:else if comp.type === "hero_form"}
    <div class="hero-form-wrapper">
      <div class="hero-form-inner">
      <div class="hero-form-left">
        {#if p.badge}
          <span class="hero-badge">{p.badge}</span>
        {/if}
        <h1 class="hero-heading">
          {#if p.headingAccent && p.heading?.includes(p.headingAccent)}
            {p.heading.split(p.headingAccent)[0]}<span class="hero-accent">{p.headingAccent}</span>{p.heading.split(p.headingAccent).slice(1).join(p.headingAccent)}
          {:else}
            {p.heading ?? "Heading"}
          {/if}
        </h1>
        {#if p.description}
          <p class="hero-description">{p.description}</p>
        {/if}
        {#if (p.features ?? []).length}
          <div class="hero-features">
            {#each p.features as feat}
              <span class="hero-feature-badge">
                {@html getFeatureIconSvg(feat.icon)}
                {feat.text}
              </span>
            {/each}
          </div>
        {/if}
      </div>
      <div class="hero-form-right">
        <div class="hero-form-card">
          <form
            class="site-form"
            onsubmit={async (e) => {
              e.preventDefault();
              if (onformsubmit) {
                formSubmitting = true;
                formResponse = '';
                const formEl = e.currentTarget;
                const data = collectFormData(formEl);
                try {
                  const result = await onformsubmit(comp, data);
                  formResponseOk = result?.ok ?? false;
                  if (result?.ok) {
                    formEl.reset();
                    fileFields = {};
                    linkFields = {};
                    if (p.successPopup?.enabled) {
                      submittedFormData = data;
                      showSuccessPopup = true;
                      formResponse = '';
                    } else {
                      formResponse = result?.responseText ?? 'Submitted successfully';
                    }
                  } else {
                    formResponse = result?.responseText ?? 'Submission failed';
                  }
                } catch (err) {
                  formResponseOk = false;
                  formResponse = err.message || 'Submission failed';
                } finally {
                  formSubmitting = false;
                }
              }
            }}
          >
            {#if true}
            {@const groupedFields = groupFieldsBySection(p.fields ?? [])}
            <div class="hero-form-fields">
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
                              <input id="{comp.id}-{field.name ?? `s${idx}f${fi}`}" type={field.type === "phone" ? "tel" : field.type} name={field.name ?? field.id} value={field.defaultValue ?? ''} required={field.required ?? false} placeholder={field.placeholder} />
                            {:else if field.type === "textarea"}
                              <textarea id="{comp.id}-{field.name ?? `s${idx}f${fi}`}" name={field.name ?? field.id} required={field.required ?? false} placeholder={field.placeholder} rows="3">{field.defaultValue ?? ''}</textarea>
                            {:else if field.type === "select"}
                              <select id="{comp.id}-{field.name ?? `s${idx}f${fi}`}" name={field.name ?? field.id} value={field.defaultValue ?? ''} required={field.required ?? false}>
                                <option value="">{field.placeholder ?? "Select..."}</option>
                                {#each (field.options ?? []) as opt}<option value={opt}>{opt}</option>{/each}
                              </select>
                            {:else if field.type === "checkbox"}
                              <input type="checkbox" id="{comp.id}-{field.name ?? `s${idx}f${fi}`}" name={field.name ?? field.id} checked={field.defaultValue ?? false} />
                            {:else if field.type === "user_metadata"}
                              <input id="{comp.id}-{field.name ?? `s${idx}f${fi}`}" type="text" name={field.name ?? field.id} value={user?.[field.metadataKey ?? "username"] ?? ""} readonly={!(field.editable ?? true)} required={field.required ?? false} placeholder={field.placeholder} style={!(field.editable ?? true) ? "background: var(--bg-secondary); color: var(--text-secondary); cursor: not-allowed;" : ""} />
                            {:else if field.type === "file"}
                              {@const fkey = fileFieldKey(field, `s${idx}f${fi}`)}
                              <div class="file-dropzone" class:file-dragover={dragOver[fkey]} class:has-files={(fileFields[fkey] ?? []).length > 0} ondragover={(e) => { e.preventDefault(); dragOver[fkey] = true; }} ondragleave={() => { dragOver[fkey] = false; }} ondrop={(e) => handleFileDrop(e, fkey)} onclick={(e) => { if (e.target.closest('.file-remove')) return; e.currentTarget.querySelector('input[type="file"]')?.click(); }} role="button" tabindex="0" onkeydown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.currentTarget.querySelector('input[type="file"]')?.click(); } }}>
                                <input type="file" id="{comp.id}-{field.name ?? `s${idx}f${fi}`}" name={field.name ?? field.id} required={(field.required ?? false) && !(fileFields[fkey] ?? []).length} multiple style="display: none;" onchange={(e) => handleFileSelect(e, fkey)} />
                                {#if (fileFields[fkey] ?? []).length > 0}
                                  <div class="file-list">
                                    {#each fileFields[fkey] as file, jdx}
                                      <div class="file-item">
                                        <svg class="file-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                                        <span class="file-name">{file.name}</span>
                                        <span class="file-size">{formatFileSize(file.size)}</span>
                                        <button type="button" class="file-remove" onclick={() => removeFile(fkey, jdx)} title="Remove"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg></button>
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
                                    <input type="text" value={link} oninput={(e) => updateLink(lkey, li, e.currentTarget.value)} placeholder={field.placeholder ?? "https://..."} />
                                    <button type="button" class="link-remove" onclick={() => removeLink(lkey, li)} title="Remove"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg></button>
                                  </div>
                                {/each}
                                <button type="button" class="link-add" onclick={() => addLink(lkey)}>+</button>
                              </div>
                            {:else}
                              <input id="{comp.id}-{field.name ?? `s${idx}f${fi}`}" type="text" name={field.name ?? field.id} required={field.required ?? false} placeholder={field.placeholder} />
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
                  <label for="{comp.id}-hf-{item.name ?? idx}">{item.label ?? item.name}</label>
                  {#if item.type === "email" || item.type === "text" || item.type === "phone"}
                    <input id="{comp.id}-hf-{item.name ?? idx}" type={item.type === "phone" ? "tel" : item.type} name={item.name ?? item.id} value={item.defaultValue ?? ''} required={item.required ?? false} placeholder={item.placeholder} />
                  {:else if item.type === "textarea"}
                    <textarea id="{comp.id}-hf-{item.name ?? idx}" name={item.name ?? item.id} required={item.required ?? false} placeholder={item.placeholder} rows="3">{item.defaultValue ?? ''}</textarea>
                  {:else if item.type === "select"}
                    <select id="{comp.id}-hf-{item.name ?? idx}" name={item.name ?? item.id} value={item.defaultValue ?? ''} required={item.required ?? false}>
                      <option value="">{item.placeholder ?? "Select..."}</option>
                      {#each (item.options ?? []) as opt}<option value={opt}>{opt}</option>{/each}
                    </select>
                  {:else if item.type === "checkbox"}
                    <input type="checkbox" id="{comp.id}-hf-{item.name ?? idx}" name={item.name ?? item.id} checked={item.defaultValue ?? false} />
                  {:else if item.type === "user_metadata"}
                    <input id="{comp.id}-hf-{item.name ?? idx}" type="text" name={item.name ?? item.id} value={user?.[item.metadataKey ?? "username"] ?? ""} readonly={!(item.editable ?? true)} required={item.required ?? false} placeholder={item.placeholder} style={!(item.editable ?? true) ? "background: var(--bg-secondary); color: var(--text-secondary); cursor: not-allowed;" : ""} />
                  {:else if item.type === "file"}
                    {@const fkey = fileFieldKey(item, idx)}
                    <div class="file-dropzone" class:file-dragover={dragOver[fkey]} class:has-files={(fileFields[fkey] ?? []).length > 0} ondragover={(e) => { e.preventDefault(); dragOver[fkey] = true; }} ondragleave={() => { dragOver[fkey] = false; }} ondrop={(e) => handleFileDrop(e, fkey)} onclick={(e) => { if (e.target.closest('.file-remove')) return; e.currentTarget.querySelector('input[type="file"]')?.click(); }} role="button" tabindex="0" onkeydown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.currentTarget.querySelector('input[type="file"]')?.click(); } }}>
                      <input type="file" id="{comp.id}-hf-{item.name ?? idx}" name={item.name ?? item.id} required={(item.required ?? false) && !(fileFields[fkey] ?? []).length} multiple style="display: none;" onchange={(e) => handleFileSelect(e, fkey)} />
                      {#if (fileFields[fkey] ?? []).length > 0}
                        <div class="file-list">
                          {#each fileFields[fkey] as file, jdx}
                            <div class="file-item">
                              <svg class="file-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                              <span class="file-name">{file.name}</span>
                              <span class="file-size">{formatFileSize(file.size)}</span>
                              <button type="button" class="file-remove" onclick={() => removeFile(fkey, jdx)} title="Remove"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg></button>
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
                          <input type="text" value={link} oninput={(e) => updateLink(lkey, li, e.currentTarget.value)} placeholder={item.placeholder ?? "https://..."} />
                          <button type="button" class="link-remove" onclick={() => removeLink(lkey, li)} title="Remove"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg></button>
                        </div>
                      {/each}
                      <button type="button" class="link-add" onclick={() => addLink(lkey)}>+</button>
                    </div>
                  {:else}
                    <input id="{comp.id}-hf-{item.name ?? idx}" type="text" name={item.name ?? item.id} required={item.required ?? false} placeholder={item.placeholder} />
                  {/if}
                </div>
              {/if}
            {/each}
            </div>
            <div class="hero-form-footer">
              <button type="submit" class="hero-submit-btn" disabled={formSubmitting}>
                {#if formSubmitting}
                  Submitting...
                {:else}
                  {p.submitLabel ?? "Submit"}
                {/if}
              </button>
              {#if formResponse}
                <div class="form-response" class:form-response-ok={formResponseOk} class:form-response-error={!formResponseOk}>
                  {formResponse}
                </div>
              {/if}
            </div>
            {/if}
          </form>
        </div>
      </div>
      </div>
    </div>
    {#if showSuccessPopup && p.successPopup?.enabled}
      {@const popup = p.successPopup}
      <div class="success-popup-overlay" role="dialog" aria-modal="true" onclick={() => (showSuccessPopup = false)}>
        <div class="success-popup-card" onclick={(e) => e.stopPropagation()}>
          <div class="success-popup-icon-wrap">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
          </div>
          <h2 class="success-popup-title">{popup.title ?? "Request Received"}</h2>
          <p class="success-popup-body">{@html interpolatePopupBody(popup.body ?? "", submittedFormData)}</p>
          {#if popup.ctaLabel}
            <button class="success-popup-cta" onclick={() => {
              showSuccessPopup = false;
              if (popup.ctaRoute) {
                const prefix = project ? `/${encodeURIComponent(project)}` : "";
                const route = popup.ctaRoute.startsWith("/") ? popup.ctaRoute : "/" + popup.ctaRoute;
                const full = route.startsWith(prefix) ? route : prefix + route;
                window.history.pushState({}, "", full);
                window.dispatchEvent(new PopStateEvent("popstate"));
              }
            }}>
              {popup.ctaLabel}
            </button>
          {/if}
        </div>
      </div>
    {/if}
  {:else if comp.type === "compliance_form"}
    {@const brand = p.brandColor ?? "#C41230"}
    {@const internalFields = (p.fields ?? []).filter(f => f.section === "internal")}
    {@const externalFields = (p.fields ?? []).filter(f => f.section === "external")}
    {@const historyCount = complianceHistoryItems.length}
    {@const intLinkKey = internalFields.find(f => f.type === "links") ? linkFieldKey(internalFields.find(f => f.type === "links"), "cf-int") : null}
    {@const intFileKey = internalFields.find(f => f.type === "file") ? fileFieldKey(internalFields.find(f => f.type === "file"), "cf-int-file") : null}
    {@const extLinkKey = externalFields.find(f => f.type === "links") ? linkFieldKey(externalFields.find(f => f.type === "links"), "cf-ext") : null}
    {@const extFileKey = externalFields.find(f => f.type === "file") ? fileFieldKey(externalFields.find(f => f.type === "file"), "cf-ext-file") : null}
    {@const intUrlCount = intLinkKey ? (getLinks(intLinkKey).filter(l => l.trim()).length) : 0}
    {@const intFileCount = intFileKey ? (fileFields[intFileKey] ?? []).length : 0}
    {@const intAddedCount = intUrlCount + intFileCount}
    {@const extUrlCount = extLinkKey ? (getLinks(extLinkKey).filter(l => l.trim()).length) : 0}
    {@const extFileCount = extFileKey ? (fileFields[extFileKey] ?? []).length : 0}
    {@const extAddedCount = extUrlCount + extFileCount}
    <div class="cf-wrapper" style="--cf-brand: {brand};">
      <div class="cf-inner">
        <!-- Left: Hero -->
        <div class="cf-left">
          {#if p.badge}
            <span class="cf-badge">{p.badge}</span>
          {/if}
          <h1 class="cf-heading">
            {#if p.headingAccent && p.heading?.includes(p.headingAccent)}
              {p.heading.split(p.headingAccent)[0]}<span class="cf-accent">{p.headingAccent}</span>{p.heading.split(p.headingAccent).slice(1).join(p.headingAccent)}
            {:else}
              {p.heading ?? "Heading"}
            {/if}
          </h1>
          {#if p.description}
            <p class="cf-description">{p.description}</p>
          {/if}
          {#if (p.features ?? []).length}
            <div class="cf-features">
              {#each p.features as feat}
                <span class="cf-feature-badge">
                  {@html getFeatureIconSvg(feat.icon)}
                  {feat.text}
                </span>
              {/each}
            </div>
          {/if}
        </div>

        <!-- Right: Tabbed Card -->
        <div class="cf-right">
      <div class="cf-card">
        <!-- Tab navigation -->
        <div class="cf-tabs">
          <button type="button" class="cf-tab" class:cf-tab-active={complianceTab === "new"} onclick={() => (complianceTab = "new")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.912 5.813a2 2 0 0 0 1.275 1.275L21 12l-5.813 1.912a2 2 0 0 0-1.275 1.275L12 21l-1.912-5.813a2 2 0 0 0-1.275-1.275L3 12l5.813-1.912a2 2 0 0 0 1.275-1.275L12 3z"/></svg>
            New Compliance Check
          </button>
          <button type="button" class="cf-tab" class:cf-tab-active={complianceTab === "history"} onclick={() => (complianceTab = "history")}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>
            Recent Jobs
            <span class="cf-tab-badge">{historyCount}</span>
          </button>
          <div class="cf-tab-indicator" style="transform: translateX({complianceTab === 'new' ? '0%' : '100%'});"></div>
        </div>

        {#if complianceTab === "new"}
          <form
            class="cf-form"
            onsubmit={async (e) => {
              e.preventDefault();
              if (onformsubmit) {
                formSubmitting = true;
                formResponse = '';
                const formEl = e.currentTarget;
                const data = collectFormData(formEl);
                data._recursiveSearchLevel = complianceRecursiveLevel;
                try {
                  const result = await onformsubmit(comp, data);
                  formResponseOk = result?.ok ?? false;
                  if (result?.ok) {
                    formEl.reset();
                    fileFields = {};
                    linkFields = {};
                    if (p.successPopup?.enabled) {
                      submittedFormData = data;
                      showSuccessPopup = true;
                      formResponse = '';
                    } else {
                      formResponse = result?.responseText ?? 'Submitted successfully';
                    }
                  } else {
                    formResponse = result?.responseText ?? 'Submission failed';
                  }
                } catch (err) {
                  formResponseOk = false;
                  formResponse = err.message || 'Submission failed';
                } finally {
                  formSubmitting = false;
                }
              }
            }}
          >
            <div class="cf-form-scroll">
              <!-- Section 1: Internal Source -->
              <div class="cf-section">
                <div class="cf-section-header">
                  <h3 class="cf-section-title"><span class="cf-section-num">1.</span> {p.internalSourceLabel ?? "Internal HR Policy Source"}</h3>
                  <span class="cf-added-badge">{intAddedCount} ADDED</span>
                </div>
                <div class="cf-source-toggle">
                  <button type="button" class="cf-pill" class:cf-pill-active={complianceInternalMode === "url"} onclick={() => (complianceInternalMode = "url")}>Provide URL</button>
                  <button type="button" class="cf-pill" class:cf-pill-active={complianceInternalMode === "upload"} onclick={() => (complianceInternalMode = "upload")}>Upload Document</button>
                </div>
                {#if complianceInternalMode === "url"}
                  {#each internalFields.filter(f => f.type === "links") as field}
                    {@const lkey = linkFieldKey(field, "cf-int")}
                    {@const links = getLinks(lkey)}
                    <div class="cf-field">
                      <div class="cf-url-row">
                        <div class="cf-url-icon">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                        </div>
                        <input type="text" class="cf-url-input" value={links[links.length - 1] ?? ""} oninput={(e) => updateLink(lkey, links.length - 1, e.currentTarget.value)} placeholder={field.placeholder ?? "https://intranet.ocbc.com/hr/policies/..."} />
                        <button type="button" class="cf-url-plus" onclick={() => addLink(lkey)} title="Add URL">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        </button>
                      </div>
                    </div>
                  {/each}
                {:else}
                  {#each internalFields.filter(f => f.type === "file") as field}
                    {@const fkey = fileFieldKey(field, "cf-int-file")}
                    <div class="cf-dropzone" class:cf-dragover={dragOver[fkey]} ondragover={(e) => { e.preventDefault(); dragOver[fkey] = true; }} ondragleave={() => { dragOver[fkey] = false; }} ondrop={(e) => handleFileDrop(e, fkey)} onclick={(e) => { if (e.target.closest('.file-remove')) return; e.currentTarget.querySelector('input[type="file"]')?.click(); }} role="button" tabindex="0" onkeydown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.currentTarget.querySelector('input[type="file"]')?.click(); } }}>
                      <input type="file" name={field.name ?? field.id} multiple style="display: none;" onchange={(e) => handleFileSelect(e, fkey)} />
                      {#if (fileFields[fkey] ?? []).length > 0}
                        <div class="file-list">
                          {#each fileFields[fkey] as file, jdx}
                            <div class="file-item">
                              <svg class="file-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                              <span class="file-name">{file.name}</span>
                              <span class="file-size">{formatFileSize(file.size)}</span>
                              <button type="button" class="file-remove" onclick={() => removeFile(fkey, jdx)} title="Remove"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg></button>
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
                  {/each}
                {/if}
                <!-- Combined badges for section 1 -->
                {#if intAddedCount > 0}
                  <div class="cf-link-badges">
                    {#if intLinkKey}
                      {#each getLinks(intLinkKey) as link, li}
                        {#if link.trim()}
                          <span class="cf-link-badge">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                            <span class="cf-link-badge-text">{link.length > 30 ? link.slice(0, 30) + "..." : link}</span>
                            <button type="button" class="cf-link-badge-remove" onclick={() => removeLink(intLinkKey, li)}>
                              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                            </button>
                          </span>
                        {/if}
                      {/each}
                    {/if}
                    {#if intFileKey}
                      {#each (fileFields[intFileKey] ?? []) as file, jdx}
                        <span class="cf-link-badge">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                          <span class="cf-link-badge-text">{file.name}</span>
                          <button type="button" class="cf-link-badge-remove" onclick={() => removeFile(intFileKey, jdx)}>
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                          </button>
                        </span>
                      {/each}
                    {/if}
                  </div>
                {/if}
              </div>

              <!-- Section 2: External Source -->
              <div class="cf-section">
                <div class="cf-section-header">
                  <h3 class="cf-section-title"><span class="cf-section-num">2.</span> {p.externalSourceLabel ?? "External Document to Check"}</h3>
                  <span class="cf-added-badge">{extAddedCount} ADDED</span>
                </div>
                <div class="cf-source-toggle">
                  <button type="button" class="cf-pill" class:cf-pill-active={complianceExternalMode === "url"} onclick={() => (complianceExternalMode = "url")}>Provide URL</button>
                  <button type="button" class="cf-pill" class:cf-pill-active={complianceExternalMode === "upload"} onclick={() => (complianceExternalMode = "upload")}>Upload Document</button>
                </div>
                {#if complianceExternalMode === "url"}
                  {#each externalFields.filter(f => f.type === "links") as field}
                    {@const lkey = linkFieldKey(field, "cf-ext")}
                    {@const links = getLinks(lkey)}
                    <div class="cf-field">
                      <div class="cf-url-row">
                        <div class="cf-url-icon">
                          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                        </div>
                        <input type="text" class="cf-url-input" value={links[links.length - 1] ?? ""} oninput={(e) => updateLink(lkey, links.length - 1, e.currentTarget.value)} placeholder={field.placeholder ?? "https://regulations.gov/..."} />
                        <button type="button" class="cf-url-plus" onclick={() => addLink(lkey)} title="Add URL">
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
                        </button>
                      </div>
                    </div>
                  {/each}
                {:else}
                  {#each externalFields.filter(f => f.type === "file") as field}
                    {@const fkey = fileFieldKey(field, "cf-ext-file")}
                    <div class="cf-dropzone" class:cf-dragover={dragOver[fkey]} ondragover={(e) => { e.preventDefault(); dragOver[fkey] = true; }} ondragleave={() => { dragOver[fkey] = false; }} ondrop={(e) => handleFileDrop(e, fkey)} onclick={(e) => { if (e.target.closest('.file-remove')) return; e.currentTarget.querySelector('input[type="file"]')?.click(); }} role="button" tabindex="0" onkeydown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.currentTarget.querySelector('input[type="file"]')?.click(); } }}>
                      <input type="file" name={field.name ?? field.id} multiple style="display: none;" onchange={(e) => handleFileSelect(e, fkey)} />
                      {#if (fileFields[fkey] ?? []).length > 0}
                        <div class="file-list">
                          {#each fileFields[fkey] as file, jdx}
                            <div class="file-item">
                              <svg class="file-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                              <span class="file-name">{file.name}</span>
                              <span class="file-size">{formatFileSize(file.size)}</span>
                              <button type="button" class="file-remove" onclick={() => removeFile(fkey, jdx)} title="Remove"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg></button>
                            </div>
                          {/each}
                        </div>
                        <p class="file-hint">Drop more files or click to add</p>
                      {:else}
                        <svg class="file-upload-icon" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
                        <p class="file-dropzone-text">Drop external document here</p>
                        <p class="file-dropzone-hint">Upload vendor policies or contracts to verify.</p>
                      {/if}
                    </div>
                  {/each}
                {/if}
                {#if extAddedCount > 0}
                  <div class="cf-link-badges">
                    {#if extLinkKey}
                      {#each getLinks(extLinkKey) as link, li}
                        {#if link.trim()}
                          <span class="cf-link-badge">
                            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>
                            <span class="cf-link-badge-text">{link.length > 30 ? link.slice(0, 30) + "..." : link}</span>
                            <button type="button" class="cf-link-badge-remove" onclick={() => removeLink(extLinkKey, li)}>
                              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                            </button>
                          </span>
                        {/if}
                      {/each}
                    {/if}
                    {#if extFileKey}
                      {#each (fileFields[extFileKey] ?? []) as file, jdx}
                        <span class="cf-link-badge">
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                          <span class="cf-link-badge-text">{file.name}</span>
                          <button type="button" class="cf-link-badge-remove" onclick={() => removeFile(extFileKey, jdx)}>
                            <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6L6 18"/><path d="M6 6l12 12"/></svg>
                          </button>
                        </span>
                      {/each}
                    {/if}
                  </div>
                {/if}
              </div>

              <!-- Advanced Settings (collapsible card) -->
              <div class="cf-advanced-card">
                <button type="button" class="cf-advanced-toggle" onclick={() => (complianceAdvancedOpen = !complianceAdvancedOpen)}>
                  <div class="cf-advanced-left">
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l1.912 5.813a2 2 0 0 0 1.275 1.275L21 12l-5.813 1.912a2 2 0 0 0-1.275 1.275L12 21l-1.912-5.813a2 2 0 0 0-1.275-1.275L3 12l5.813-1.912a2 2 0 0 0 1.275-1.275L12 3z"/></svg>
                    <span class="cf-advanced-title">{p.advancedLabel ?? "Advanced Settings"}</span>
                  </div>
                  <svg class="cf-advanced-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    {#if complianceAdvancedOpen}
                      <line x1="5" y1="12" x2="19" y2="12"/>
                    {:else}
                      <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
                    {/if}
                  </svg>
                </button>
                {#if complianceAdvancedOpen}
                  <div class="cf-advanced-body">
                    <div class="cf-slider-row">
                      <div class="cf-slider-info">
                        <span class="cf-slider-label">Max Recursive Search Level</span>
                        <span class="cf-slider-desc">Determines how deep the analyzer crawls linked pages.</span>
                      </div>
                      <span class="cf-slider-value">Level {complianceRecursiveLevel}</span>
                    </div>
                    <input type="range" class="cf-slider" min="1" max="5" bind:value={complianceRecursiveLevel} />
                  </div>
                {/if}
              </div>
            </div>

            <!-- Footer -->
            <div class="cf-form-footer">
              <button type="submit" class="cf-submit-btn" disabled={formSubmitting}>
                {#if formSubmitting}
                  Submitting...
                {:else}
                  {p.submitLabel ?? "RUN COMPLIANCE CHECK"}
                {/if}
              </button>
              {#if formResponse}
                <div class="form-response" class:form-response-ok={formResponseOk} class:form-response-error={!formResponseOk}>
                  {formResponse}
                </div>
              {/if}
            </div>
          </form>
        {:else}
          <!-- History tab -->
          <div class="cf-history">
            {#if complianceHistoryItems.length === 0}
              <div class="cf-history-empty">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ccc" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <h3>No recent jobs</h3>
                <p>Completed compliance checks will appear here.</p>
                <button type="button" class="cf-empty-cta" onclick={() => (complianceTab = "new")}>Start a Check</button>
              </div>
            {:else}
              <div class="cf-history-list">
                {#each complianceHistoryItems as job}
                  <div class="cf-history-card">
                    <div class="cf-history-card-icon">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                    </div>
                    <div class="cf-history-card-info">
                      <span class="cf-history-card-id">{job.id ?? "Job"}</span>
                      <span class="cf-history-card-time">{job.timestamp ?? ""}</span>
                    </div>
                    <svg class="cf-history-card-arrow" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        {/if}
      </div>
        </div>
      </div>
    </div>
    {#if showSuccessPopup && p.successPopup?.enabled}
      {@const popup = p.successPopup}
      <div class="success-popup-overlay" role="dialog" aria-modal="true" onclick={() => (showSuccessPopup = false)}>
        <div class="success-popup-card" onclick={(e) => e.stopPropagation()}>
          <div class="success-popup-icon-wrap" style="background: {brand}; box-shadow: 0 8px 24px {brand}55;">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><polyline points="9 12 11 14 15 10"/></svg>
          </div>
          <h2 class="success-popup-title">{popup.title ?? "Check Submitted"}</h2>
          <p class="success-popup-body">{@html interpolatePopupBody(popup.body ?? "", submittedFormData)}</p>
          {#if popup.ctaLabel}
            <button class="success-popup-cta" onclick={() => {
              showSuccessPopup = false;
              if (popup.ctaRoute) {
                const prefix = project ? `/${encodeURIComponent(project)}` : "";
                const route = popup.ctaRoute.startsWith("/") ? popup.ctaRoute : "/" + popup.ctaRoute;
                const full = route.startsWith(prefix) ? route : prefix + route;
                window.history.pushState({}, "", full);
                window.dispatchEvent(new PopStateEvent("popstate"));
              }
            }}>
              {popup.ctaLabel}
            </button>
          {/if}
        </div>
      </div>
    {/if}
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
    <!-- fullscreen adds the #f5f5f5 full-viewport wrapper; card style is always the same -->
    {#if comp.fullscreen && interactive}
      <div class="table-fullpage">
        {#if p.backLabel || p.backRoute}
          <button class="table-back-btn" onclick={() => {
            if (p.backRoute) {
              const prefix = project ? `/${encodeURIComponent(project)}` : "";
              const r = p.backRoute.startsWith("/") ? p.backRoute : "/" + p.backRoute;
              const full = r.startsWith(prefix) ? r : prefix + r;
              window.history.pushState({}, "", full);
              window.dispatchEvent(new PopStateEvent("popstate"));
            } else {
              window.history.back();
            }
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="15 18 9 12 15 6"/></svg>
            {p.backLabel ?? "Back"}
          </button>
        {/if}
        {@render tableCard()}
      </div>
    {:else}
      {@render tableCard()}
    {/if}

    {#snippet tableCard()}
      <div class="table-fullpage-card">
        <div class="table-fullpage-header">
          <div>
            {#if p.title}<h2 class="table-fullpage-title">{p.title}</h2>{/if}
            {#if p.subtitle}<p class="table-fullpage-subtitle">{p.subtitle}</p>{/if}
          </div>
          <div class="table-fullpage-controls">
            {#if p.activeCountCol && interactive}
              <span class="table-active-badge">{activeCount} Active</span>
            {/if}
            {#if interactive}
              <button class="table-refresh-btn-lg" type="button" onclick={fetchTableData} title="Refresh" disabled={tableLoading}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></svg>
              </button>
            {/if}
          </div>
        </div>
        {#if !interactive}
          <!-- Static placeholder for canvas preview -->
          <div class="table-scroll">
            <table class="site-table">
              <thead><tr><th>Column 1</th><th>Column 2</th><th>Column 3</th>{#if (p.actions ?? []).length}<th class="actions-col">Actions</th>{/if}</tr></thead>
              <tbody>
                {#each [0, 1, 2] as _}
                  <tr class="table-placeholder-row">
                    <td><span class="placeholder-cell"></span></td>
                    <td><span class="placeholder-cell"></span></td>
                    <td><span class="placeholder-cell"></span></td>
                    {#if (p.actions ?? []).length}<td class="actions-cell">{#each (p.actions ?? []) as act}<span class="row-action-btn placeholder-action" title={act.label}>{@html getActionIconSvg(act.icon)}</span>{/each}</td>{/if}
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        {:else if tableError && tableRetryCount >= TABLE_MAX_RETRIES}
          <div class="table-status table-error-msg">Failed to load data after {TABLE_MAX_RETRIES} attempts. Check the endpoint configuration.</div>
        {:else if tableLoading}
          <div class="table-status">Loading…</div>
        {:else if !tableData.length && !tableError}
          <div class="table-status">{p.emptyMessage ?? "No data found"}</div>
        {:else if tableError}
          <div class="table-status table-error-msg">{tableError}
            {#if tableRetryCount < TABLE_MAX_RETRIES}<button type="button" class="table-retry-btn" onclick={() => fetchTableData(true)}>Retry</button>{/if}
          </div>
        {:else if tableColumns.length}
          <div class="table-scroll">
            <table class="site-table">
              {#if p.showHeader !== false}
                <thead>
                  <tr>
                    {#each tableColumns as col}<th style="width: {col.width ?? 150}px">{col.label || col.key}</th>{/each}
                    {#if (p.actions ?? []).length}<th class="actions-col">Actions</th>{/if}
                  </tr>
                </thead>
              {/if}
              <tbody>
                {#each tableData as row}
                  <tr>
                    {#each tableColumns as col}<td>{row[col.key] ?? ""}</td>{/each}
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
      </div>
    {/snippet}
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
    padding: 0 var(--spacing-md);
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
    padding: 0 var(--spacing-md);
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

  .back-nav-bar {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    background: transparent;
  }

  .back-nav-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: none;
    border: none;
    font-size: 0.95rem;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    padding: 0.4rem 0.6rem;
    border-radius: var(--radius-sm);
    transition: color 0.15s ease, background 0.15s ease;
  }

  .back-nav-btn:hover {
    color: var(--text-primary);
    background: rgba(0, 0, 0, 0.04);
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
    font-size: 0.875rem;
    color: var(--text-primary);
  }

  .site-table thead {
    position: sticky;
    top: 0;
    z-index: 1;
  }

  .site-table th {
    background: transparent;
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #999;
    padding: 1rem 1rem 1rem;
    text-align: left;
    border-bottom: 1px solid #eee;
    white-space: nowrap;
  }

  .site-table td {
    padding: 1.1rem 1rem;
    border-bottom: 1px solid #f0f0f0;
    max-width: 280px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    color: #333;
    font-size: 0.875rem;
  }

  .site-table tbody tr:hover {
    background: #fafafa;
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
    width: 30px;
    height: 30px;
    border: none;
    background: transparent;
    border-radius: var(--radius-sm);
    color: #999;
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
    padding: 0;
  }

  .row-action-btn:hover {
    background: #f5f5f5;
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

  .form-response {
    margin-top: var(--spacing-sm);
    padding: var(--spacing-sm) var(--spacing-md);
    font-size: 0.875rem;
    font-weight: 500;
    border-radius: 6px;
    word-break: break-word;
  }
  .form-response-ok {
    color: #16a34a;
    background: rgba(22, 163, 74, 0.08);
  }
  .form-response-error {
    color: #dc2626;
    background: rgba(220, 38, 38, 0.08);
  }

  /* ── Hero + Form component ── */
  .hero-form-wrapper {
    display: flex;
    justify-content: center;
    width: 100%;
    height: 100%;
    padding: 3rem max(4rem, calc((100% - 1200px) / 2 + 4rem));
    background: #f5f5f5;
    border-radius: var(--radius-lg);
    overflow: auto;
    align-items: center;
    font-family: var(--font-sans);
    box-sizing: border-box;
  }

  .hero-form-inner {
    display: grid;
    grid-template-columns: 44% 1fr;
    gap: 3rem;
    width: 100%;
    max-width: 1200px;
    align-items: center;
  }

  .hero-form-left {
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    padding-left: 3%;
    padding-right: 0.5rem;
  }

  .hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    width: fit-content;
    padding: 0.3rem 0.75rem;
    background: rgba(225, 29, 72, 0.08);
    color: var(--primary-accent);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-radius: var(--radius-full);
    border: 1px solid rgba(225, 29, 72, 0.15);
  }

  .hero-heading {
    margin: 0;
    font-size: 3.5rem;
    font-weight: 800;
    line-height: 1.08;
    color: #0f172a;
    font-family: var(--font-display);
    letter-spacing: -0.03em;
  }

  .hero-accent {
    color: var(--primary-accent);
  }

  .hero-description {
    margin: 0;
    font-size: 1.05rem;
    line-height: 1.6;
    color: #475569;
  }

  .hero-features {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.25rem;
  }

  .hero-feature-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.75rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: var(--radius-full);
    font-size: 0.78rem;
    font-weight: 500;
    color: #334155;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  }

  .hero-feature-badge :global(svg) {
    color: var(--primary-accent);
    flex-shrink: 0;
  }

  .hero-form-right {
    display: flex;
    align-items: flex-start;
    justify-content: center;
  }

  .hero-form-card {
    width: 100%;
    max-width: 520px;
    max-height: 80vh;
    background: white;
    border-radius: 20px;
    padding: 0;
    box-shadow: 0 4px 32px rgba(0, 0, 0, 0.07), 0 1px 4px rgba(0, 0, 0, 0.03);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .hero-form-card :global(.site-form) {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
  }

  .hero-form-fields {
    flex: 1;
    overflow-y: auto;
    padding: 2.25rem 2.5rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .hero-form-footer {
    padding: 1.25rem 2.5rem 2rem;
    border-top: 1px solid #f1f5f9;
    background: white;
    flex-shrink: 0;
    border-radius: 0 0 20px 20px;
    box-sizing: border-box;
  }

  .hero-form-card :global(.form-field) {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .hero-form-card :global(.form-field label) {
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748b;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }

  .hero-form-card :global(.form-field input),
  .hero-form-card :global(.form-field textarea) {
    padding: 0.85rem 1.1rem;
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    font-size: 0.95rem;
    background: white;
    color: #0f172a;
    font-family: var(--font-sans);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .hero-form-card :global(.form-field select) {
    padding: 0.85rem 1.1rem;
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    font-size: 0.95rem;
    background: white;
    color: #0f172a;
    font-family: var(--font-sans);
    width: 100%;
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
  }

  .hero-form-card :global(.form-field input:focus),
  .hero-form-card :global(.form-field textarea:focus),
  .hero-form-card :global(.form-field select:focus) {
    outline: none;
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 3px rgba(225, 29, 72, 0.08);
  }

  .hero-form-card :global(.form-field input::placeholder),
  .hero-form-card :global(.form-field textarea::placeholder) {
    color: #94a3b8;
  }

  .hero-form-card :global(.file-dropzone) {
    border: 2px dashed #d1d5db;
    border-radius: 14px;
    background: rgba(0, 0, 0, 0.01);
    padding: 2.5rem 1.5rem;
    min-height: 160px;
  }

  .hero-form-card :global(.file-dropzone:hover) {
    border-color: var(--primary-accent);
    background: rgba(225, 29, 72, 0.02);
  }

  .hero-form-card :global(.file-upload-icon) {
    width: 48px;
    height: 48px;
    padding: 12px;
    background: #f1f5f9;
    border-radius: 50%;
    color: #64748b;
    opacity: 1;
    margin-bottom: 4px;
  }

  .hero-form-card :global(.file-dropzone-text) {
    font-size: 1rem;
    font-weight: 600;
    color: #0f172a;
  }

  .hero-form-card :global(.file-dropzone-hint) {
    font-size: 0.85rem;
    color: #94a3b8;
  }

  .hero-form-card :global(.form-section) {
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
  }

  .hero-form-card :global(.form-section-header) {
    background: #f8fafc;
    font-size: 0.95rem;
    padding: 0.9rem 1.25rem;
  }

  .hero-submit-btn {
    width: 100%;
    padding: 1rem;
    border-radius: 999px;
    font-size: 1rem;
    font-weight: 500;
    background: #f0f0f0;
    color: #1a1a1a;
    border: none;
    box-shadow: none;
    display: block;
    cursor: pointer;
    box-sizing: border-box;
    transition: background 0.15s ease;
  }

  .hero-submit-btn:hover {
    background: #e5e5e5;
  }

  .hero-submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  /* ── Compliance Form ── */
  .cf-wrapper {
    display: flex;
    justify-content: center;
    width: 100%;
    height: 100%;
    padding: 3rem max(4rem, calc((100% - 1200px) / 2 + 4rem));
    background: #F3F4F6;
    border-radius: var(--radius-lg);
    overflow: auto;
    align-items: center;
    font-family: 'Inter', var(--font-sans);
    box-sizing: border-box;
  }

  .cf-inner {
    display: grid;
    grid-template-columns: 44% 1fr;
    gap: 3rem;
    width: 100%;
    max-width: 1200px;
    align-items: center;
  }

  .cf-left {
    display: flex;
    flex-direction: column;
    gap: 1.1rem;
    padding-left: 3%;
    padding-right: 0.5rem;
  }

  .cf-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    width: fit-content;
    padding: 0.3rem 0.75rem;
    background: color-mix(in srgb, var(--cf-brand) 8%, transparent);
    color: var(--cf-brand);
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-radius: var(--radius-full);
    border: 1px solid color-mix(in srgb, var(--cf-brand) 15%, transparent);
  }

  .cf-heading {
    margin: 0;
    font-size: 3.5rem;
    font-weight: 900;
    line-height: 1.08;
    color: #1A1A1A;
    font-family: 'Inter', var(--font-display);
    letter-spacing: -0.03em;
  }

  .cf-accent {
    color: var(--cf-brand);
  }

  .cf-description {
    margin: 0;
    font-size: 1.05rem;
    line-height: 1.6;
    color: #475569;
  }

  .cf-features {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 0.25rem;
  }

  .cf-feature-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.35rem 0.75rem;
    background: white;
    border: 1px solid #e2e8f0;
    border-radius: var(--radius-full);
    font-size: 0.78rem;
    font-weight: 500;
    color: #334155;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  }

  .cf-feature-badge :global(svg) {
    color: var(--cf-brand);
    flex-shrink: 0;
  }

  .cf-right {
    display: flex;
    align-items: flex-start;
    justify-content: center;
  }

  .cf-card {
    width: 100%;
    max-width: 680px;
    background: white;
    border-radius: 20px;
    box-shadow: 0 32px 64px -16px rgba(0, 0, 0, 0.08), 0 1px 4px rgba(0, 0, 0, 0.03);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  /* Tabs */
  .cf-tabs {
    display: grid;
    grid-template-columns: 1fr 1fr;
    position: relative;
    border-bottom: 1px solid #eee;
    flex-shrink: 0;
  }

  .cf-tab {
    background: none;
    border: none;
    padding: 1.1rem 0.5rem;
    font-size: 0.88rem;
    font-weight: 500;
    color: #999;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.45rem;
    transition: color 0.2s ease;
    font-family: 'Inter', var(--font-sans);
  }

  .cf-tab-active {
    color: var(--cf-brand);
    font-weight: 600;
  }

  .cf-tab svg {
    flex-shrink: 0;
  }

  .cf-tab-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 22px;
    height: 22px;
    padding: 0 6px;
    background: #F3F4F6;
    border: 1px solid #e5e5e5;
    border-radius: var(--radius-full);
    font-size: 0.72rem;
    font-weight: 600;
    color: #666;
  }

  .cf-tab-indicator {
    position: absolute;
    bottom: -1px;
    left: 0;
    width: 50%;
    height: 4px;
    background: var(--cf-brand);
    border-radius: 4px 4px 0 0;
    transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  }

  /* Form body */
  .cf-form {
    display: flex;
    flex-direction: column;
    flex: 1;
    min-height: 0;
  }

  .cf-form-scroll {
    flex: 1;
    overflow-y: auto;
    padding: 2rem 2.25rem 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 2.25rem;
  }

  .cf-section {
    display: flex;
    flex-direction: column;
    gap: 0.85rem;
  }

  .cf-section-header {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
  }

  .cf-section-title {
    margin: 0;
    font-size: 1rem;
    font-weight: 800;
    color: #1A1A1A;
    font-family: 'Inter', var(--font-sans);
  }

  .cf-section-num {
    font-weight: 800;
  }

  .cf-added-badge {
    font-size: 0.7rem;
    font-weight: 600;
    color: #999;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    flex-shrink: 0;
  }

  /* Source toggle pills */
  .cf-source-toggle {
    display: flex;
    background: #F3F4F6;
    border-radius: 14px;
    padding: 4px;
    gap: 0;
  }

  .cf-pill {
    flex: 1;
    padding: 0.65rem 1rem;
    border: none;
    background: transparent;
    border-radius: 11px;
    font-size: 0.85rem;
    font-weight: 500;
    color: #999;
    cursor: pointer;
    transition: all 0.2s ease;
    font-family: 'Inter', var(--font-sans);
    text-align: center;
  }

  .cf-pill-active {
    background: white;
    color: #1A1A1A;
    font-weight: 600;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.06);
  }

  /* URL input */
  .cf-url-row {
    display: flex;
    align-items: center;
    gap: 0;
    background: #F3F4F6;
    border: none;
    border-radius: 14px;
    overflow: hidden;
    transition: box-shadow 0.2s ease;
  }

  .cf-url-row:focus-within {
    box-shadow: 0 0 0 2px color-mix(in srgb, var(--cf-brand) 20%, transparent);
  }

  .cf-url-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0 0.85rem;
    color: #94a3b8;
    flex-shrink: 0;
  }

  .cf-url-input {
    flex: 1;
    border: none;
    padding: 0.9rem 0.5rem 0.9rem 0;
    font-size: 0.9rem;
    background: none;
    color: #1A1A1A;
    font-family: 'Inter', var(--font-sans);
    outline: none;
  }

  .cf-url-input::placeholder {
    color: #b0b0b0;
  }

  .cf-url-plus {
    background: none;
    border: none;
    padding: 0.65rem 0.85rem;
    color: #94a3b8;
    cursor: pointer;
    display: flex;
    align-items: center;
    transition: color 0.15s ease;
  }

  .cf-url-plus:hover {
    color: var(--cf-brand);
  }

  /* Link + file badges */
  .cf-link-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
  }

  .cf-link-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.55rem 0.35rem 0.5rem;
    background: white;
    border: 1px solid #e5e5e5;
    border-radius: var(--radius-full);
    font-size: 0.78rem;
    color: #333;
  }

  .cf-link-badge svg {
    color: #94a3b8;
    flex-shrink: 0;
  }

  .cf-link-badge-text {
    max-width: 180px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .cf-link-badge-remove {
    background: none;
    border: none;
    padding: 2px;
    cursor: pointer;
    color: #b0b0b0;
    display: flex;
    align-items: center;
    border-radius: 50%;
    transition: all 0.12s ease;
    margin-left: 2px;
  }

  .cf-link-badge-remove:hover {
    background: #fee2e2;
    color: #ef4444;
  }

  /* Dropzone */
  .cf-dropzone {
    border: 2px dashed #d5d5d5;
    border-radius: 16px;
    background: #fafafa;
    padding: 2.5rem 1.5rem;
    min-height: 160px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .cf-dropzone:hover,
  .cf-dragover {
    border-color: var(--cf-brand);
    background: color-mix(in srgb, var(--cf-brand) 2%, white);
  }

  /* Advanced settings card */
  .cf-advanced-card {
    background: #F9FAFB;
    border: 1px solid #eee;
    border-radius: 16px;
    overflow: hidden;
  }

  .cf-advanced-toggle {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    background: none;
    border: none;
    padding: 1rem 1.25rem;
    cursor: pointer;
    transition: background 0.15s ease;
    font-family: 'Inter', var(--font-sans);
  }

  .cf-advanced-toggle:hover {
    background: #f3f4f6;
  }

  .cf-advanced-left {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    color: #94a3b8;
  }

  .cf-advanced-title {
    font-size: 0.92rem;
    font-weight: 700;
    color: #1A1A1A;
  }

  .cf-advanced-icon {
    color: #b0b0b0;
    transition: color 0.15s ease;
  }

  .cf-advanced-toggle:hover .cf-advanced-icon {
    color: #666;
  }

  .cf-advanced-body {
    padding: 0 1.25rem 1.25rem;
    border-top: 1px solid #eee;
  }

  .cf-slider-row {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 1rem;
    padding-top: 1rem;
  }

  .cf-slider-info {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
  }

  .cf-slider-label {
    font-size: 0.88rem;
    font-weight: 700;
    color: #1A1A1A;
    display: block;
  }

  .cf-slider-desc {
    font-size: 0.78rem;
    color: #999;
  }

  .cf-slider {
    width: 100%;
    accent-color: var(--cf-brand);
    margin-top: 0.75rem;
  }

  .cf-slider-value {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--cf-brand);
    white-space: nowrap;
    flex-shrink: 0;
  }

  /* Footer */
  .cf-form-footer {
    padding: 1.25rem 2.25rem 1.75rem;
    border-top: 1px solid #f1f5f9;
    background: white;
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-end;
  }

  .cf-submit-btn {
    padding: 0.9rem 2.5rem;
    border-radius: var(--radius-full);
    font-size: 0.82rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    background: var(--cf-brand);
    color: white;
    border: none;
    cursor: pointer;
    box-shadow: 0 4px 14px color-mix(in srgb, var(--cf-brand) 25%, transparent);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
  }

  .cf-submit-btn:hover {
    transform: scale(1.03);
    box-shadow: 0 6px 20px color-mix(in srgb, var(--cf-brand) 35%, transparent);
  }

  .cf-submit-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    transform: none;
  }

  /* History tab */
  .cf-history {
    flex: 1;
    overflow-y: auto;
    padding: 1.75rem 2.25rem;
  }

  .cf-history-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 3rem 1rem;
    gap: 0.5rem;
  }

  .cf-history-empty h3 {
    margin: 0.5rem 0 0;
    font-size: 1.1rem;
    font-weight: 600;
    color: #1A1A1A;
  }

  .cf-history-empty p {
    margin: 0;
    font-size: 0.88rem;
    color: #999;
  }

  .cf-empty-cta {
    margin-top: 1rem;
    padding: 0.6rem 1.5rem;
    border-radius: var(--radius-full);
    background: var(--cf-brand);
    color: white;
    border: none;
    font-size: 0.82rem;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.15s ease;
  }

  .cf-empty-cta:hover {
    opacity: 0.9;
  }

  .cf-history-list {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
  }

  .cf-history-card {
    display: flex;
    align-items: center;
    gap: 0.85rem;
    padding: 1rem 1.25rem;
    background: white;
    border: 1px solid #e5e5e5;
    border-radius: 1.25rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .cf-history-card:hover {
    border-color: #d1d5db;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  }

  .cf-history-card-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    border-radius: 12px;
    background: #F3F4F6;
    color: #64748b;
    flex-shrink: 0;
  }

  .cf-history-card-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.15rem;
  }

  .cf-history-card-id {
    font-size: 0.88rem;
    font-weight: 600;
    color: #1A1A1A;
  }

  .cf-history-card-time {
    font-size: 0.75rem;
    color: #999;
  }

  .cf-history-card-arrow {
    color: #ccc;
    transition: transform 0.15s ease;
    flex-shrink: 0;
  }

  .cf-history-card:hover .cf-history-card-arrow {
    transform: translateX(3px);
    color: var(--cf-brand);
  }

  /* Dark theme overrides */
  :global([data-theme="dark"]) .cf-wrapper {
    background: var(--bg-secondary);
  }

  :global([data-theme="dark"]) .cf-heading {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .cf-description {
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .cf-feature-badge {
    background: var(--bg-primary);
    border-color: var(--border-color);
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .cf-card {
    background: var(--bg-primary);
    box-shadow: 0 32px 64px -16px rgba(0, 0, 0, 0.4);
  }

  :global([data-theme="dark"]) .cf-tabs {
    border-bottom-color: var(--border-color);
  }

  :global([data-theme="dark"]) .cf-tab {
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .cf-tab-badge {
    background: var(--bg-secondary);
    border-color: var(--border-color);
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .cf-section-title {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .cf-source-toggle {
    background: var(--bg-secondary);
  }

  :global([data-theme="dark"]) .cf-pill-active {
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .cf-url-row {
    background: var(--bg-secondary);
  }

  :global([data-theme="dark"]) .cf-url-input {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .cf-link-badge {
    background: var(--bg-secondary);
    border-color: var(--border-color);
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .cf-dropzone {
    border-color: var(--border-color);
    background: var(--bg-secondary);
  }

  :global([data-theme="dark"]) .cf-advanced-card {
    background: var(--bg-secondary);
    border-color: var(--border-color);
  }

  :global([data-theme="dark"]) .cf-advanced-title {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .cf-advanced-body {
    border-top-color: var(--border-color);
  }

  :global([data-theme="dark"]) .cf-slider-label {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .cf-form-footer {
    border-top-color: var(--border-color);
    background: var(--bg-primary);
  }

  :global([data-theme="dark"]) .cf-history-card {
    background: var(--bg-primary);
    border-color: var(--border-color);
  }

  :global([data-theme="dark"]) .cf-history-card-icon {
    background: var(--bg-secondary);
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .cf-history-card-id {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .cf-history-empty h3 {
    color: var(--text-primary);
  }

  /* ── Success popup ── */
  .success-popup-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.55);
    backdrop-filter: blur(4px);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .success-popup-card {
    background: white;
    border-radius: 24px;
    padding: 3rem 2.5rem;
    max-width: 480px;
    width: 90%;
    text-align: center;
    box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
    animation: scaleIn 0.15s ease-out;
  }

  .success-popup-icon-wrap {
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: #e05252;
    margin: 0 auto 1.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 24px rgba(224, 82, 82, 0.35);
  }

  .success-popup-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f0f0f;
    margin: 0 0 1rem;
    font-family: var(--font-display, 'Outfit', sans-serif);
  }

  .success-popup-body {
    color: #6b6b6b;
    line-height: 1.7;
    margin: 0 0 2rem;
    font-size: 0.95rem;
  }

  .success-popup-body :global(strong) {
    color: #0f0f0f;
    font-weight: 600;
  }

  .success-popup-cta {
    width: 100%;
    padding: 1.1rem;
    border-radius: 14px;
    background: #1a1a1a;
    color: white;
    font-size: 1rem;
    font-weight: 600;
    border: none;
    cursor: pointer;
    transition: background 0.15s ease;
  }

  .success-popup-cta:hover {
    background: #333;
  }

  /* ── Full-page table ── */
  .table-fullpage {
    min-height: 100vh;
    background: #f5f5f5;
    padding: 2.5rem;
    box-sizing: border-box;
  }

  .table-back-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    background: none;
    border: none;
    font-size: 0.875rem;
    color: #6b6b6b;
    cursor: pointer;
    margin-bottom: 1.75rem;
    padding: 0;
    transition: color 0.15s ease;
  }

  .table-back-btn:hover {
    color: #0f0f0f;
  }

  .table-fullpage-card {
    background: white;
    border-radius: 20px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.07);
    max-width: 1200px;
    margin: 0 auto;
    padding: 2.5rem 3rem 2rem;
    overflow: hidden;
  }

  .table-fullpage-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    padding-bottom: 2rem;
    border-bottom: 1px solid #eee;
    margin-bottom: 0;
  }

  .table-fullpage-title {
    font-size: 1.75rem;
    font-weight: 700;
    color: #0f0f0f;
    margin: 0 0 0.35rem;
    font-family: var(--font-display, 'Outfit', sans-serif);
    letter-spacing: -0.01em;
    line-height: 1.2;
  }

  .table-fullpage-subtitle {
    font-size: 0.9rem;
    color: #888;
    margin: 0;
    line-height: 1.4;
  }

  .table-fullpage-controls {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    flex-shrink: 0;
    margin-top: 0.25rem;
  }

  .table-active-badge {
    padding: 0.5rem 1.2rem;
    background: white;
    border: 1.5px solid #e0e0e0;
    border-radius: 999px;
    font-size: 0.85rem;
    font-weight: 600;
    color: #0f0f0f;
    white-space: nowrap;
  }

  .table-refresh-btn-lg {
    width: 38px;
    height: 38px;
    border-radius: 50%;
    border: 1.5px solid #e0e0e0;
    background: white;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    color: #999;
    transition: background 0.15s ease, color 0.15s ease, border-color 0.15s ease;
    padding: 0;
    flex-shrink: 0;
  }

  .table-refresh-btn-lg:hover {
    background: #f5f5f5;
    color: #0f0f0f;
  }

  .table-refresh-btn-lg:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  /* ── Dark mode overrides ── */
  :global([data-theme="dark"]) .hero-form-wrapper {
    background: var(--bg-secondary);
  }

  :global([data-theme="dark"]) .hero-heading {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .hero-description {
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .hero-feature-badge {
    background: var(--bg-secondary);
    border-color: var(--border-color);
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .hero-form-card {
    background: var(--bg-primary);
    box-shadow: 0 4px 32px rgba(0, 0, 0, 0.4), 0 1px 4px rgba(0, 0, 0, 0.2);
  }

  :global([data-theme="dark"]) .hero-form-footer {
    background: var(--bg-primary);
    border-top-color: var(--border-color);
  }

  :global([data-theme="dark"]) .hero-form-card :global(.form-field label) {
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .hero-form-card :global(.form-field input),
  :global([data-theme="dark"]) .hero-form-card :global(.form-field textarea),
  :global([data-theme="dark"]) .hero-form-card :global(.form-field select) {
    background: var(--bg-secondary);
    border-color: var(--border-color);
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .hero-form-card :global(.form-field input::placeholder),
  :global([data-theme="dark"]) .hero-form-card :global(.form-field textarea::placeholder) {
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .hero-form-card :global(.file-dropzone) {
    border-color: var(--border-color);
    background: var(--bg-secondary);
  }

  :global([data-theme="dark"]) .hero-form-card :global(.file-upload-icon) {
    background: var(--bg-secondary);
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .hero-form-card :global(.file-dropzone-text) {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .hero-form-card :global(.file-dropzone-hint) {
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .hero-form-card :global(.form-section) {
    border-color: var(--border-color);
  }

  :global([data-theme="dark"]) .hero-form-card :global(.form-section-header) {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .hero-submit-btn {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .hero-submit-btn:hover {
    background: var(--border-color);
  }

  :global([data-theme="dark"]) .success-popup-card {
    background: var(--bg-primary);
  }

  :global([data-theme="dark"]) .success-popup-title {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .success-popup-body {
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .success-popup-body :global(strong) {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .success-popup-cta {
    background: var(--text-primary);
    color: var(--bg-primary);
  }

  :global([data-theme="dark"]) .site-table th {
    color: var(--text-secondary);
    border-bottom-color: var(--border-color);
  }

  :global([data-theme="dark"]) .site-table td {
    color: var(--text-primary);
    border-bottom-color: var(--border-color);
  }

  :global([data-theme="dark"]) .site-table tbody tr:hover {
    background: var(--bg-secondary);
  }

  :global([data-theme="dark"]) .row-action-btn {
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .row-action-btn:hover {
    background: var(--bg-secondary);
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .table-fullpage {
    background: var(--bg-secondary);
  }

  :global([data-theme="dark"]) .table-fullpage-card {
    background: var(--bg-primary);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.4);
  }

  :global([data-theme="dark"]) .table-fullpage-header {
    border-bottom-color: var(--border-color);
  }

  :global([data-theme="dark"]) .table-fullpage-title {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .table-fullpage-subtitle {
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .table-active-badge {
    background: var(--bg-secondary);
    border-color: var(--border-color);
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .table-refresh-btn-lg {
    background: var(--bg-secondary);
    border-color: var(--border-color);
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .table-refresh-btn-lg:hover {
    background: var(--border-color);
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .table-back-btn {
    color: var(--text-secondary);
  }

  :global([data-theme="dark"]) .table-back-btn:hover {
    color: var(--text-primary);
  }

  :global([data-theme="dark"]) .back-nav-btn:hover {
    background: rgba(255, 255, 255, 0.06);
  }
</style>
