# Internal POC UI Renderer

A minimal, client-side Svelte-based UI renderer that allows you to upload a JSON definition and render it dynamically.

## Features

✅ Upload a JSON UI definition  
✅ Validate + store it locally  
✅ Render UI from JSON using a component registry  
✅ Display rendered UI inside an iframe  
✅ 100% client-side, zero backend  
✅ Safe (no user JS execution)  

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the dev server:**
   ```bash
   npm run dev
   ```

3. **Open your browser:**
   Navigate to `http://localhost:5173`

4. **Upload a JSON file:**
   Click the file input and select `sample-schema.json` to see an example dashboard

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
