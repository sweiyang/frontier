<script>
  import ModelSelector from "./ModelSelector.svelte";
  import { tick, onMount } from "svelte";
  import { authFetch, authPost } from "./auth.js";

  let { 
    currentUser = null, 
    conversationId = null, 
    project = null,
    onconversationcreated = () => {},
    onmessagesent = () => {},
  } = $props();

  let messages = $state([]);
  let inputValue = $state("");
  let isLoading = $state(false);
  let chatContainer;
  let currentModel = $state("default");
  let activeConversationId = $state(null);

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
        onconversationcreated({ detail: { conversationId: data.id, conversation: data } });
        return data.id;
      }
    } catch (error) {
      console.error("Failed to create conversation:", error);
    }
    return null;
  }

  async function sendMessage() {
    if (!inputValue.trim() || isLoading) return;

    const convId = await ensureConversation();
    if (!convId) {
      console.error("No conversation available");
      return;
    }

    const userMessage = { role: "user", content: inputValue };
    messages = [...messages, userMessage];
    const currentInput = inputValue;
    inputValue = "";
    isLoading = true;

    // Scroll to bottom
    await tick();
    scrollToBottom();

    // Create placeholder for assistant response
    const assistantMessage = { role: "assistant", content: "" };
    messages = [...messages, assistantMessage];

    try {
      const response = await authPost("/chat", {
        message: currentInput,
        conversation_id: convId,
        model: currentModel,
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

  function handleAgentSelect(event) {
    // ModelSelector sends { agent, model }, where model is the agent name
    currentModel = event?.detail?.model || "default";
  }
</script>

<main class="chat-area">
  <div class="top-bar">
    <ModelSelector project={project} onselect={handleAgentSelect} />
  </div>

  <div class="chat-scroll-area" bind:this={chatContainer}>
    {#if messages.length === 0}
      <div class="content-centered">
        <div class="greeting">
          <div class="logo-large">O</div>
          <h1>Hello{#if currentUser}, {currentUser}{/if}</h1>
          {#if project}
            <p class="project-context">Working in <strong>{project}</strong></p>
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
              <div class="text">
                {msg.content}
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
        <div class="input-header">
          <textarea
            bind:value={inputValue}
            on:keydown={handleKeydown}
            placeholder="How can I help you today?"
            rows="1"
          ></textarea>
        </div>
        <div class="input-actions">
          <button class="send-btn" on:click={sendMessage} disabled={isLoading}>
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
</main>

<style>
  .chat-area {
    flex: 1;
    display: flex;
    flex-direction: column;
    position: relative;
    background-color: var(--bg-primary);
    overflow: hidden; /* Prevent double scrollbars */
  }

  .top-bar {
    padding: var(--spacing-md);
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    z-index: 10;
    background: transparent; /* Or blur/solid if needed */
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
</style>
