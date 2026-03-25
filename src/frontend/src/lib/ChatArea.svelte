<script>
  import ModelSelector from "./ModelSelector.svelte";
  import { tick, onMount } from "svelte";
  import { authFetch, authPost, prepareFilesForUpload } from "./utils.js";
  import { renderMarkdown } from "./markdown.js";
  import DynamicPanel from "./DynamicPanel.svelte";
  import { Send, Paperclip, X, Bot, User, Loader2, FileText, Image as ImageIcon, Square, Info, Maximize2, Minimize2, MoreHorizontal, Trash2, Sparkles } from "lucide-svelte";
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
        });
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
    isLoading = true;

    // Scroll to bottom
    await tick();
    scrollToBottom();

    // Create placeholder for assistant response
    const assistantMessage = { role: "assistant", content: "" };
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
        client_context: panelState,
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
    const decoder = new TextDecoder();
    let buffer = "";
    const lastMsg = messages[messages.length - 1];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        if (!line.trim()) continue;
        try {
          const event = JSON.parse(line);
          if (event.type === "text") {
            lastMsg.content += event.content ?? "";
          } else if (event.type === "elements") {
            if (event.elements) {
              if (Array.isArray(event.elements) && event.elements.length === 0) {
                panelElements = [];
              } else {
                const existingMap = new Map(panelElements.map((e) => [e.id, e]));
                for (const el of event.elements) {
                  existingMap.set(el.id, el);
                }
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
  }

  async function triggerAutoInvoke() {
    if (!autoInvokeEnabled || !autoInvokePrompt || messages.length > 0 || isLoading) return;

    const convId = await ensureConversation();
    if (!convId) return;

    isLoading = true;
    const assistantMessage = { role: "assistant", content: "" };
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

    // Auto-invoke: trigger agent's first message on new conversations
    if (autoInvokeEnabled && autoInvokePrompt && !activeConversationId) {
      triggerAutoInvoke();
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
          <div class="agent-avatar-header" style="background: {currentAgentColor}">
            <span>{currentAgentName.charAt(0).toUpperCase()}</span>
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
        <div class="content-centered">
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
        <div class="messages-list">
          {#each messages as msg}
            <div class="message {msg.role}">
              <div class="message-content">
                {#if msg.role === "assistant"}
                  {#if currentAgentIcon}
                    <img src={currentAgentIcon} alt="" class="avatar assistant" />
                  {:else}
                    <div class="avatar assistant">
                      <Bot size={18} />
                    </div>
                  {/if}
                {:else}
                  <div class="avatar user">
                    <User size={18} />
                  </div>
                {/if}
                <div class="message-stack">
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
                  </div>
                  {#if msg.role === "assistant" && msg.content.trim()}
                    <div class="message-actions">
                      <button class="message-action-btn" type="button" title="Copy">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                          <rect x="9" y="9" width="13" height="13" rx="2"></rect>
                          <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
                        </svg>
                      </button>
                      <button class="message-action-btn" type="button" title="Like">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M7 10v12"></path>
                          <path d="M15 5.88 14 10h5.83a2 2 0 0 1 1.92 2.56l-2.33 8A2 2 0 0 1 17.5 22H4a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2.76a2 2 0 0 0 1.79-1.11L12 2a3.13 3.13 0 0 1 3 3.88z"></path>
                        </svg>
                      </button>
                      <button class="message-action-btn" type="button" title="Dislike">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M17 14V2"></path>
                          <path d="M9 18.12 10 14H4.17a2 2 0 0 1-1.92-2.56l2.33-8A2 2 0 0 1 6.5 2H20a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2h-2.76a2 2 0 0 0-1.79 1.11L12 22a3.13 3.13 0 0 1-3-3.88z"></path>
                        </svg>
                      </button>
                      <button class="message-action-btn" type="button" title="Regenerate">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                          <path d="M21.5 2v6h-6"></path>
                          <path d="M2.5 22v-6h6"></path>
                          <path d="M2.5 12a10 10 0 0 1 17.17-6.83L21.5 8"></path>
                          <path d="M21.5 12a10 10 0 0 1-17.17 6.83L2.5 16"></path>
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
      <div class="input-container">
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
            <button
              class="action-btn"
              onclick={triggerFileInput}
              title="Attach files"
              disabled={isLoading}
            >
              <Paperclip size={18} />
            </button>
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
    margin: 0;
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

  .markdown-content :global(a) {
    color: var(--primary-accent);
    text-decoration: none;
  }

  .markdown-content :global(a:hover) {
    text-decoration: underline;
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
</style>
