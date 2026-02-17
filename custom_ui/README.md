# Internal POC UI Renderer

A minimal, client-side Svelte-based UI renderer that allows you to upload a JSON definition and render it dynamically.

## Features

✅ Load JSON schema from API  
✅ Validate + render dynamic UI  
✅ Render UI from JSON using a component registry  
✅ Display rendered UI inside an iframe  
✅ Includes mock API server for development  
✅ Safe (no user JS execution)  

## Quick Start

### Option 1: Run with Mock API (Recommended)

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start both the mock API and dev server:**
   ```bash
   npm run dev:full
   ```
   This will run:
   - Mock API server on `http://localhost:3001`
   - Vite dev server on `http://localhost:5173`

3. **Open your browser:**
   Navigate to `http://localhost:5173`
   The app will automatically fetch the schema from the mock API server.

### Option 2: Run Only Dev Server

If you need to run just the Vite dev server:

```bash
npm install
npm run dev
```

Then open `http://localhost:5173`

### Option 3: Run Only Mock API Server

To run just the mock API server:

```bash
npm install
npm run mock-api
```

The API will be available at `http://localhost:3001/api/schema`

## Project Structure

```
src/
 ├─ main.js                 ← Vite entry point
 ├─ App.svelte              ← Upload + iframe host
 ├─ Renderer.svelte         ← JSON → HTML renderer
 ├─ componentRegistry.ts     ← Component registry
 ├─ components/
 │    ├─ TextBlock.svelte
 │    ├─ Button.svelte
 │    └─ MetricCard.svelte
 └─ renderer.html           ← iframe entry point
```

## Mock API Server

The mock API server (`mock-api-server.js`) simulates a production schema API:

- **Endpoint:** `GET /api/schema`
- **Port:** 3001
- **Default Schema:** Loaded from `sample-schema.json`

### Using with Production APIs

In production, update the schema endpoint in [src/App.svelte](src/App.svelte) (line ~9):

```javascript
const response = await fetch('https://your-production-api.com/api/schema');
```

The mock server is for development only and can be replaced with any API that returns the same schema JSON structure.

## JSON Schema Format

```json
{
  "components": [
    {
      "id": "unique-id",
      "type": "TextBlock|Button|MetricCard",
      "x": 0,
      "y": 0,
      "w": 4,
      "h": 1,
      "props": {
        // Component-specific props
      }
    }
  ]
}
```

### Grid System

- **x, y**: Position in a 12-column grid (0-indexed)
- **w**: Width in grid units (1-12)
- **h**: Height in grid rows (1+)
- **Grid row height**: 60px

### Available Components

#### TextBlock
```json
{
  "type": "TextBlock",
  "props": {
    "text": "Your text here"
  }
}
```

#### Button
```json
{
  "type": "Button",
  "props": {
    "label": "Click me"
  }
}
```

#### MetricCard
```json
{
  "type": "MetricCard",
  "props": {
    "label": "Accuracy",
    "value": "92.3%"
  }
}
```

## Building for Production

```bash
npm run build
```

Output will be in the `dist/` directory.

## Notes

- The iframe uses `sandbox="allow-scripts allow-same-origin"` for security
- UI schema is stored in `localStorage` for persistence during the session
- No backend required—everything runs client-side
