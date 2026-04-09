<script>
  import ModelSelector from "./ModelSelector.svelte";
  import { tick, onMount, onDestroy } from "svelte";
  import { authFetch, authPost, prepareFilesForUpload } from "./utils.js";
  import { renderMarkdown } from "./markdown.js";
  import DynamicPanel from "./DynamicPanel.svelte";
  import { Send, Paperclip, X, Bot, User, Loader2, FileText, Image as ImageIcon, Square, Info, Maximize2, Minimize2, MoreHorizontal, Trash2, Sparkles, Globe, Brain, ImagePlus } from "lucide-svelte";
  import { showToast } from "./toast.js";

  let {
    currentUser = null,
    currentUserDisplayName = null,
    conversationId = null,
    project = null,
    footnote = "",
    onconversationcreated = () => {},
    onmessagesent = () => {},
    onnewchat = () => {},
    onlayoutchange = () => {},
    onagentchange = () => {},
    agentId = null,
    preSelectedAgentId = null,
    initialElements = [],
    onelementschange = () => {},
  } = $props();

  // Use display name if available, otherwise fall back to username
  const displayName = $derived(currentUserDisplayName || currentUser);

  let panelElements = $state(initialElements);
  let frontendEnabled = $state(false);
  let panelState = $state({});
  let chatFlex = $state(1);
  let panelFlex = $state(1);
  let agentWantsCollapse = $state(false);
  let hasNotifiedCollapse = false;

  let messages = $state([]);
  let inputValue = $state("");
  let isLoading = $state(false);
  let lastFailedMessage = $state(null);
  let streamError = $state(false);
  let chatContainer;
  let currentModel = $state("default");
  let currentAgentId = $state(null);
  let currentAgentIcon = $state(null);
  let activeConversationId = $state(null);
  let attachedFiles = $state([]);
  let fileInputRef;
  let isDragging = $state(false);
  let dragCounter = 0;
  let sampleQuestions = $state([]);
  let isFullscreen = $state(false);
  let showInfo = $state(false);
  let showMoreMenu = $state(false);
  let currentAgentName = $state(null);
  let currentAgentColor = $state('var(--agent-color-1, #6366f1)');
  let currentWelcomeMessage = $state(null);
  let autoInvokeEnabled = $state(false);
  let autoInvokePrompt = $state(null);
  let messagesLoaded = false;
  let autoInvokePending = false;
  let autoInvokeTriggered = false;
  let activeReader = null;
  let chatWidthOverride = $state(null);
  let showAgentNameEnabled = $state(false);
  let showStepsEnabled = $state(false);
  let expandedNodes = $state(new Set());

  // --- Table toolbar: CSV download & copy ---
  function parseTableData(table) {
    const rows = [];
    for (const tr of table.querySelectorAll('tr')) {
      const cells = [];
      for (const cell of tr.querySelectorAll('th, td')) {
        cells.push(cell.textContent.trim());
      }
      if (cells.length) rows.push(cells);
    }
    return rows;
  }

  function toCsv(rows) {
    return rows.map(r => r.map(c => {
      if (c.includes(',') || c.includes('"') || c.includes('\n')) {
        return '"' + c.replace(/"/g, '""') + '"';
      }
      return c;
    }).join(',')).join('\n');
  }

  function attachTableToolbarHandlers(root) {
    const container = root || chatContainer;
    if (!container) return;
    for (const wrapper of container.querySelectorAll('.table-wrapper')) {
      const table = wrapper.querySelector('table');
      if (!table) continue;

      const copyBtn = wrapper.querySelector('.table-copy-btn');
      const csvBtn = wrapper.querySelector('.table-csv-btn');

      if (copyBtn && !copyBtn._bound) {
        copyBtn._bound = true;
        copyBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          const rows = parseTableData(table);
          const text = rows.map(r => r.join('\t')).join('\n');
          navigator.clipboard.writeText(text).then(() => {
            const orig = copyBtn.innerHTML;
            copyBtn.textContent = 'Copied!';
            setTimeout(() => { copyBtn.innerHTML = orig; }, 1500);
          });
        });
      }

      if (csvBtn && !csvBtn._bound) {
        csvBtn._bound = true;
        csvBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          const rows = parseTableData(table);
          const csv = toCsv(rows);
          const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
          const url = URL.createObjectURL(blob);
          const a = document.createElement('a');
          a.href = url;
          a.download = 'table.csv';
          document.body.appendChild(a);
          a.click();
          document.body.removeChild(a);
          URL.revokeObjectURL(url);
        });
      }
    }
  }

  // Use MutationObserver to detect when tables appear/reappear in the DOM
  let tableObserver;
  onMount(() => {
    tableObserver = new MutationObserver(() => {
      attachTableToolbarHandlers();
    });
  });

  $effect(() => {
    if (chatContainer && tableObserver) {
      tableObserver.observe(chatContainer, { childList: true, subtree: true });
      // Also handle tables already in the DOM
      attachTableToolbarHandlers();
      return () => tableObserver.disconnect();
    }
  });

  // Tools configuration — visibility driven by agent extras
  const toolsDef = [
    { id: 'files',      icon: Paperclip,  label: 'Attach files',      type: 'action',  extrasKey: 'enable_file_attachments' },
    { id: 'web_search', icon: Globe,      label: 'Web search',        type: 'toggle',  extrasKey: 'enable_web_search' },
    { id: 'deep_think', icon: Brain,      label: 'Deep think',        type: 'toggle',  extrasKey: 'enable_deep_think' },
    { id: 'image_gen',  icon: ImagePlus,  label: 'Generate images',   type: 'toggle',  extrasKey: 'enable_image_gen' },
  ];
  let agentToolConfig = $state({});
  const visibleTools = $derived(toolsDef.filter(t => agentToolConfig[t.extrasKey]));
  const anyStepNames = $derived(messages.some(m => m.role === "assistant" && m.step_name));
  let activeTools = $state({});

  function toggleTool(toolId) {
    activeTools = { ...activeTools, [toolId]: !activeTools[toolId] };
  }

  // Feedback modal state
  let feedbackModal = $state(null); // null | { type: "thumbs_up"|"thumbs_down", messageContent: string, conversationId: number|null }
  let feedbackComment = $state("");
  let feedbackSubmitting = $state(false);
  let copiedMsgId = $state(null);

  async function copyMessage(msg) {
    const id = msg.id ?? msg.content?.slice(0, 40);
    try {
      await navigator.clipboard.writeText(msg.content);
      copiedMsgId = id;
      setTimeout(() => { copiedMsgId = null; }, 2000);
    } catch {
      // Fallback for non-HTTPS
      const el = document.createElement("textarea");
      el.value = msg.content;
      el.style.position = "fixed";
      el.style.opacity = "0";
      document.body.appendChild(el);
      el.select();
      document.execCommand("copy");
      document.body.removeChild(el);
      copiedMsgId = id;
      setTimeout(() => { copiedMsgId = null; }, 2000);
    }
  }

  function openFeedback(type, messageContent) {
    feedbackModal = { type, utterance: messageContent, agentId: currentAgentId };
    feedbackComment = "";
  }

  function closeFeedback() {
    feedbackModal = null;
    feedbackComment = "";
  }

  async function submitFeedback() {
    if (!feedbackModal || !project) return;
    feedbackSubmitting = true;
    try {
      const res = await authPost(`/projects/${encodeURIComponent(project)}/feedback`, {
        agent_id: feedbackModal.agentId || null,
        utterance: feedbackModal.utterance || null,
        feedback_type: feedbackModal.type === "thumbs_up" ? "good" : "bad",
        comments: feedbackComment.trim() || null,
      });
      if (!res.ok) {
        const err = await res.text();
        console.error("Feedback submission failed:", res.status, err);
        return;
      }
      closeFeedback();
    } catch (e) {
      console.error("Failed to submit feedback:", e);
    } finally {
      feedbackSubmitting = false;
    }
  }

  onDestroy(() => {
    if (activeReader) {
      activeReader.cancel().catch(() => {});
      activeReader = null;
    }
  });

  // Decorative agent-distinguishing colors — a stable semantic set of distinct hues for visual differentiation.
  // CSS custom properties with hex fallbacks allow theming overrides.
  const AGENT_COLORS = [
    'var(--agent-color-1, #6366f1)',
    'var(--agent-color-2, #e11d48)',
    'var(--agent-color-3, #f59e0b)',
    'var(--agent-color-4, #10b981)',
    'var(--agent-color-5, #8b5cf6)',
    'var(--agent-color-6, #ec4899)',
    'var(--agent-color-7, #06b6d4)',
    'var(--agent-color-8, #f97316)',
  ];

  // Max file size: 10MB
  const MAX_FILE_SIZE = 10 * 1024 * 1024;
  // Allowed file types
  const ALLOWED_TYPES = [
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
    "application/pdf",
    "text/plain",
    "text/csv",
    "text/markdown",
    "application/json",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  ];

  $effect(() => {
    if (agentId && project) {
      authFetch(`/projects/${encodeURIComponent(project)}/agents`)
        .then(res => res.json())
        .then(data => {
          const agents = data.agents || [];
          const agent = agents.find(a => a.id === agentId)
            || agents.find(a => a.is_default)
            || agents[0];
          if (agent) {
            handleAgentSelect({ detail: { agent, model: agent.name, agent_id: agent.id } });
          }
        })
        .catch(err => console.error("Failed to load agents:", err));
    }
  });

  function notifyElementsChange() {
    onelementschange([...panelElements]);
  }

  function handleFileSelect(event) {
    const files = Array.from(event.target.files || []);
    processFiles(files);
    // Reset file input
    if (fileInputRef) fileInputRef.value = "";
  }

  function removeFile(index) {
    attachedFiles = attachedFiles.filter((_, i) => i !== index);
  }

  function triggerFileInput() {
    fileInputRef?.click();
  }

  function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  }

  function getFileIcon(type) {
    if (type.startsWith("image/")) return "🖼️";
    if (type === "application/pdf") return "📄";
    if (type.startsWith("text/")) return "📝";
    if (type.includes("word")) return "📃";
    return "📎";
  }

  // Drag and drop handlers
  function handleDragEnter(event) {
    event.preventDefault();
    event.stopPropagation();
    dragCounter++;
    if (event.dataTransfer?.types?.includes("Files")) {
      isDragging = true;
    }
  }

  function handleDragLeave(event) {
    event.preventDefault();
    event.stopPropagation();
    dragCounter--;
    if (dragCounter === 0) {
      isDragging = false;
    }
  }

  function handleDragOver(event) {
    event.preventDefault();
    event.stopPropagation();
  }

  function handleDrop(event) {
    event.preventDefault();
    event.stopPropagation();
    dragCounter = 0;
    isDragging = false;

    const files = Array.from(event.dataTransfer?.files || []);
    processFiles(files);
  }

  function processFiles(files) {
    for (const file of files) {
      if (file.size > MAX_FILE_SIZE) {
        showToast(`File "${file.name}" is too large. Max size is 10MB.`, 'error');
        continue;
      }
      if (
        !ALLOWED_TYPES.includes(file.type) &&
        !file.type.startsWith("text/")
      ) {
        showToast(`File type "${file.type || "unknown"}" is not supported.`, 'error');
        continue;
      }
      // Avoid duplicates
      if (
        !attachedFiles.some((f) => f.name === file.name && f.size === file.size)
      ) {
        attachedFiles = [...attachedFiles, file];
      }
    }
  }

  onMount(async () => {
    activeConversationId = conversationId;
    if (conversationId) {
      await loadMessages(conversationId);
    }
    messagesLoaded = true;
    maybeAutoInvoke();
  });

  async function loadMessages(convId) {
    try {
      const response = await authFetch(`/conversations/${convId}/messages`);
      if (response.ok) {
        const data = await response.json();
        messages = data.messages || [];
        await tick();
        scrollToBottom();
      }
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  }

  async function ensureConversation() {
    if (activeConversationId) return activeConversationId;

    // Create a new conversation
    try {
      const response = await authPost("/conversations", { agent_id: currentAgentId });
      if (response.ok) {
        const data = await response.json();
        activeConversationId = data.id;
        // Notify parent that a new conversation was created
        onconversationcreated({
          detail: { conversationId: data.id, conversation: data },
        });
        return data.id;
      }
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
    return null;
  }

  export async function sendMessage(content = null) {
    const isManualInput = content === null;
    const textToSend = isManualInput ? inputValue : content;

    if ((!textToSend.trim() && attachedFiles.length === 0) || isLoading) return;

    // Clear any previous stream error
    streamError = false;
    lastFailedMessage = textToSend;

    const convId = await ensureConversation();
    if (!convId) {
      console.error("No conversation available");
      return;
    }

    // Build user message with file info
    let messageContent = textToSend;
    const filesToSend = [...attachedFiles];

    // Create display message with file attachments info
    const userMessage = {
      role: "user",
      content: messageContent,
      files: filesToSend.map((f) => ({
        name: f.name,
        type: f.type,
        size: f.size,
      })),
    };
    messages = [...messages, userMessage];

    if (isManualInput) {
      inputValue = "";
    }
    attachedFiles = [];
    activeTools = {};
    isLoading = true;

    // Scroll to bottom
    await tick();
    scrollToBottom();

    // Create placeholder for assistant response
    const assistantMessage = { role: "assistant", content: "", agent_name: currentAgentName };
    messages = [...messages, assistantMessage];

    try {
      // Prepare files for upload (convert to base64)
      let preparedFiles = null;
      if (filesToSend.length > 0) {
        preparedFiles = await prepareFilesForUpload(filesToSend);
      }

      const response = await authPost("/chat", {
        message: textToSend,
        conversation_id: convId,
        agent_id: currentAgentId, // Optional
        model: currentModel, // Deprecated, kept for backward compatibility
        files: preparedFiles,
        client_context: {
          ...panelState,
          tools: Object.fromEntries(
            Object.entries(activeTools).filter(([_, v]) => v)
          ),
        },
      });

      if (!response.ok) throw new Error("Network response was not ok");

      await processStream(response);
    } catch (error) {
      console.error("Error:", error);
      // Remove the empty assistant placeholder and show retry UI instead
      messages = messages.slice(0, -1);
      streamError = true;
    } finally {
      isLoading = false;
      // Notify parent that a message was sent (for sidebar refresh)
      onmessagesent({ detail: { conversationId: convId } });
    }
  }

  async function processStream(response) {
    const reader = response.body.getReader();
    activeReader = reader;
    const decoder = new TextDecoder();
    let buffer = "";
    const lastMsg = messages[messages.length - 1];

    try {
    while (true) {
      let done, value;
      try {
        ({ done, value } = await reader.read());
      } catch (readErr) {
        if (readErr.name !== "AbortError") {
          console.error("Stream read error:", readErr);
        }
        break;
      }
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const event = JSON.parse(line);
          if (event.type === "metadata") {
            if (event.step_name) {
              lastMsg.step_name = event.step_name;
            }
            if (event.step_description) {
              lastMsg.step_description = event.step_description;
            }
            if (event.step_name || event.step_description) {
              messages = messages;
            }
          } else if (event.type === "text") {
            lastMsg.content += event.content ?? "";
            messages = messages;
          } else if (event.type === "elements") {
            if (event.elements || event.remove_ids) {
              const existingMap = new Map(panelElements.map((e) => [e.id, e]));

              // Remove specific elements by ID
              if (event.remove_ids && Array.isArray(event.remove_ids)) {
                for (const id of event.remove_ids) {
                  existingMap.delete(id);
                }
              }

              // Add/update elements (empty array with no remove_ids clears all)
              if (event.elements) {
                if (Array.isArray(event.elements) && event.elements.length === 0 && !event.remove_ids) {
                  panelElements = [];
                } else {
                  for (const el of event.elements) {
                    existingMap.set(el.id, el);
                  }
                  panelElements = Array.from(existingMap.values());
                }
              } else {
                panelElements = Array.from(existingMap.values());
              }

              notifyElementsChange();
            }
            if (agentWantsCollapse && panelElements.length > 0 && !hasNotifiedCollapse) {
              hasNotifiedCollapse = true;
              onlayoutchange({ detail: { collapseSidebar: true } });
            }
          } else if (event.type === "file" && event.file) {
            const fileJson = event.file;
            if (fileJson.name && fileJson.content) {
              const byteChars = atob(fileJson.content);
              const byteNums = new Array(byteChars.length);
              for (let i = 0; i < byteChars.length; i++) {
                byteNums[i] = byteChars.charCodeAt(i);
              }
              const blob = new Blob([new Uint8Array(byteNums)], {
                type: fileJson.type || "application/octet-stream",
              });
              const url = URL.createObjectURL(blob);
              if (!lastMsg.files) lastMsg.files = [];
              lastMsg.files.push({
                name: fileJson.name,
                type: fileJson.type || "application/octet-stream",
                size: blob.size,
                url,
              });
            }
          }
        } catch (e) {
          console.error("Failed to parse NDJSON event", e);
        }
      }
      scrollToBottom();
    }
    } finally {
      if (activeReader === reader) activeReader = null;
      reader.releaseLock();
    }
  }

  function maybeAutoInvoke() {
    if (autoInvokePending && messagesLoaded && messages.length === 0 && !isLoading && !autoInvokeTriggered) {
      autoInvokePending = false;
      autoInvokeTriggered = true;
      triggerAutoInvoke();
    }
  }

  async function triggerAutoInvoke() {
    if (!autoInvokeEnabled || !autoInvokePrompt || messages.length > 0 || isLoading) return;

    const convId = await ensureConversation();
    if (!convId) return;

    isLoading = true;
    const assistantMessage = { role: "assistant", content: "", agent_name: currentAgentName };
    messages = [assistantMessage];

    try {
      const response = await authPost("/chat", {
        message: autoInvokePrompt,
        conversation_id: convId,
        agent_id: currentAgentId,
        model: currentModel,
        is_system: true,
      });

      if (!response.ok) throw new Error("Auto-invoke failed");

      await processStream(response);
    } catch (error) {
      console.error("Auto-invoke error:", error);
      messages = [];
    } finally {
      isLoading = false;
      onmessagesent({ detail: { conversationId: convId } });
    }
  }

  function scrollToBottom() {
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }

  function handleKeydown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function handleAgentSelect(event) {
    // ModelSelector sends { agent, model, agent_id }
    currentModel = event?.detail?.model || "default";
    currentAgentId = event?.detail?.agent_id || null;

    const agent = event?.detail?.agent;
    currentAgentIcon = agent?.icon || null;
    currentAgentName = agent?.name || null;
    currentAgentColor = agent?._color || AGENT_COLORS[0];
    frontendEnabled = agent?.extras?.frontend === true;
    console.log("frontend enabled: ", frontendEnabled);

    // Read auto-invoke config
    autoInvokeEnabled = agent?.extras?.auto_invoke === true;
    autoInvokePrompt = agent?.extras?.auto_invoke_prompt || null;

    // Read sample questions and welcome message from agent extras
    sampleQuestions = agent?.extras?.sample_questions || [];
    const welcomeText = (autoInvokeEnabled && autoInvokePrompt) ? null : (agent?.extras?.welcome_message || null);
    currentWelcomeMessage = welcomeText;

    chatWidthOverride = agent?.extras?.chat_width || null;
    showAgentNameEnabled = agent?.extras?.show_agent_name === true;
    showStepsEnabled = agent?.extras?.show_steps === true;

    // Tool visibility from agent extras
    const extras = agent?.extras || {};
    agentToolConfig = {
      enable_file_attachments: extras.enable_file_attachments === true,
      enable_web_search: extras.enable_web_search === true,
      enable_deep_think: extras.enable_deep_think === true,
      enable_image_gen: extras.enable_image_gen === true,
    };
    activeTools = {};

    // Inject welcome message as the first assistant bubble (only on fresh load)
    if (welcomeText && messages.length === 0) {
      messages = [{ id: 'welcome', role: 'assistant', content: welcomeText }];
    }

    // Layout: remember agent preference for sidebar collapse (applied when panel appears)
    agentWantsCollapse = agent?.extras?.collapse_sidebar === true;
    hasNotifiedCollapse = false;

    // Layout: panel ratio (e.g. "1:2", "30:70", "1:3")
    const ratioStr = agent?.extras?.panel_ratio;
    if (ratioStr && typeof ratioStr === "string" && ratioStr.includes(":")) {
      const [left, right] = ratioStr.split(":").map(Number);
      if (left > 0 && right > 0) {
        chatFlex = left;
        panelFlex = right;
      }
    } else {
      chatFlex = 1;
      panelFlex = 1;
    }

    // If the new agent wants sidebar collapsed, notify immediately
    if (agentWantsCollapse) {
      onlayoutchange({ detail: { collapseSidebar: true } });
    }

    // Notify parent of agent change for sidebar filtering
    onagentchange({ detail: { agentId: currentAgentId } });

    // Auto-invoke: defer until messages are confirmed loaded to avoid race conditions
    if (autoInvokeEnabled && autoInvokePrompt) {
      autoInvokePending = true;
      maybeAutoInvoke();
    }
  }

  function handlePanelSendMessage(event) {
    sendMessage(event.detail);
  }
