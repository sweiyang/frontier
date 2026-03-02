<script>
  import ModelSelector from "./ModelSelector.svelte";
  import { tick, onMount } from "svelte";
  import { authFetch, authPost, prepareFilesForUpload } from "./utils.js";
  import { renderMarkdown } from "./markdown.js";
  import Renderer from './custom_ui/Renderer.svelte';
  import { schema } from './custom_ui/stores/schemaStore';
  
  async function handleFetchSchema(lastMessage = null, componentId = null) {
    await schema.fetchSchema(lastMessage, componentId, currentAgentEndpoint);
  }

  let {
    currentUser = null,
    conversationId = null,
    project = null,
    onconversationcreated = () => {},
    onmessagesent = () => {},
    onnewchat = () => {},
  } = $props();

  let messages = $state([]);
  let inputValue = $state("");
  let isLoading = $state(false);
  let chatContainer;
  let currentModel = $state("default");
  let currentAgentId = $state(null);
  let currentAgentEndpoint = $state(null);
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
    // Schema will be fetched when an agent is selected
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

  async function sendMessage() {
    if ((!inputValue.trim() && attachedFiles.length === 0) || isLoading) return;

    const convId = await ensureConversation();
    if (!convId) {
      console.error("No conversation available");
      return;
    }

    // Build user message with file info
    let messageContent = inputValue;
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

    const currentInput = inputValue;
    inputValue = "";
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
        message: currentInput,
        conversation_id: convId,
        agent_id: currentAgentId, // Optional
        model: currentModel, // Deprecated, kept for backward compatibility
        files: preparedFiles,
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

  function extractAgentEndpoint(agent) {
    // Extract endpoint from the selected agent
    return agent?.endpoint || null;
  }

  function handleAgentSelect(event) {
    // ModelSelector sends { agent, model, agent_id }
    currentModel = event?.detail?.model || "default";
    currentAgentId = event?.detail?.agent_id || null;
    currentAgentEndpoint = extractAgentEndpoint(event?.detail?.agent);
    
    // Fetch schema from the selected agent's endpoint
    handleFetchSchema();
  }
</script>

<main class="chat-area">

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
  <div class="container">
    <div class="renderer-wrapper">
      {#if $schema}
        <Renderer schema={$schema} onButtonClick={handleFetchSchema} />
      {:else}
        <div class="empty-state">
          <p>Loading UI schema from API...</p>
        </div>
      {/if}
    </div>
  </div>

</main>

<style>
  .chat-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    background-color: var(--bg-primary);
    overflow: hidden;
  }

  .top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    background-color: var(--bg-primary);
    border-bottom: 1px solid var(--border-color);
  }

  .mobile-new-chat {
    display: none;
    width: 36px;
    height: 36px;
    border-radius: var(--radius-full);
    background-color: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: var(--shadow-sm);
  }

  .container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .renderer-wrapper {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: auto;
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    color: var(--text-secondary);
  }

  @media (max-width: 768px) {
    .mobile-new-chat {
      display: flex;
    }
  }
</style>
