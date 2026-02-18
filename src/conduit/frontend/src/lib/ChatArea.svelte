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
    onconversationcreated = () => {},
    onmessagesent = () => {},
    onnewchat = () => {},
  } = $props();

  let panelElements = $state([]);
  let frontendEnabled = $state(false);
  let panelState = $state({});

  let messages = $state([]);
  let inputValue = $state("");
  let isLoading = $state(false);
  let chatContainer;
  let currentModel = $state("default");
  let currentAgentId = $state(null);
  let activeConversationId = $state(null);
  let attachedFiles = $state([]);
  let fileInputRef;
  let isDragging = $state(false);
  let dragCounter = 0;

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
      const lastMsg = messages[messages.length - 1];
      const elementsMatch = lastMsg.content.match(
        /\[ELEMENTS\]([\s\S]*?)\[\/ELEMENTS\]/,
      );
      console.log("debug element rendering: ", lastMsg, elementsMatch);
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
                existingMap.set(el.id, el);
              }

              panelElements = Array.from(existingMap.values());
            }
          }
          // Remove the block from the message
          lastMsg.content = lastMsg.content
            .replace(elementsMatch[0], "")
            .trim();
          messages = messages; // Trigger reactivity
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

    // Check for frontend capability
    const agent = event?.detail?.agent;
    frontendEnabled = agent?.extras?.frontend === true;
    console.log("frontend enabled: ", frontendEnabled);
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

  <div class="chat-area">
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
            <div class="logo-large">O</div>
            <h1>
              Hello{#if currentUser}, {currentUser}{/if}
            </h1>
            {#if project}
              <p class="project-context">
                Working in <strong>{project}</strong>
              </p>
            {/if}
          </div>

          <div class="suggestions">
            <div class="suggestion-row">
              <button
                class="suggestion-item"
                on:click={() => {
                  inputValue =
                    "Show me a code snippet of a website's sticky header";
                  sendMessage();
                }}
              >
                <div class="s-title">Show me a code snippet</div>
                <div class="s-desc">of a website's sticky header</div>
              </button>
              <button
                class="suggestion-item"
                on:click={() => {
                  inputValue =
                    "Help me study vocabulary for a college entrance exam";
                  sendMessage();
                }}
              >
                <div class="s-title">Help me study</div>
                <div class="s-desc">vocabulary for a college entrance exam</div>
              </button>
              <button
                class="suggestion-item"
                on:click={() => {
                  inputValue = "Overcome procrastination give me tips";
                  sendMessage();
                }}
              >
                <div class="s-title">Overcome procrastination</div>
                <div class="s-desc">give me tips</div>
              </button>
            </div>
          </div>
        </div>
      {:else}
        <div class="messages-list">
          {#each messages as msg}
            <div class="message {msg.role}">
              <div class="message-content">
                {#if msg.role === "assistant"}
                  <div class="avatar assistant">O</div>
                {:else}
                  <div class="avatar user">U</div>
                {/if}
                <div class="text-container">
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
              placeholder="How can I help you today?"
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
              <span>📎</span>
            </button>
            <div class="spacer"></div>
            <button
              class="send-btn"
              on:click={() => sendMessage()}
              disabled={isLoading}
            >
              {#if isLoading}
                <span>◻</span>
              {:else}
                <span>↑</span>
              {/if}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>

  {#if frontendEnabled && panelElements.length > 0}
    <div class="panel-container">
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
    padding-top: 60px; /* Space for top bar */
    padding-bottom: 20px;
    display: flex;
    flex-direction: column;
  }

  .content-centered {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
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
    gap: 1.5rem;
    padding: 1rem;
    width: 100%;
    max-width: 800px;
    margin: 0 auto;
  }

  .message {
    display: flex;
    width: 100%;
  }

  .message-content {
    display: flex;
    gap: 1rem;
    max-width: 100%;
    align-items: flex-start;
  }

  .avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    font-size: 0.9rem;
    flex-shrink: 0;
  }

  .avatar.assistant {
    background-color: black;
    color: white;
  }

  .avatar.user {
    background-color: #ddd;
    color: #333;
  }

  .text {
    line-height: 1.6;
    color: var(--text-primary);
    white-space: pre-wrap; /* Preserve newlines */
    margin-top: 0.25rem;
  }

  /* Input Area */
  .input-container-wrapper {
    display: flex;
    justify-content: center;
    padding: 1rem 1rem 2rem 1rem;
    background: linear-gradient(to top, var(--bg-primary) 80%, transparent);
  }

  .input-container {
    width: 100%;
    max-width: 700px;
  }

  .input-card {
    background: var(--bg-secondary);
    border-radius: 32px;
    padding: var(--spacing-lg);
    box-shadow: var(--shadow-sm);
    border: 1px solid transparent;
    transition: all 0.2s;
  }

  .input-card:hover,
  .input-card:focus-within {
    box-shadow: var(--shadow-md);
    border-color: var(--border-color);
  }

  .input-header {
    margin-bottom: var(--spacing-lg);
  }

  textarea {
    width: 100%;
    background: transparent;
    border: none;
    outline: none;
    resize: none;
    color: var(--text-primary);
    font-size: 1.1rem;
    font-family: inherit;
    min-height: 24px;
    max-height: 200px;
  }

  textarea::placeholder {
    color: var(--text-secondary);
  }

  .input-actions {
    display: flex;
    gap: var(--spacing-sm);
    align-items: center;
    justify-content: flex-end;
  }

  .action-btn {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--text-secondary);
    transition: background 0.2s;
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 1.2rem;
  }

  .action-btn:hover {
    background: rgba(0, 0, 0, 0.05);
    color: var(--text-primary);
  }

  .spacer {
    flex: 1;
  }

  .send-btn {
    width: 40px;
    height: 40px;
    border-radius: 50%;
    background-color: black;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    cursor: pointer;
    transition: opacity 0.2s;
  }

  .send-btn:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  /* Suggestions */
  .suggestions {
    width: 100%;
    max-width: 700px;
  }

  .suggestion-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
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
    width: 100%;
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
  .text-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

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
    line-height: 1.6;
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
      grid-template-columns: 1fr;
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
