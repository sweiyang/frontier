import express from 'express';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const app = express();
const PORT = 3001;
const schemaPath = path.join(__dirname, 'sample-schema.json');

// Function to load schema from file
function loadSchema() {
  try {
    const schemaFile = fs.readFileSync(schemaPath, 'utf-8');
    return JSON.parse(schemaFile);
  } catch (error) {
    console.error('Failed to load schema:', error);
    throw error;
  }
}

// Middleware
app.use(express.json());

// CORS middleware
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type');
  next();
});

// API endpoint to serve the schema
app.get('/api/schema', (req, res) => {
  try {
    const schema = loadSchema();
    res.json(schema);
  } catch (error) {
    res.status(500).json({ error: 'Failed to load schema' });
  }
});

// API endpoint to fetch schema with current component state
app.post('/api/schema', (req, res) => {
  try {
    const currentComponents = req.body.components || [];
    const schema = loadSchema();
    
    // Log the received payload for debugging
    console.log('Received payload:');
    console.log('- Components:', JSON.stringify(currentComponents, null, 2));
    
    // Check if any ChatWindow component has a query field
    const chatWindowComponent = currentComponents.find(
      comp => comp.type === 'ChatWindow' && comp.props && comp.props.query
    );
    
    if (chatWindowComponent) {
      const userQuery = chatWindowComponent.props.query;
      console.log('- Chat query received:', userQuery);
      
      // Find the corresponding ChatWindow in the schema and update its messages
      const correspondingComponent = schema.components.find(
        comp => comp.id === chatWindowComponent.id && comp.type === 'ChatWindow'
      );
      
      if (correspondingComponent) {
        // Use the messages from currentComponents (which already has all accumulated messages)
        // instead of the fresh schema's messages
        if (!correspondingComponent.props.messages) {
          correspondingComponent.props.messages = [];
        }
        
        // Copy existing messages from currentComponents
        if (chatWindowComponent.props.messages && chatWindowComponent.props.messages.length > 0) {
          correspondingComponent.props.messages = [...chatWindowComponent.props.messages];
        }
        
        // Add the new user message
        correspondingComponent.props.messages.push({
          text: userQuery,
          sender: 'user'
        });
        
        // Add a mock assistant response
        correspondingComponent.props.messages.push({
          text: 'mock response',
          sender: 'assistant'
        });
        
        console.log('- Updated ChatWindow messages. Total:', correspondingComponent.props.messages.length);
      }
    } else {
      console.log('- No query in ChatWindow, returning fresh schema from disk');
    }
    
    // Return the schema (either with appended messages or fresh from disk)
    res.json(schema);
  } catch (error) {
    res.status(500).json({ error: 'Failed to load schema' });
  }
});

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`Mock API server running on http://localhost:${PORT}`);
  console.log(`Schema endpoint: http://localhost:${PORT}/api/schema (GET or POST)`);
});
