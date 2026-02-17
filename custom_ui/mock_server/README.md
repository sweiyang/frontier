# Mock API Server

A Python FastAPI server that serves mock schema data and handles component state updates.

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

Start the server with:
```bash
python main.py
```

The server will run on `http://localhost:3001`

Or use uvicorn directly:
```bash
uvicorn main:app --reload --port 3001
```

## Endpoints

### GET `/api/schema`
Returns the schema from `sample-schema.json`

**Response:**
```json
{
  "components": [...]
}
```

### POST `/api/schema`
Accepts current component state and returns the schema with updated ChatWindow messages.

**Request Body:**
```json
{
  "components": [
    {
      "id": "chat1",
      "type": "ChatWindow",
      "props": {
        "query": "user message",
        "messages": [...]
      }
    }
  ]
}
```

**Response:**
Returns the schema with updated chat messages.

### GET `/health`
Health check endpoint

**Response:**
```json
{
  "status": "ok"
}
```

## How It Works

1. The server loads the schema from `sample-schema.json` (one directory level up from mock_server)
2. When a POST request is received with a ChatWindow component containing a query:
   - It finds the matching ChatWindow in the schema
   - Preserves existing messages from the request
   - Appends the new user message
   - Adds a mock assistant response
   - Returns the updated schema
3. When a GET request is received, it returns a fresh copy of the schema

## CORS

The server is configured to accept requests from any origin with allowed methods: GET, POST, OPTIONS
