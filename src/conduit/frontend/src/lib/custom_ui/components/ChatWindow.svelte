<script>
  export let title = "Chat";
  export let messages = [];
  export let onClick;

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
    
    const userMessage = inputValue.trim();
    normalizedMessages = [...normalizedMessages, { text: userMessage, sender: "user" }];
    
    inputValue = "";
    
    // Trigger schema fetch with the message
    if (onClick) {
      onClick(userMessage);
    }
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
    width: 100%;
    border: none;
    border-radius: 12px;
    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    overflow: hidden;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
  }

  .chat-header {
    padding: 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-bottom: none;
    font-weight: 700;
    color: white;
    font-size: 15px;
  }

  .chat-messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
    background: #fafbfc;
  }

  .message {
    display: flex;
    margin-bottom: 4px;
  }

  .message.user {
    justify-content: flex-end;
  }

  .message.assistant {
    justify-content: flex-start;
  }

  .message-text {
    padding: 10px 14px;
    border-radius: 12px;
    max-width: 70%;
    word-wrap: break-word;
    line-height: 1.4;
    font-size: 14px;
  }

  .message.user .message-text {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 12px 4px 12px 12px;
  }

  .message.assistant .message-text {
    background: #e8eef5;
    color: #1a1a2e;
    border-radius: 4px 12px 12px 12px;
  }

  .chat-input-area {
    display: flex;
    gap: 8px;
    padding: 12px;
    border-top: 1px solid #e0e6ed;
    background: white;
  }

  input {
    flex: 1;
    padding: 10px 14px;
    border: 1px solid #e0e6ed;
    border-radius: 8px;
    font-size: 14px;
    transition: all 0.3s ease;
  }

  input:focus {
    outline: none;
    border-color: #c9cdd4;
    box-shadow: 0 0 0 3px rgba(201, 205, 212, 0.1);
  }

  .chat-input-area button {
    padding: 10px 16px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border: none;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 4px 12px rgba(201, 205, 212, 0.3);
  }

  .chat-input-area button:hover {
    box-shadow: 0 6px 16px rgba(201, 205, 212, 0.4);
    transform: translateY(-2px);
  }

  .chat-input-area button:active {
    transform: translateY(0);
  }
</style>
