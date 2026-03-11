# OpenAI Connector Example — Ollama

Use Frontier’s **OpenAI connector** with [Ollama](https://ollama.com) for local chat. This guide shows how to add Ollama as an agent **through the Frontier frontend**.

---

## Step 1: Run Ollama

1. Install Ollama from [ollama.com/download](https://ollama.com/download) and start it (e.g. open the Ollama app or run `ollama serve`).
2. Pull a model so it appears in the API:
   ```bash
   ollama pull llama3.2
   ```
   You can use any model you like (e.g. `mistral`, `codellama`). Ollama serves at **http://localhost:11434** by default.

---

## Step 2: Open project settings in Frontier

1. Log in to Frontier and open the project where you want to add the agent.
2. Go to **Settings** (gear or project settings).
3. Open the **Agents** tab.
4. Click **Add Agent**. The “Add Agent” form opens.

---

## Step 3: Configure the agent in the form

Fill the form as follows, in order:

1. **Connection Type**  
   Select **OPENAI** from the dropdown.

2. **Endpoint URL**  
   Enter:
   ```text
   http://localhost:11434
   ```
   (Use another host/port only if you run Ollama elsewhere.)

3. **Icon (optional)**  
   Leave empty or upload an image if you want.

4. **Authentication**  
   Leave as **None** for local Ollama. Use API Key/Bearer only if your Ollama instance requires it.

5. **Fetch Models**  
   Click the **Fetch Models** button. The frontend will call Ollama’s `/v1/models` and fill the model list. Wait until it finishes (button shows “Fetching...” then “Fetch Models” again).

6. **Select Model**  
   In the **Select Model** dropdown, choose the model you pulled (e.g. **llama3.2**). This is required.

7. **Name (optional)**  
   Give the agent a display name, e.g. `Ollama (llama3.2)`. If you leave it blank, the UI uses the model name.

8. **System Prompt (optional)**  
   Optionally set a system message, e.g. `You are a helpful assistant.`

---

## Step 4: Save the agent

Click **Add Agent** (or **Save** if you are editing). The new agent appears in the Agents table. You can set it as the default for the project if you want.

---

## Step 5: Use the agent in chat

Open the chat view for that project. In the model/agent selector at the top, choose the Ollama agent (e.g. “Ollama (llama3.2)”). New messages will be sent to Ollama via the OpenAI connector.

---

## Summary of values (quick reference)

| Field in UI        | Value for Ollama              |
|--------------------|-------------------------------|
| Connection Type    | **OPENAI**                    |
| Endpoint URL       | `http://localhost:11434`      |
| Authentication     | **None** (for local Ollama)   |
| After “Fetch Models” | **Select Model** e.g. `llama3.2` |
| Name (optional)    | e.g. `Ollama (llama3.2)`      |
| System Prompt (optional) | e.g. `You are a helpful assistant.` |

---

## Troubleshooting

- **“Fetch Models” fails or no models in dropdown**  
  Check that Ollama is running (`ollama list` or open the Ollama app). Ensure the endpoint is exactly `http://localhost:11434` (or your Ollama URL). Frontier’s backend calls Ollama; if Frontier runs in Docker or another host, use the host that can reach Ollama (e.g. `http://host.docker.internal:11434` on Docker Desktop).

- **Model not found / errors in chat**  
  Pull the model: `ollama pull <model>`. The name in “Select Model” must match the model name in Ollama.

- **Connection refused**  
  Start Ollama (`ollama serve` or the Ollama app) and confirm nothing else is using port 11434.

---

## Optional: Add agent via API

To create the same agent via the API (e.g. for automation), you can use the included `agent_config.json` and `register_agent.py`. See the script’s `--help` or the comments inside it for usage.
