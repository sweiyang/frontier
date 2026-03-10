<script>
  import ModelSelector from "./ModelSelector.svelte";
  import { tick, onMount } from "svelte";
  import { authFetch, authPost, prepareFilesForUpload } from "./utils.js";
  import { renderMarkdown } from "./markdown.js";
  import DynamicPanel from "./DynamicPanel.svelte";

  let {
    currentUser = null,
    conversationId = null,
    project = null,
    footnote = "",
    onconversationcreated = () => {},
    onmessagesent = () => {},
    onnewchat = () => {},
    onlayoutchange = () => {},
  } = $props();

  let panelElements = $state([]);
  let frontendEnabled = $state(false);
  let panelState = $state({});
  let chatFlex = $state(1);
  let panelFlex = $state(1);
  let agentWantsCollapse = $state(false);
  let hasNotifiedCollapse = false;

  let messages = $state([]);
  let inputValue = $state("");
  let isLoading = $state(false);
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
        alert(`File "${file.name}" is too large. Max size is 10MB.`);
        continue;
      }
      if (
        !ALLOWED_TYPES.includes(file.type) &&
        !file.type.startsWith("text/")
      ) {
        alert(`File type "${file.type || "unknown"}" is not supported.`);
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
      const response = await authPost("/conversations", {});
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

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // Update the last message (assistant's)
        messages[messages.length - 1].content += chunk;
        messages = messages; // Trigger reactivity
        scrollToBottom();
      }

      // Parse Dynamic UI Elements
      // console.log("messages (full):", JSON.stringify(messages, null, 2));
      const lastMsg = messages[messages.length - 1];
      const elementsMatch = lastMsg.content.match(
        /\[ELEMENTS\]([\s\S]*?)\[\/ELEMENTS\]/,
      );
      // console.log("debug element rendering: ", lastMsg, elementsMatch);
      if (elementsMatch) {
        try {
          const jsonStr = elementsMatch[1];
          const data = JSON.parse(jsonStr);
          console.log("elements json: ", jsonStr);

          if (data.elements) {
            if (Array.isArray(data.elements) && data.elements.length === 0) {
              // Explicit clear
              panelElements = [];
            } else {
              // specific logic: Upsert by ID (Append new, Update existing)
              // using a Map to preserve order of existing elements
              const newElements = data.elements;
              const existingMap = new Map(panelElements.map((e) => [e.id, e]));

              for (const el of newElements) {
                const prev = existingMap.get(el.id);
                if (prev && prev.type !== el.type) {
                  delete panelState[el.id];
                }
                existingMap.set(el.id, el);
              }

              panelElements = Array.from(existingMap.values());
            }
          }

          if (Array.isArray(data.remove)) {
            const removeSet = new Set(data.remove);
            panelElements = panelElements.filter((e) => !removeSet.has(e.id));
            for (const id of data.remove) {
              delete panelState[id];
            }
          }
          // Remove the block from the message
          lastMsg.content = lastMsg.content
            .replace(elementsMatch[0], "")
            .trim();
          messages = messages; // Trigger reactivity

          // Collapse sidebar when dynamic panel first appears
          if (agentWantsCollapse && panelElements.length > 0 && !hasNotifiedCollapse) {
            hasNotifiedCollapse = true;
            onlayoutchange({ detail: { collapseSidebar: true } });
          }
        } catch (e) {
          console.error("Failed to parse elements JSON", e);
        }
      }

      // Parse File downloads
      const fileMatch = lastMsg.content.match(/\[FILE\]([\s\S]*?)\[\/FILE\]/);
      if (fileMatch) {
        try {
          const fileJson = JSON.parse(fileMatch[1]);
          if (fileJson.name && fileJson.content) {
            // Decode base64 to blob
            const byteChars = atob(fileJson.content);
            const byteNums = new Array(byteChars.length);
            for (let i = 0; i < byteChars.length; i++) {
              byteNums[i] = byteChars.charCodeAt(i);
            }
            const byteArray = new Uint8Array(byteNums);
            const blob = new Blob([byteArray], {
              type: fileJson.type || "application/octet-stream",
            });
            const url = URL.createObjectURL(blob);

            if (!lastMsg.files) lastMsg.files = [];
            lastMsg.files.push({
              name: fileJson.name,
              type: fileJson.type || "application/octet-stream",
              size: blob.size,
              url: url,
            });
          }
          // Remove the [FILE] block from the message
          lastMsg.content = lastMsg.content.replace(fileMatch[0], "").trim();
          messages = messages;
        } catch (e) {
          console.error("Failed to parse file JSON", e);
        }
      }
    } catch (error) {
      console.error("Error:", error);
      messages[messages.length - 1].content =
        "Error: Could not reach the server.";
    } finally {
      isLoading = false;
      // Notify parent that a message was sent (for sidebar refresh)
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
    frontendEnabled = agent?.extras?.frontend === true;
    console.log("frontend enabled: ", frontendEnabled);

    // Read sample questions from agent extras
    sampleQuestions = agent?.extras?.sample_questions || [];

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

    // Reset sidebar to expanded when switching agents
    onlayoutchange({ detail: { collapseSidebar: false } });
  }

  function handlePanelSendMessage(event) {
    sendMessage(event.detail);
  }