</script>

<main
  class="chat-layout"
  class:fullscreen={isFullscreen}
  ondragenter={handleDragEnter}
  ondragleave={handleDragLeave}
  ondragover={handleDragOver}
  ondrop={handleDrop}
>
  {#if isDragging}
    <div class="drop-overlay">
      <div class="drop-content">
        <Paperclip size={48} strokeWidth={1.5} />
        <div class="drop-text">Drop files here</div>
        <div class="drop-hint">Images, PDFs, text files, and more</div>
      </div>
    </div>
  {/if}

  <div class="chat-area" style="flex: {chatFlex};">
    <!-- Floating glassmorphic chat header -->
    <div class="chat-header">
      <div class="chat-header-left">
        {#if currentAgentIcon}
          <div class="agent-avatar-header" style="background: {currentAgentColor}">
            <img src={currentAgentIcon} alt="" />
          </div>
        {:else if currentAgentName}
          <div class="agent-avatar-header agent-avatar-default">
            <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
              <rect width="64" height="64" rx="16" fill="#f5f5f5"/>
              <circle cx="20" cy="18" r="2.5" fill="#dc2626" opacity="0.9"/><circle cx="44" cy="18" r="2.5" fill="#dc2626" opacity="0.9"/><circle cx="12" cy="32" r="2" fill="#dc2626" opacity="0.6"/><circle cx="52" cy="32" r="2" fill="#dc2626" opacity="0.6"/><circle cx="20" cy="46" r="2.5" fill="#dc2626" opacity="0.9"/><circle cx="44" cy="46" r="2.5" fill="#dc2626" opacity="0.9"/>
              <line x1="20" y1="18" x2="44" y2="18" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="20" y1="18" x2="12" y2="32" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="44" y1="18" x2="52" y2="32" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="12" y1="32" x2="20" y2="46" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="52" y1="32" x2="44" y2="46" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="20" y1="46" x2="44" y2="46" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="20" y1="18" x2="44" y2="46" stroke="#dc2626" stroke-width="0.5" opacity="0.2"/><line x1="44" y1="18" x2="20" y2="46" stroke="#dc2626" stroke-width="0.5" opacity="0.2"/>
              <rect x="28" y="22" width="8" height="14" rx="4" stroke="#dc2626" stroke-width="1.8" opacity="0.85"/><path d="M24 36v2a8 8 0 0 0 16 0v-2" stroke="#dc2626" stroke-width="1.8" stroke-linecap="round" opacity="0.85"/><line x1="32" y1="46" x2="32" y2="50" stroke="#dc2626" stroke-width="1.8" stroke-linecap="round" opacity="0.85"/><line x1="28" y1="50" x2="36" y2="50" stroke="#dc2626" stroke-width="1.8" stroke-linecap="round" opacity="0.85"/>
            </svg>
          </div>
        {/if}
        <div class="chat-header-info">
          {#if currentAgentName}
            <span class="chat-agent-name">{currentAgentName}</span>
          {:else if !agentId}
            <div class="model-selector-wrapper">
              <ModelSelector {project} {preSelectedAgentId} onselect={handleAgentSelect} />
            </div>
          {/if}
        </div>
      </div>
      <div class="chat-header-actions">
        {#if currentAgentName}
          <div class="info-wrapper"
            onmouseenter={() => showInfo = true}
            onmouseleave={() => showInfo = false}
          >
            <button class="header-icon-btn">
              <Info size={16} />
            </button>
            {#if showInfo}
              <div class="info-tooltip">
                <strong>{currentAgentName}</strong>
              </div>
            {/if}
          </div>
        {/if}
        <button class="header-icon-btn" onclick={() => isFullscreen = !isFullscreen} title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}>
          {#if isFullscreen}
            <Minimize2 size={16} />
          {:else}
            <Maximize2 size={16} />
          {/if}
        </button>
        <div class="more-wrapper">
          <button class="header-icon-btn" onclick={() => showMoreMenu = !showMoreMenu}>
            <MoreHorizontal size={16} />
          </button>
          {#if showMoreMenu}
            <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
            <div class="more-backdrop" role="presentation" onclick={() => showMoreMenu = false}></div>
            <div class="more-menu">
              <button class="more-menu-item more-menu-danger" onclick={() => { messages = []; showMoreMenu = false; }}>
                <Trash2 size={14} />
                <span>Clear Chat</span>
              </button>
              <button class="more-menu-item" onclick={() => { onnewchat(); showMoreMenu = false; }}>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
                <span>New Chat</span>
              </button>
            </div>
          {/if}
        </div>
      </div>
    </div>

    <div class="chat-scroll-area" bind:this={chatContainer}>
      {#if messages.length === 0}
        <div class="content-centered" style:max-width={chatWidthOverride ? `${chatWidthOverride}px` : null}>
          <div class="greeting">
            <h1>
              Hello{#if displayName}, {displayName}{/if}
            </h1>
            {#if currentWelcomeMessage}
              <p class="welcome-message">{currentWelcomeMessage}</p>
            {/if}
          </div>

        </div>
      {:else}
        <div class="messages-list" style:max-width={chatWidthOverride ? `${chatWidthOverride}px` : null}>
          {#each messages as msg}
            <div class="message {msg.role}">
              <div class="message-content">
                {#if msg.role === "assistant"}
                  {#if currentAgentIcon}
                    <img src={currentAgentIcon} alt="" class="avatar assistant" />
                  {:else}
                    <div class="avatar assistant agent-avatar-default-sm">
                      <svg viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <rect width="64" height="64" rx="16" fill="#f5f5f5"/>
                        <circle cx="20" cy="18" r="2.5" fill="#dc2626" opacity="0.9"/><circle cx="44" cy="18" r="2.5" fill="#dc2626" opacity="0.9"/><circle cx="12" cy="32" r="2" fill="#dc2626" opacity="0.6"/><circle cx="52" cy="32" r="2" fill="#dc2626" opacity="0.6"/><circle cx="20" cy="46" r="2.5" fill="#dc2626" opacity="0.9"/><circle cx="44" cy="46" r="2.5" fill="#dc2626" opacity="0.9"/>
                        <line x1="20" y1="18" x2="44" y2="18" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="20" y1="18" x2="12" y2="32" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="44" y1="18" x2="52" y2="32" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="12" y1="32" x2="20" y2="46" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="52" y1="32" x2="44" y2="46" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="20" y1="46" x2="44" y2="46" stroke="#dc2626" stroke-width="0.8" opacity="0.35"/><line x1="20" y1="18" x2="44" y2="46" stroke="#dc2626" stroke-width="0.5" opacity="0.2"/><line x1="44" y1="18" x2="20" y2="46" stroke="#dc2626" stroke-width="0.5" opacity="0.2"/>
                        <rect x="28" y="22" width="8" height="14" rx="4" stroke="#dc2626" stroke-width="1.8" opacity="0.85"/><path d="M24 36v2a8 8 0 0 0 16 0v-2" stroke="#dc2626" stroke-width="1.8" stroke-linecap="round" opacity="0.85"/><line x1="32" y1="46" x2="32" y2="50" stroke="#dc2626" stroke-width="1.8" stroke-linecap="round" opacity="0.85"/><line x1="28" y1="50" x2="36" y2="50" stroke="#dc2626" stroke-width="1.8" stroke-linecap="round" opacity="0.85"/>
                      </svg>
                    </div>
                  {/if}
                {:else}
                  <div class="avatar user">
                    <User size={18} />
                  </div>
                {/if}
                <div class="message-stack">
                  {#if msg.role === "assistant" && showAgentNameEnabled && currentAgentName}
                    <span class="msg-agent-name">{currentAgentName}</span>
                  {/if}
                  {#if showStepsEnabled && msg.role === "assistant" && anyStepNames}
                    {@const assistantMsgs = messages.filter(m => m.role === "assistant")}
                    {@const assistantIdx = assistantMsgs.indexOf(msg)}
                    {@const msgIdx = messages.indexOf(msg)}
                    {@const stepName = msg.step_name || `Step ${assistantIdx + 1}`}
                    {@const priorSteps = assistantMsgs.slice(0, assistantIdx).map((m, i) => ({ name: m.step_name || `Step ${i + 1}`, description: m.step_description || "" }))}
                    {@const allSteps = [...priorSteps, { name: stepName, description: msg.step_description || "" }]}
                    <div class="node-progress">
                      <button
                        class="node-progress-toggle"
                        type="button"
                        onclick={(e) => {
                          const el = e.currentTarget.parentElement;
                          el.classList.toggle('open');
                        }}
                      >
                        <span class="node-progress-current">{stepName}</span>
                        {#if allSteps.length > 1}
                          <svg class="node-progress-chevron" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="6 9 12 15 18 9"></polyline>
                          </svg>
                        {/if}
                      </button>
                      {#if allSteps.length > 1}
                        <div class="node-progress-dropdown">
                          {#each allSteps as step, i}
                            {@const nodeKey = `${msgIdx}-${i}`}
                            <div
                              class="node-progress-item"
                              class:current={i === allSteps.length - 1}
                            >
                              <div class="node-dot-col">
                                <span class="node-dot"></span>
                                {#if i < allSteps.length - 1}
                                  <span class="node-line"></span>
                                {/if}
                              </div>
                              <div class="node-info">
                                {#if step.description}
                                  <button
                                    class="node-label-btn"
                                    type="button"
                                    onclick={() => {
                                      if (expandedNodes.has(nodeKey)) {
                                        expandedNodes.delete(nodeKey);
                                      } else {
                                        expandedNodes.add(nodeKey);
                                      }
                                      expandedNodes = new Set(expandedNodes);
                                    }}
                                  >
                                    <span class="node-label">{step.name}</span>
                                    <svg class="node-expand-icon" class:rotated={expandedNodes.has(nodeKey)} width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                      <polyline points="6 9 12 15 18 9"></polyline>
                                    </svg>
                                  </button>
                                {:else}
                                  <span class="node-label">{step.name}</span>
                                {/if}
                                {#if expandedNodes.has(nodeKey) && step.description}
                                  <p class="node-description">{step.description}</p>
                                {/if}
                              </div>
                            </div>
                          {/each}
                        </div>
                      {/if}
                    </div>
                  {/if}
                  <div class="bubble">
                  {#if msg.files && msg.files.length > 0}
                    <div class="message-files">
                      {#each msg.files as file}
                        <div class="message-file">
                          <span class="file-icon-wrap">
                            {#if file.type?.startsWith("image/")}
                              <ImageIcon size={14} />
                            {:else}
                              <FileText size={14} />
                            {/if}
                          </span>
                          {#if file.url}
                            <a
                              href={file.url}
                              download={file.name}
                              class="file-name download-link"
                              title="Click to download"
                            >
                              {file.name}
                            </a>
                          {:else}
                            <span class="file-name">{file.name}</span>
                          {/if}
                        </div>
                      {/each}
                    </div>
                  {/if}
                  {#if msg.role === "assistant" && !msg.content.trim() && isLoading}
                    <div class="loading-dots">
                      <span></span><span></span><span></span>
                    </div>
                  {:else}
                    <div class="text markdown-content">
                      {@html renderMarkdown(msg.content)}
                    </div>
                  {/if}
                  {#if msg.role === "assistant" && msg.content.trim() && isLoading && msg === messages[messages.length - 1]}
                    <div class="streaming-indicator">
                      <Loader2 size={14} />
                    </div>
                  {/if}
                  </div>
                  {#if msg.role === "assistant" && msg.content.trim()}
                    <div class="message-actions">
                      <button class="message-action-btn" class:copied={copiedMsgId === (msg.id ?? msg.content?.slice(0, 40))} type="button" title={copiedMsgId === (msg.id ?? msg.content?.slice(0, 40)) ? "Copied!" : "Copy"} onclick={() => copyMessage(msg)}>
                        {#if copiedMsgId === (msg.id ?? msg.content?.slice(0, 40))}
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <polyline points="20 6 9 17 4 12"></polyline>
                          </svg>
                        {:else}
                          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                            <rect x="9" y="9" width="13" height="13" rx="2"></rect>
                            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                          </svg>
                        {/if}
                      </button>
                      <button class="message-action-btn" type="button" title="Like" onclick={() => openFeedback("thumbs_up", msg.content)}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M7 10v12"></path>
                          <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88z"></path>
                        </svg>
                      </button>
                      <button class="message-action-btn" type="button" title="Dislike" onclick={() => openFeedback("thumbs_down", msg.content)}>
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M17 14V2"></path>
                          <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88z"></path>
                        </svg>
                      </button>
                    </div>
                  {/if}
                </div>
              </div>
            </div>
          {/each}
          {#if streamError}
            <div class="stream-error">
              <span class="stream-error-text">Message failed to send.</span>
              <button
                class="stream-retry-btn"
                onclick={() => {
                  streamError = false;
                  if (lastFailedMessage) sendMessage(lastFailedMessage);
                }}
              >Try again</button>
              <button
                class="stream-dismiss-btn"
                onclick={() => streamError = false}
              >Dismiss</button>
            </div>
          {/if}
        </div>
      {/if}
    </div>

    <div class="input-container-wrapper">
      <div class="input-container" style:max-width={chatWidthOverride ? `${Math.round(chatWidthOverride * 0.875)}px` : null}>
        <!-- Suggested prompts shown above input when there are sample questions -->
        {#if sampleQuestions.length > 0 && messages.length === 0}
          <div class="prompts-row">
            {#each sampleQuestions.slice(0, 3) as q}
              <button
                class="prompt-chip"
                onclick={() => {
                  inputValue = (q.description || q.title).trim();
                  sendMessage();
                }}
              >
                <Sparkles size={11} class="prompt-sparkle" />
                <span>{q.title}</span>
              </button>
            {/each}
          </div>
        {/if}

        <div class="input-card">
          {#if attachedFiles.length > 0}
            <div class="attached-files">
              {#each attachedFiles as file, index}
                <div class="attached-file">
                  <span class="file-icon-wrap">
                    {#if file.type?.startsWith("image/")}
                      <ImageIcon size={14} />
                    {:else}
                      <FileText size={14} />
                    {/if}
                  </span>
                  <span class="file-name">{file.name}</span>
                  <span class="file-size">{formatFileSize(file.size)}</span>
                  <button
                    class="remove-file"
                    onclick={() => removeFile(index)}
                    title="Remove file"
                  >
                    <X size={14} />
                  </button>
                </div>
              {/each}
            </div>
          {/if}
          <div class="input-header">
            <textarea
              bind:value={inputValue}
              onkeydown={handleKeydown}
              placeholder="Reply..."
              rows="1"
            ></textarea>
          </div>
          <div class="input-actions">
            <input
              type="file"
              bind:this={fileInputRef}
              onchange={handleFileSelect}
              multiple
              accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.txt,.csv,.md,.json,.doc,.docx"
              style="display: none;"
            />
            {#each visibleTools as tool}
              <button
                class="action-btn"
                class:tool-active={tool.type === 'toggle' && activeTools[tool.id]}
                onclick={() => {
                  if (tool.id === 'files') triggerFileInput();
                  else if (tool.type === 'toggle') toggleTool(tool.id);
                }}
                title={tool.label}
                disabled={isLoading}
              >
                <svelte:component this={tool.icon} size={18} />
              </button>
            {/each}
            <div class="spacer"></div>
            <button
              class="send-btn"
              onclick={() => sendMessage()}
              disabled={isLoading}
            >
              {#if isLoading}
                <Square size={16} />
              {:else}
                <Send size={18} />
              {/if}
            </button>
          </div>
        </div>
      </div>
      {#if footnote}
        <div class="footnote-text">{footnote}</div>
      {/if}
    </div>
  </div>

  {#if panelElements.length > 0}
    <div class="panel-container" style="flex: {panelFlex};">
      <DynamicPanel
        elements={panelElements}
        bind:componentState={panelState}
        onsendMessage={handlePanelSendMessage}
      />
    </div>
  {/if}
</main>

{#if feedbackModal}
  <div class="feedback-overlay" onclick={closeFeedback}>
    <div class="feedback-modal" onclick={(e) => e.stopPropagation()}>
      <div class="feedback-modal-header">
        <span class="feedback-modal-icon">
          {#if feedbackModal.type === "thumbs_up"}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M7 10v12"/><path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88z"/>
            </svg>
          {:else}
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 14V2"/><path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88z"/>
            </svg>
          {/if}
        </span>
        <h3 class="feedback-modal-title">{feedbackModal.type === "thumbs_up" ? "What did you like?" : "What went wrong?"}</h3>
        <button class="feedback-modal-close" onclick={closeFeedback} type="button">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <textarea
        class="feedback-textarea"
        placeholder="Add a comment (optional)"
        bind:value={feedbackComment}
        rows="4"
      ></textarea>
      <div class="feedback-modal-footer">
        <button class="feedback-cancel-btn" onclick={closeFeedback} type="button">Cancel</button>
        <button class="feedback-submit-btn" onclick={submitFeedback} disabled={feedbackSubmitting} type="button">
          {feedbackSubmitting ? "Submitting…" : "Submit"}
        </button>
      </div>
    </div>
  </div>
{/if}

<style>
  /* Fullscreen mode */
  .chat-layout.fullscreen {
    position: fixed;
    inset: 0;
    z-index: 9999;
    width: 100vw;
    height: 100vh;
  }

  /* Floating chat header */
  .chat-header {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.875rem 1.5rem;
    background: var(--chat-header-bg, rgba(2, 6, 23, 0.85));
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
  }

  .chat-header-left {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .agent-avatar-header {
    width: 44px;
    height: 44px;
    border-radius: var(--radius-2xl);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    font-size: 1rem;
    font-weight: 700;
    color: white;
    box-shadow: var(--shadow-md);
    overflow: hidden;
  }

  .agent-avatar-header img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .agent-avatar-default {
    background: transparent !important;
    padding: 0;
    overflow: hidden;
  }

  .agent-avatar-default svg {
    width: 100%;
    height: 100%;
    border-radius: var(--radius-2xl);
  }

  .agent-avatar-default-sm {
    background: transparent !important;
    border: none !important;
    padding: 0;
    overflow: hidden;
  }

  .agent-avatar-default-sm svg {
    width: 100%;
    height: 100%;
    border-radius: 50%;
  }

  .chat-header-info {
    display: flex;
    flex-direction: column;
  }

  .chat-agent-name {
    font-size: 1rem;
    font-weight: 700;
    color: var(--text-primary);
  }

  .model-selector-wrapper {
    display: flex;
    align-items: center;
  }

  .chat-header-actions {
    display: flex;
    align-items: center;
    gap: 0.25rem;
  }

  .header-icon-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 34px;
    height: 34px;
    border-radius: var(--radius-xl);
    border: none;
    background: transparent;
    color: var(--text-secondary);
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
  }

  .header-icon-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  /* Info tooltip */
  .info-wrapper {
    position: relative;
  }

  .info-tooltip {
    position: absolute;
    top: calc(100% + 8px);
    right: 0;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    padding: 0.75rem 1rem;
    width: 200px;
    box-shadow: var(--shadow-lg);
    z-index: 50;
    font-size: 0.8rem;
    color: var(--text-secondary);
  }

  .info-tooltip strong {
    display: block;
    color: var(--text-primary);
    margin-bottom: 0.25rem;
  }

  /* More menu */
  .more-wrapper {
    position: relative;
  }

  .more-backdrop {
    position: fixed;
    inset: 0;
    z-index: 40;
  }

  .more-menu {
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    box-shadow: var(--shadow-lg);
    padding: 0.35rem 0;
    min-width: 160px;
    z-index: 50;
  }

  .more-menu-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.5rem 1rem;
    border: none;
    background: transparent;
    color: var(--text-secondary);
    font-size: 0.85rem;
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
    text-align: left;
  }

  .more-menu-item:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .more-menu-danger {
    color: #f87171;
  }

  .more-menu-danger:hover {
    background: rgba(239, 68, 68, 0.1);
    color: #f87171;
  }

  /* Suggested prompts above input */
  .prompts-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 0.75rem;
    justify-content: center;
  }

  .prompt-chip {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding: 0.4rem 0.875rem;
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-xl);
    color: var(--text-secondary);
    font-size: 0.75rem;
    font-weight: 700;
    cursor: pointer;
    transition: background 0.12s ease, border-color 0.12s ease, color 0.12s ease;
  }

  .prompt-chip:hover {
    border-color: rgba(225, 29, 72, 0.3);
    background: rgba(225, 29, 72, 0.05);
    color: #fb7185;
  }

  .prompt-chip :global(.prompt-sparkle) {
    color: #f59e0b;
  }

  .chat-layout {
    flex: 1;
    display: flex;
    flex-direction: row;
    position: relative;
    background-color: var(--bg-primary);
    overflow: hidden;
  }

  .chat-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    position: relative;
    min-width: 0;
  }

  .panel-container {
    flex: 1;
    border-left: 1px solid var(--border-color);
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }

  .mobile-new-chat {
    display: none;
  }

  .chat-scroll-area {
    flex: 1;
    overflow-y: auto;
    padding-top: 76px;
    padding-bottom: 20px;
  }

  .content-centered {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    min-height: 100%;
    gap: var(--spacing-xl);
    max-width: 800px;
    margin: 0 auto;
    width: 100%;
    padding: 2rem;
  }

  .greeting {
    text-align: center;
    margin-bottom: var(--spacing-lg);
  }

  h1 {
    font-weight: 500;
    font-size: 2rem;
    color: var(--text-primary);
    font-family: var(--font-display);
  }

  .project-context {
    margin-top: var(--spacing-sm);
    color: var(--text-secondary);
    font-size: 1rem;
  }

  .welcome-message {
    margin-top: var(--spacing-sm);
    color: var(--text-secondary);
    font-size: 1rem;
    max-width: 600px;
    line-height: 1.6;
  }

  .project-context strong {
    color: var(--primary-accent);
  }

  /* Stream error / retry */
  .stream-error {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.5rem 0.75rem;
    margin: 0.25rem 0;
    background: rgba(220, 38, 38, 0.08);
    border: 1px solid rgba(220, 38, 38, 0.25);
    border-radius: var(--radius-md);
    font-size: 0.85rem;
  }
  .stream-error-text {
    color: #dc2626;
    flex: 1;
  }
  .stream-retry-btn {
    background: #dc2626;
    color: #fff;
    border: none;
    border-radius: var(--radius-sm);
    padding: 0.25rem 0.6rem;
    font-size: 0.8rem;
    cursor: pointer;
    transition: background 0.12s ease;
  }
  .stream-retry-btn:hover {
    background: #b91c1c;
  }
  .stream-dismiss-btn {
    background: none;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    padding: 0.25rem 0.6rem;
    font-size: 0.8rem;
    cursor: pointer;
    color: var(--text-secondary);
    transition: background 0.12s ease;
  }
  .stream-dismiss-btn:hover {
    background: var(--bg-hover);
  }

  /* Messages */
  .messages-list {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    padding: 1rem;
    width: 100%;
    max-width: 800px;
    margin: 0 auto;
  }

  .message.user + .message.assistant,
  .message.assistant + .message.user {
    margin-top: 0.8rem;
  }

  .message {
    display: flex;
    width: 100%;
  }

  .message.user {
    justify-content: flex-end;
  }

  .message-content {
    display: flex;
    gap: 0.6rem;
    max-width: 80%;
    align-items: flex-start;
  }

  .message.user .message-content {
    flex-direction: row-reverse;
  }

  .avatar {
    width: 40px;
    height: 40px;
    border-radius: var(--radius-xl);
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .avatar.assistant {
    background-color: var(--bg-primary);
    border: 1px solid var(--border-color);
    color: var(--text-secondary);
    object-fit: cover;
  }

  .avatar.user {
    background-color: var(--primary-accent);
    color: white;
  }

  .message-stack {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }

  .node-progress {
    position: relative;
    margin-bottom: 0.2rem;
  }

  .node-progress-toggle {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    background: none;
    border: none;
    padding: 0.15rem 0.3rem;
    border-radius: var(--radius-sm, 0.375rem);
    cursor: pointer;
    font-family: var(--font-sans, 'Inter', sans-serif);
    transition: background 0.12s ease;
  }

  .node-progress-toggle:hover {
    background: rgba(0, 0, 0, 0.04);
  }

  .node-progress-current {
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text-secondary, #6b6b6b);
  }

  .node-progress-chevron {
    color: var(--text-secondary, #6b6b6b);
    transition: transform 0.15s ease-out;
    flex-shrink: 0;
  }

  .node-progress.open .node-progress-chevron {
    transform: rotate(180deg);
  }

  .node-progress-dropdown {
    display: none;
    padding: 0.5rem 0.6rem;
    margin-top: 0.25rem;
    background: var(--bg-primary, #ffffff);
    border: 1px solid var(--border-color, #e5e5e5);
    border-radius: var(--radius-md, 0.5rem);
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
    animation: slideUp 0.12s ease;
  }

  .node-progress.open .node-progress-dropdown {
    display: block;
  }

  .node-progress-item {
    display: flex;
    align-items: stretch;
    gap: 0.5rem;
  }

  .node-dot-col {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 12px;
    flex-shrink: 0;
  }

  .node-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: var(--border-color, #e5e5e5);
    flex-shrink: 0;
    margin-top: 0.35rem;
  }

  .node-progress-item.current .node-dot {
    background: #dc2626;
    box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.15);
  }

  .node-line {
    width: 2px;
    flex: 1;
    background: var(--border-color, #e5e5e5);
    min-height: 12px;
  }

  .node-info {
    display: flex;
    flex-direction: column;
    padding-bottom: 0.25rem;
    min-width: 0;
  }

  .node-label-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    font-family: var(--font-sans, 'Inter', sans-serif);
  }

  .node-label {
    font-size: 0.75rem;
    color: var(--text-secondary, #6b6b6b);
    line-height: 1.4;
  }

  .node-progress-item.current .node-label {
    color: #dc2626;
    font-weight: 600;
  }

  .node-expand-icon {
    color: var(--text-secondary, #6b6b6b);
    transition: transform 0.12s ease;
    flex-shrink: 0;
  }

  .node-expand-icon.rotated {
    transform: rotate(180deg);
  }

  .node-description {
    font-size: 0.7rem;
    color: var(--text-secondary, #6b6b6b);
    margin: 0.15rem 0 0.1rem;
    line-height: 1.4;
    opacity: 0.8;
  }

  .msg-agent-name {
    font-size: 0.8rem;
    font-weight: 600;
    color: var(--text-primary, #0f0f0f);
    white-space: nowrap;
  }

  .message.user .message-stack {
    align-items: flex-end;
  }

  .bubble {
    padding: 1rem 1.5rem;
    border-radius: var(--radius-2xl);
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .message.assistant .bubble {
    background-color: var(--bg-primary);
    border: 1px solid var(--border-strong);
    color: var(--text-primary);
    border-top-left-radius: var(--radius-sm);
  }

  .message.user .bubble {
    background-color: var(--primary-accent);
    color: white;
    border-top-right-radius: var(--radius-sm);
  }

  .message-actions {
    display: flex;
    align-items: center;
    gap: 0.1rem;
    padding-left: 0.1rem;
  }

  .message-action-btn {
    width: 28px;
    height: 28px;
    border: none;
    border-radius: 6px;
    background: transparent;
    color: var(--text-muted);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background-color 0.12s ease, color 0.12s ease;
  }

  .message-action-btn:hover {
    background: rgba(255, 255, 255, 0.06);
    color: var(--text-primary);
  }

  .message-action-btn:active {
    transform: scale(0.92);
  }

  .text {
    font-size: 0.875rem;
    line-height: 1.55;
    color: inherit;
    white-space: normal;
    overflow-wrap: anywhere;
    word-break: break-word;
  }

  /* Input Area */
  .input-container-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0.75rem 1rem 1.25rem 1rem;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
  }

  .footnote-text {
    font-size: 0.7rem;
    /* Use text-muted directly; opacity: 0.7 compound was insufficient for WCAG AA */
    color: var(--text-muted);
    text-align: center;
    margin-top: 0.4rem;
  }

  .input-container {
    width: 100%;
    max-width: 700px;
  }

  .input-card {
    background: var(--bg-primary);
    border-radius: var(--radius-2xl);
    padding: 0.75rem 1rem;
    border: 1px solid var(--border-strong);
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .input-card:focus-within {
    border-color: var(--primary-accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }

  .input-header {
    margin-bottom: 0.5rem;
  }

  textarea {
    width: 100%;
    background: transparent;
    border: none;
    outline: none;
    resize: none;
    color: var(--text-primary);
    font-size: 1rem;
    font-family: inherit;
    min-height: 24px;
    max-height: 200px;
    line-height: 1.5;
  }

  textarea::placeholder {
    color: var(--text-muted);
  }

  .input-actions {
    display: flex;
    gap: 0.25rem;
    align-items: center;
  }

  .action-btn {
    width: 36px;
    height: 36px;
    border-radius: var(--radius-lg);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-muted);
    transition: background 0.15s, color 0.15s;
    background: transparent;
    border: none;
    cursor: pointer;
  }

  .action-btn:hover {
    background: rgba(255, 255, 255, 0.06);
    color: var(--text-primary);
  }

  .action-btn.tool-active {
    color: var(--primary-accent);
    background: rgba(245, 158, 11, 0.10);
  }

  .action-btn.tool-active:hover {
    background: rgba(245, 158, 11, 0.16);
  }

  .spacer {
    flex: 1;
  }

  .send-btn {
    width: 40px;
    height: 40px;
    border-radius: var(--radius-xl);
    background-color: var(--primary-accent);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    cursor: pointer;
    transition: background 0.15s, transform 0.12s;
  }

  .send-btn:hover {
    background: var(--primary-accent-hover);
    transform: scale(1.05);
  }

  .send-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    transform: none;
  }

  /* Attached Files Preview */
  .attached-files {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-color);
  }

  .attached-file {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-md);
    font-size: 0.85rem;
  }

  .file-icon-wrap {
    display: flex;
    align-items: center;
    color: var(--text-muted);
  }

  .attached-file .file-name {
    color: var(--text-primary);
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .attached-file .file-size {
    color: var(--text-muted);
    font-size: 0.75rem;
  }

  .attached-file .remove-file {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0;
    margin-left: 0.25rem;
    display: flex;
    align-items: center;
    transition: color 0.2s;
  }

  .attached-file .remove-file:hover {
    color: var(--primary-accent);
  }

  /* Message Files */
  .message-files {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .message-file {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.35rem 0.6rem;
    background: rgba(255, 255, 255, 0.06);
    border-radius: var(--radius-sm);
    font-size: 0.8rem;
  }

  .message-file .file-name {
    color: inherit;
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .message-file .download-link {
    text-decoration: none;
    color: var(--primary-accent);
    font-weight: 500;
  }

  .message-file .download-link:hover {
    text-decoration: underline;
  }

  /* Loading dots */
  .loading-dots {
    display: flex;
    gap: 5px;
    padding: 8px 0;
    align-items: center;
  }

  .loading-dots span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background-color: #fb7185;
    animation: dotBounce 1.4s ease-in-out infinite;
  }

  .loading-dots span:nth-child(2) {
    animation-delay: 0.2s;
  }

  .loading-dots span:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes dotBounce {
    0%,
    80%,
    100% {
      opacity: 0.3;
      transform: scale(0.8);
    }
    40% {
      opacity: 1;
      transform: scale(1);
    }
  }

  /* Drag and Drop Overlay */
  .drop-overlay {
    position: absolute;
    inset: 0;
    background: rgba(225, 29, 72, 0.9);
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-lg);
    border: 3px dashed rgba(255, 255, 255, 0.4);
    margin: 8px;
    animation: dropFadeIn 0.15s ease-out;
  }

  @keyframes dropFadeIn {
    from {
      opacity: 0;
      transform: scale(0.98);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  .drop-content {
    text-align: center;
    color: white;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.75rem;
  }

  .drop-text {
    font-size: 1.5rem;
    font-weight: 600;
  }

  .drop-hint {
    font-size: 0.9rem;
    opacity: 0.8;
  }

  /* Markdown Content Styles */
  .markdown-content {
    font-size: 0.875rem;
    line-height: 1.55;
  }

  .bubble .markdown-content :global(*:first-child) {
    margin-top: 0;
  }

  .bubble .markdown-content :global(*:last-child) {
    margin-bottom: 0;
  }

  .bubble .markdown-content :global(p) {
    margin: 0.4em 0;
  }

  .markdown-content :global(h1),
  .markdown-content :global(h2),
  .markdown-content :global(h3),
  .markdown-content :global(h4),
  .markdown-content :global(h5),
  .markdown-content :global(h6) {
    font-weight: 600;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    color: var(--text-primary);
    line-height: 1.25;
  }

  .markdown-content :global(h1) {
    font-size: 1.75em;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.3em;
  }

  .markdown-content :global(h2) {
    font-size: 1.5em;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0.3em;
  }

  .markdown-content :global(h3) {
    font-size: 1.25em;
  }

  .markdown-content :global(h4) {
    font-size: 1.1em;
  }

  .markdown-content :global(h5),
  .markdown-content :global(h6) {
    font-size: 1em;
  }

  .markdown-content :global(p) {
    margin: 0.75em 0;
  }

  .markdown-content :global(ul),
  .markdown-content :global(ol) {
    margin: 0.75em 0;
    padding-left: 2em;
  }

  .markdown-content :global(li) {
    margin: 0.25em 0;
  }

  .markdown-content :global(blockquote) {
    margin: 0.75em 0;
    padding: 0.5em 1em;
    border-left: 4px solid var(--border-color);
    background: var(--bg-secondary);
    color: var(--text-secondary);
  }

  .markdown-content :global(code) {
    background: rgba(255, 255, 255, 0.06);
    padding: 0.2em 0.4em;
    border-radius: 4px;
    font-size: 0.9em;
    font-family: "Courier New", monospace;
    color: var(--text-primary);
  }

  .markdown-content :global(pre) {
    background: var(--bg-elevated);
    border: 1px solid var(--border-color);
    padding: 1em;
    border-radius: var(--radius-lg);
    overflow-x: auto;
    margin: 1em 0;
    line-height: 1.45;
  }

  .markdown-content :global(pre code) {
    background: transparent;
    padding: 0;
    border-radius: 0;
    font-size: 0.9em;
    color: inherit;
  }

  .markdown-content :global(.hljs) {
    background: var(--bg-elevated);
    color: #d4d4d4;
  }

  .markdown-content :global(table) {
    border-collapse: collapse;
    margin: 1em 0;
    width: 100%;
    display: block;
    overflow-x: auto;
  }

  .markdown-content :global(thead) {
    background: var(--bg-secondary);
  }

  .markdown-content :global(th),
  .markdown-content :global(td) {
    border: 1px solid var(--border-color);
    padding: 0.5em 0.75em;
    text-align: left;
  }

  .markdown-content :global(th) {
    font-weight: 600;
    background: var(--bg-secondary);
  }

  .markdown-content :global(tr:nth-child(even)) {
    background: rgba(255, 255, 255, 0.02);
  }

  .markdown-content :global(.table-wrapper) {
    position: relative;
    margin: 1em 0;
  }

  .markdown-content :global(.table-wrapper table) {
    margin: 0;
  }

  .markdown-content :global(.table-toolbar) {
    display: flex;
    justify-content: flex-end;
    gap: 0.375rem;
    margin-bottom: 0.375rem;
  }

  .markdown-content :global(.table-action-btn) {
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    font-family: var(--font-sans);
    font-weight: 500;
    color: var(--text-secondary);
    background: transparent;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-sm);
    cursor: pointer;
    transition: background 0.12s ease, color 0.12s ease;
    line-height: 1;
  }

  .markdown-content :global(.table-action-btn:hover) {
    background: rgba(0, 0, 0, 0.04);
    color: var(--text-primary);
  }

  .markdown-content :global(a) {
    color: var(--primary-accent);
    text-decoration: none;
  }

  .markdown-content :global(a:hover) {
    text-decoration: underline;
  }

  .message.user .bubble .markdown-content :global(a) {
    color: white;
    text-decoration: underline;
  }

  .message.user .bubble .markdown-content :global(a:hover) {
    opacity: 0.85;
  }

  .markdown-content :global(img) {
    max-width: 100%;
    height: auto;
    border-radius: var(--radius-md);
    margin: 0.5em 0;
  }

  .markdown-content :global(hr) {
    border: none;
    border-top: 1px solid var(--border-color);
    margin: 1.5em 0;
  }

  .markdown-content :global(strong) {
    font-weight: 600;
  }

  .markdown-content :global(em) {
    font-style: italic;
  }

  .markdown-content :global(del) {
    text-decoration: line-through;
    opacity: 0.7;
  }

  @media (max-width: 1280px) {
    .messages-list {
      max-width: 720px;
    }
    .content-centered {
      max-width: 720px;
      padding: 1.5rem;
    }
    .input-container {
      max-width: 640px;
    }
    .bubble {
      padding: 0.875rem 1.25rem;
    }
    h1 {
      font-size: 1.75rem;
    }
    .chat-header {
      padding: 0.75rem 1.25rem;
    }
    .agent-avatar-header {
      width: 38px;
      height: 38px;
    }
    .chat-agent-name {
      font-size: 0.9rem;
    }
  }

  @media (max-width: 1024px) {
    .messages-list {
      max-width: 640px;
      padding: 0.75rem;
    }
    .content-centered {
      max-width: 640px;
      padding: 1.25rem;
    }
    .input-container {
      max-width: 580px;
    }
    .bubble {
      padding: 0.75rem 1rem;
    }
    .text,
    .markdown-content {
      font-size: 0.9rem;
    }
    h1 {
      font-size: 1.5rem;
    }
    .chat-header {
      padding: 0.625rem 1rem;
    }
    .agent-avatar-header {
      width: 34px;
      height: 34px;
    }
    .chat-agent-name {
      font-size: 0.85rem;
    }
    .input-container-wrapper {
      padding: 0.5rem 0.75rem 1rem;
    }
    textarea {
      font-size: 0.9rem;
    }
    .send-btn {
      width: 36px;
      height: 36px;
    }
    .action-btn {
      width: 32px;
      height: 32px;
    }
  }

  @media (max-width: 768px) {
    .top-bar {
      justify-content: flex-end;
    }

    :global(.top-bar .model-selector-wrapper) {
      display: none;
    }

    .mobile-new-chat {
      display: flex;
    }

    .chat-scroll-area {
      padding-top: 20px;
    }

    .text,
    .markdown-content {
      font-size: 0.875rem;
      word-break: break-word;
      overflow-wrap: anywhere;
    }

    .markdown-content :global(pre) {
      max-width: 100%;
      overflow-x: auto;
      white-space: pre;
    }
  }

  /* Copy button check state */
  .message-action-btn.copied {
    color: #10b981;
  }

  /* Feedback modal */
  .feedback-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    animation: fadeIn 0.15s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; }
    to   { opacity: 1; }
  }

  .feedback-modal {
    background: var(--bg-primary);
    border: 1px solid var(--border-color);
    border-radius: var(--radius-lg);
    width: 420px;
    max-width: calc(100vw - 2rem);
    box-shadow: var(--shadow-lg);
    animation: scaleIn 0.15s ease;
  }

  @keyframes scaleIn {
    from { transform: scale(0.95); opacity: 0; }
    to   { transform: scale(1);    opacity: 1; }
  }

  .feedback-modal-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 1.1rem 1.25rem 0.75rem;
  }

  .feedback-modal-icon {
    color: var(--text-secondary);
    display: flex;
    align-items: center;
  }

  .feedback-modal-title {
    font-family: var(--font-display);
    font-size: 1rem;
    font-weight: 600;
    color: var(--text-primary);
    flex: 1;
    margin: 0;
  }

  .feedback-modal-close {
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-secondary);
    padding: 0.2rem;
    border-radius: var(--radius-sm);
    display: flex;
    align-items: center;
    transition: color 0.12s;
  }

  .feedback-modal-close:hover { color: var(--text-primary); }

  .feedback-textarea {
    display: block;
    width: 100%;
    box-sizing: border-box;
    margin: 0 0 0 0;
    padding: 0.75rem 1.25rem;
    font-family: var(--font-sans);
    font-size: 0.9rem;
    color: var(--text-primary);
    background: transparent;
    border: none;
    border-top: 1px solid var(--border-color);
    border-bottom: 1px solid var(--border-color);
    resize: vertical;
    outline: none;
    min-height: 90px;
  }

  .feedback-textarea::placeholder { color: var(--text-secondary); }

  .feedback-modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
    padding: 0.75rem 1.25rem;
  }

  .feedback-cancel-btn {
    background: none;
    border: 1px solid var(--border-color);
    border-radius: var(--radius-full);
    padding: 0.45rem 1rem;
    font-size: 0.875rem;
    cursor: pointer;
    color: var(--text-secondary);
    transition: background 0.12s;
  }

  .feedback-cancel-btn:hover { background: rgba(0,0,0,0.04); }

  .feedback-submit-btn {
    background: #0f0f0f;
    color: #fff;
    border: none;
    border-radius: var(--radius-full);
    padding: 0.45rem 1.1rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: opacity 0.12s;
  }

  .feedback-submit-btn:disabled { opacity: 0.6; cursor: not-allowed; }
  .feedback-submit-btn:not(:disabled):hover { opacity: 0.85; }

  .streaming-indicator {
    display: flex;
    align-items: center;
    padding-top: 0.25rem;
    color: var(--text-tertiary, #999);
  }

  .streaming-indicator :global(svg) {
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>
