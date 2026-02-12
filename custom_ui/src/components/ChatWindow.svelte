<script>
  export let title = "Chat";
  export let messages = [];

  let inputValue = "";

  // Normalize messages to ensure they have text and sender properties
  let normalizedMessages = [];
  
  $: {
    normalizedMessages = messages.map(msg => {
      if (typeof msg === "string") {
        return { text: msg, sender: "assistant" };
      }
      return msg;
    });
  }

  function sendMessage() {
    if (!inputValue.trim()) return;
    
    normalizedMessages = [...normalizedMessages, { text: inputValue, sender: "user" }];
    inputValue = "";
  }

  function handleKeydown(e) {
    if (e.key === "Enter") {
      sendMessage();
    }
  }
</script>

<div class="chat-window">
  <div class="chat-header">{title}</div>
  <div class="chat-messages">
    {#each normalizedMessages as msg (msg)}
      <div class="message {msg.sender}">
        <div class="message-text">{msg.text}</div>
      </div>
    {/each}
  </div>
  <div class="chat-input-area">
    <input
      type="text"
      placeholder="Type a message..."
      bind:value={inputValue}
      on:keydown={handleKeydown}
    />
    <button on:click={sendMessage}>Send</button>
  </div>
</div>

<style>
  .chat-window {
    display: flex;
    flex-direction: column;
    height: 100%;
    border: 1px solid #ddd;
    border-radius: 6px;
    background: white;
    overflow: hidden;
  }

  .chat-header {
    padding: 12px;
    background: #f0f0f0;
    border-bottom: 1px solid #ddd;
    font-weight: 600;
    color: #333;
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .message {
    display: flex;
    margin-bottom: 8px;
  }

  .message.user {
    justify-content: flex-end;
  }

  .message.assistant {
    justify-content: flex-start;
  }

  .message-text {
    padding: 8px 12px;
    border-radius: 6px;
    max-width: 70%;
    word-wrap: break-word;
  }

  .message.user .message-text {
    background: #2196F3;
    color: white;
  }

  .message.assistant .message-text {
    background: #f0f0f0;
    color: #333;
  }

  .chat-input-area {
    display: flex;
    gap: 8px;
    padding: 12px;
    border-top: 1px solid #ddd;
    background: #fafafa;
  }

  input {
    flex: 1;
    padding: 8px 12px;
    border: 1px solid #ddd;
    border-radius: 4px;
    font-size: 14px;
  }

  input:focus {
    outline: none;
    border-color: #2196F3;
  }

  button {
    padding: 8px 16px;
    background: #2196F3;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-weight: 500;
    transition: background 0.2s;
  }

  button:hover {
    background: #1976D2;
  }

  button:active {
    background: #1565C0;
  }
</style>
