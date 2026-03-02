from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI()

# Get the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCHEMA_PATH = os.path.join(BASE_DIR, 'sample-schema.json')

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


# Pydantic models
class ComponentProps(BaseModel):
    query: Optional[str] = None
    messages: Optional[List[Dict[str, str]]] = None
    class Config:
        extra = "allow"


class Component(BaseModel):
    id: str
    type: str
    props: Optional[ComponentProps] = None
    class Config:
        extra = "allow"


class SchemaRequest(BaseModel):
    components: Optional[List[Component]] = None
    class Config:
        extra = "allow"


# Function to load schema from file
def load_schema() -> Dict[str, Any]:
    try:
        with open(SCHEMA_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f'Schema file not found at {SCHEMA_PATH}')
        raise HTTPException(status_code=500, detail='Failed to load schema')
    except json.JSONDecodeError:
        logger.error('Failed to decode schema JSON')
        raise HTTPException(status_code=500, detail='Failed to load schema')
    except Exception as error:
        logger.error(f'Failed to load schema: {error}')
        raise HTTPException(status_code=500, detail='Failed to load schema')


@app.get('/api/schema')
def get_schema():
    """Endpoint to serve the schema"""
    try:
        schema = load_schema()
        return schema
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f'Error in GET /api/schema: {error}')
        raise HTTPException(status_code=500, detail='Failed to load schema')


@app.post('/api/schema')
def post_schema(request: SchemaRequest):
    """Endpoint to fetch schema with current component state"""
    try:
        current_components = request.components or []
        schema = load_schema()
        
        # Log the received payload for debugging
        logger.info('Received payload:')
        logger.info(f'- Components: {json.dumps([c.dict() for c in current_components], indent=2)}')
        
        # Check if any ChatWindow component has a query field
        chat_window_component = None
        for comp in current_components:
            if comp.type == 'ChatWindow' and comp.props and comp.props.query:
                chat_window_component = comp
                break
        
        if chat_window_component:
            user_query = chat_window_component.props.query
            logger.info(f'- Chat query received: {user_query}')
            
            # Find the corresponding ChatWindow in the schema and update its messages
            corresponding_component = None
            for comp in schema.get('components', []):
                if comp.get('id') == chat_window_component.id and comp.get('type') == 'ChatWindow':
                    corresponding_component = comp
                    break
            
            if corresponding_component:
                # Use the messages from currentComponents (which already has all accumulated messages)
                # instead of the fresh schema's messages
                if 'props' not in corresponding_component:
                    corresponding_component['props'] = {}
                
                if 'messages' not in corresponding_component['props']:
                    corresponding_component['props']['messages'] = []
                
                # Copy existing messages from currentComponents
                if (chat_window_component.props.messages and 
                    len(chat_window_component.props.messages) > 0):
                    corresponding_component['props']['messages'] = chat_window_component.props.messages.copy()
                
                # Add the new user message
                corresponding_component['props']['messages'].append({
                    'text': user_query,
                    'sender': 'user'
                })
                
                # Add a mock assistant response
                corresponding_component['props']['messages'].append({
                    'text': 'mock response',
                    'sender': 'assistant'
                })
                
                logger.info(f"- Updated ChatWindow messages. Total: {len(corresponding_component['props']['messages'])}")
        else:
            logger.info('- No query in ChatWindow, returning fresh schema from disk')
        
        # Return the schema (either with appended messages or fresh from disk)
        return schema
    except HTTPException:
        raise
    except Exception as error:
        logger.error(f'Error in POST /api/schema: {error}')
        raise HTTPException(status_code=500, detail='Failed to process schema')


@app.get('/health')
def health_check():
    """Health check endpoint"""
    return {'status': 'ok'}


@app.on_event('startup')
def startup_event():
    logger.info('Mock API server starting...')
    logger.info(f'Schema path: {SCHEMA_PATH}')


if __name__ == '__main__':
    import uvicorn
    PORT = 3001
    logger.info(f'Mock API server running on http://localhost:{PORT}')
    logger.info(f'Schema endpoint: http://localhost:{PORT}/api/schema (GET or POST)')
    uvicorn.run(app, host='0.0.0.0', port=PORT)