</script>

<main
  class="chat-layout"
  on:dragenter={handleDragEnter}
  on:dragleave={handleDragLeave}
  on:dragover={handleDragOver}
  on:drop={handleDrop}
>
  {#if isDragging}
    <div class="drop-overlay">
      <div class="drop-content">
        <div class="drop-icon">📎</div>
        <div class="drop-text">Drop files here</div>
        <div class="drop-hint">Images, PDFs, text files, and more</div>
      </div>
    </div>
  {/if}

  <div class="chat-area" style="flex: {chatFlex};">
    <div class="top-bar">
      <ModelSelector {project} onselect={handleAgentSelect} />
      <button class="mobile-new-chat" on:click={onnewchat} title="New Chat">
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"
          ></path>
          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"
          ></path>
        </svg>
      </button>
    </div>

    <div class="chat-scroll-area" bind:this={chatContainer}>
      {#if messages.length === 0}
        <div class="content-centered">
          <div class="greeting">
            <h1>
              Hello{#if currentUser}, {currentUser}{/if}
            </h1>
            {#if project}
              <p class="project-context">
                Working in <strong>{project}</strong>
              </p>
            {/if}
          </div>

          {#if sampleQuestions.length > 0}
            <div class="suggestions">
              <div class="suggestion-row">
                {#each sampleQuestions as q}
                  <button
                    class="suggestion-item"
                    on:click={() => {
                      inputValue = (q.description || q.title).trim();
                      sendMessage();
                    }}
                  >
                    <div class="s-title">{q.title}</div>
                    {#if q.description}
                      <div class="s-desc">{q.description}</div>
                    {/if}
                  </button>
                {/each}
              </div>
            </div>
          {/if}
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
                    <div class="avatar assistant"></div>
                  {/if}
                {:else}
                  <div class="avatar user">U</div>
                {/if}
                <div class="message-stack">
                  <div class="bubble">
                  {#if msg.files && msg.files.length > 0}
                    <div class="message-files">
                      {#each msg.files as file}
                        <div class="message-file">
                          <span class="file-icon">{getFileIcon(file.type)}</span
                          >
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
                  {#if msg.role === "assistant" && !msg.content
                      .replace(/\[(?:FILE|ELEMENTS)\][\s\S]*$/g, "")
                      .trim() && isLoading}
                    <div class="loading-dots">
                      <span></span><span></span><span></span>
                    </div>
                  {:else}
                    <div class="text markdown-content">
                      {@html renderMarkdown(
                        msg.content.replace(
                          /\[(?:FILE|ELEMENTS)\][\s\S]*$/g,
                          "",
                        ),
                      )}
                    </div>
                  {/if}
                  </div>
                  {#if msg.role === "assistant" && msg.content
                      .replace(/\[(?:FILE|ELEMENTS)\][\s\S]*$/g, "")
                      .trim()}
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
        </div>
      {/if}
    </div>

    <div class="input-container-wrapper">
      <div class="input-container">
        <div class="input-card">
          {#if attachedFiles.length > 0}
            <div class="attached-files">
              {#each attachedFiles as file, index}
                <div class="attached-file">
                  <span class="file-icon">{getFileIcon(file.type)}</span>
                  <span class="file-name">{file.name}</span>
                  <span class="file-size">{formatFileSize(file.size)}</span>
                  <button
                    class="remove-file"
                    on:click={() => removeFile(index)}
                    title="Remove file">×</button
                  >
                </div>
              {/each}
            </div>
          {/if}
          <div class="input-header">
            <textarea
              bind:value={inputValue}
              on:keydown={handleKeydown}
              placeholder="Reply..."
              rows="1"
            ></textarea>
          </div>
          <div class="input-actions">
            <input
              type="file"
              bind:this={fileInputRef}
              on:change={handleFileSelect}
              multiple
              accept=".jpg,.jpeg,.png,.gif,.webp,.pdf,.txt,.csv,.md,.json,.doc,.docx"
              style="display: none;"
            />
            <button
              class="action-btn"
              on:click={triggerFileInput}
              title="Attach files"
              disabled={isLoading}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="12" y1="5" x2="12" y2="19"></line>
                <line x1="5" y1="12" x2="19" y2="12"></line>
              </svg>
            </button>
            <div class="spacer"></div>
            <button
              class="send-btn"
              on:click={() => sendMessage()}
              disabled={isLoading}
            >
              {#if isLoading}
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <rect x="4" y="4" width="16" height="16" rx="2"></rect>
                </svg>
              {:else}
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="12" y1="19" x2="12" y2="5"></line>
                  <polyline points="5 12 12 5 19 12"></polyline>
                </svg>
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
        on:sendMessage={handlePanelSendMessage}
      />
    </div>
  {/if}
</main>

<style>
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

  .top-bar {
    padding: var(--spacing-md);
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 10;
    background: transparent; /* Or blur/solid if needed */
    display: flex;
    justify-content: space-between; /* Space out selector and new chat button */
    pointer-events: none; /* Let clicks pass through mainly */
  }

  /* Enable pointer events for children */
  .top-bar > * {
    pointer-events: auto;
  }

  .mobile-new-chat {
    display: none; /* Hidden by default */
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: var(--shadow-sm);
  }

  .chat-scroll-area {
    flex: 1;
    overflow-y: auto;
    padding-top: 60px;
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

  .logo-large {
    font-size: 2rem;
    font-weight: bold;
    margin-bottom: var(--spacing-sm);
  }

  h1 {
    font-weight: 500;
    font-size: 2rem;
    color: var(--text-primary);
  }

  .project-context {
    margin-top: var(--spacing-sm);
    color: var(--text-secondary);
    font-size: 1rem;
  }

  .project-context strong {
    color: var(--primary-accent, #6366f1);
  }

  /* Messages */
  .messages-list {
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
    padding: 1rem;
    width: 100%;
    max-width: 800px;
    margin: 0 auto;
  }

  .message.user + .message.assistant,
  .message.assistant + .message.user {
    margin-top: 0.6rem;
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
    gap: 0.45rem;
    max-width: 80%;
    align-items: center;
  }

  .message.user .message-content {
    flex-direction: row-reverse;
  }

  .avatar {
    width: 30px;
    height: 30px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 0.8rem;
    flex-shrink: 0;
  }

  .avatar.assistant {
    background-color: black;
    color: white;
    object-fit: cover;
  }

  .avatar.user {
    background-color: #ddd;
    color: #333;
  }

  .message-stack {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 0.18rem;
  }

  .message.user .message-stack {
    align-items: flex-end;
  }

  .bubble {
    padding: 0.3rem 0.72rem 0.2rem;
    border-radius: 1rem;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
  }

  .message.assistant .bubble {
    background-color: var(--bg-secondary, #f5f5f5);
    border-top-left-radius: 0.25rem;
  }

  .message.user .bubble {
    background-color: var(--user-bubble-bg, #e8e8e8);
    border-top-right-radius: 0.25rem;
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
    color: var(--text-secondary, #999);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: background-color 0.12s ease, color 0.12s ease;
  }

  .message-action-btn:hover {
    background: rgba(0, 0, 0, 0.06);
    color: var(--text-primary, #333);
  }

  .message-action-btn:active {
    transform: scale(0.92);
  }

  .text {
    line-height: 1.4;
    color: var(--text-primary);
    white-space: normal;
  }

  /* Input Area */
  .input-container-wrapper {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 0.75rem 1rem 1.25rem 1rem;
    background: var(--bg-primary);
  }

  .footnote-text {
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-align: center;
    margin-top: 0.4rem;
    opacity: 0.7;
  }

  .input-container {
    width: 100%;
    max-width: 700px;
  }

  .input-card {
    background: var(--bg-primary, #fff);
    border-radius: 1.5rem;
    padding: 0.75rem 1rem;
    border: 1px solid var(--border-color, #e0e0e0);
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .input-card:focus-within {
    border-color: var(--border-focus, #c0c0c0);
    box-shadow: 0 0 0 1px var(--border-focus, #c0c0c0);
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
    color: var(--text-secondary, #aaa);
  }

  .input-actions {
    display: flex;
    gap: 0.25rem;
    align-items: center;
  }

  .action-btn {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary, #999);
    transition: background 0.15s, color 0.15s;
    background: transparent;
    border: none;
    cursor: pointer;
  }

  .action-btn:hover {
    background: rgba(0, 0, 0, 0.05);
    color: var(--text-primary);
  }

  .spacer {
    flex: 1;
  }

  .send-btn {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    background-color: transparent;
    color: var(--text-secondary, #999);
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    cursor: pointer;
    transition: background 0.15s, color 0.15s;
  }

  .send-btn:hover {
    background: rgba(0, 0, 0, 0.05);
    color: var(--text-primary);
  }

  .send-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  /* Suggestions */
  .suggestions {
    width: 100%;
    max-width: 700px;
  }

  .suggestion-row {
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    gap: var(--spacing-md);
  }

  .suggestion-item {
    padding: var(--spacing-md);
    border-radius: var(--radius-lg);
    cursor: pointer;
    transition: background 0.2s;
    background: transparent;
    border: 1px solid transparent;
    text-align: left;
    height: 100%;
    max-width: 220px;
    flex: 0 1 220px;
    display: flex;
    flex-direction: column;
    justify-content: flex-start;
  }

  .suggestion-item:hover {
    background-color: var(--bg-secondary);
    border-color: var(--border-color, #eee);
  }

  .s-title {
    font-weight: 500;
    color: var(--text-primary);
    margin-bottom: 2px;
  }

  .s-desc {
    font-size: 0.85rem;
    color: var(--text-secondary);
  }

  /* Attached Files Preview */
  .attached-files {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: var(--spacing-md);
    padding-bottom: var(--spacing-md);
    border-bottom: 1px solid var(--border-color, #eee);
  }

  .attached-file {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: var(--bg-tertiary, #f5f5f5);
    border-radius: var(--radius-md, 8px);
    font-size: 0.85rem;
  }

  .attached-file .file-icon {
    font-size: 1rem;
  }

  .attached-file .file-name {
    color: var(--text-primary);
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .attached-file .file-size {
    color: var(--text-secondary);
    font-size: 0.75rem;
  }

  .attached-file .remove-file {
    background: none;
    border: none;
    color: var(--text-secondary);
    cursor: pointer;
    font-size: 1.1rem;
    padding: 0;
    margin-left: 0.25rem;
    line-height: 1;
    transition: color 0.2s;
  }

  .attached-file .remove-file:hover {
    color: #e74c3c;
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
    background: var(--bg-tertiary, #f0f0f0);
    border-radius: var(--radius-sm, 6px);
    font-size: 0.8rem;
  }

  .message-file .file-icon {
    font-size: 0.9rem;
  }

  .message-file .file-name {
    color: var(--text-primary);
    max-width: 200px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .message-file .download-link {
    text-decoration: none;
    color: var(--primary-accent, #2563eb);
    font-weight: 500;
  }

  .message-file .download-link:hover {
    text-decoration: underline;
  }

  /* Loading dots */
  .loading-dots {
    display: flex;
    gap: 4px;
    padding: 8px 0;
    align-items: center;
  }

  .loading-dots span {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--text-secondary, #999);
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
    background: rgba(99, 102, 241, 0.95);
    z-index: 100;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: var(--radius-lg, 12px);
    border: 3px dashed rgba(255, 255, 255, 0.5);
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
  }

  .drop-icon {
    font-size: 3rem;
    margin-bottom: 1rem;
    animation: dropBounce 0.5s ease-in-out infinite alternate;
  }

  @keyframes dropBounce {
    from {
      transform: translateY(0);
    }
    to {
      transform: translateY(-8px);
    }
  }

  .drop-text {
    font-size: 1.5rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
  }

  .drop-hint {
    font-size: 0.9rem;
    opacity: 0.8;
  }

  /* Markdown Content Styles */
  .markdown-content {
    line-height: 1.4;
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
    border-bottom: 1px solid var(--border-color, #eee);
    padding-bottom: 0.3em;
  }

  .markdown-content :global(h2) {
    font-size: 1.5em;
    border-bottom: 1px solid var(--border-color, #eee);
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
    border-left: 4px solid var(--border-color, #ddd);
    background: var(--bg-secondary, #f5f5f5);
    color: var(--text-secondary);
  }

  .markdown-content :global(code) {
    background: var(--bg-tertiary, #f0f0f0);
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 0.9em;
    font-family: "Courier New", monospace;
    color: var(--text-primary);
  }

  .markdown-content :global(pre) {
    background: var(--bg-tertiary, #1e1e1e);
    padding: 1em;
    border-radius: 6px;
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
    background: var(--bg-tertiary, #1e1e1e);
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
    background: var(--bg-secondary, #f5f5f5);
  }

  .markdown-content :global(th),
  .markdown-content :global(td) {
    border: 1px solid var(--border-color, #ddd);
    padding: 0.5em 0.75em;
    text-align: left;
  }

  .markdown-content :global(th) {
    font-weight: 600;
    background: var(--bg-secondary, #f5f5f5);
  }

  .markdown-content :global(tr:nth-child(even)) {
    background: var(--bg-secondary, #fafafa);
  }

  .markdown-content :global(a) {
    color: var(--primary-accent, #6366f1);
    text-decoration: none;
  }

  .markdown-content :global(a:hover) {
    text-decoration: underline;
  }

  .markdown-content :global(img) {
    max-width: 100%;
    height: auto;
    border-radius: 4px;
    margin: 0.5em 0;
  }

  .markdown-content :global(hr) {
    border: none;
    border-top: 1px solid var(--border-color, #ddd);
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
      justify-content: flex-end; /* Align button to right */
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

    .suggestion-row {
      flex-direction: column;
      align-items: center;
    }

    .text,
    .markdown-content {
      font-size: 0.95rem;
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
