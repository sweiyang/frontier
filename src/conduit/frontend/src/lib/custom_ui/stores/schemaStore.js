import { writable, get } from 'svelte/store';

// Deep equality check for objects
function isEqual(obj1, obj2) {
  return JSON.stringify(obj1) === JSON.stringify(obj2);
}

// Calculate and apply delta between old and new schema
function applyDelta(oldSchema, newSchema) {
  if (!oldSchema) {
    return newSchema;
  }

  // Create a copy of the old schema to mutate
  const updatedSchema = JSON.parse(JSON.stringify(oldSchema));
  
  // Create a map of old components by id for quick lookup
  const oldComponentsMap = new Map(
    oldSchema.components.map(comp => [comp.id, comp])
  );
  
  const newComponentsMap = new Map(
    newSchema.components.map(comp => [comp.id, comp])
  );

  // Update components array by applying only delta changes
  updatedSchema.components = newSchema.components.map(newComp => {
    const oldComp = oldComponentsMap.get(newComp.id);
    
    // If component exists and hasn't changed, keep the old reference
    if (oldComp && isEqual(oldComp, newComp)) {
      return oldComp;
    }
    
    // Otherwise return the new component (added or modified)
    return newComp;
  });

  return updatedSchema;
}

function createSchemaStore() {
  const { subscribe, set, update } = writable(null);

  return {
    subscribe,
    
    // Fetch schema and apply delta
    async fetchSchema(lastMessage = null, messageComponentId = null, agentEndpoint = null) {
      try {
        let payload = { components: [] };
        
        // Subscribe to get current schema value
        const unsubscribe = subscribe(currentSchema => {
          if (currentSchema) {
            // Extract id, type, props, and layout info from all current components
            // If a message was sent and we know which component it came from,
            // inject the message as a 'query' field in that component's props
            payload.components = currentSchema.components.map(comp => {
              const compData = {
                id: comp.id,
                type: comp.type,
                x: comp.x,
                y: comp.y,
                w: comp.w,
                h: comp.h,
                props: { ...comp.props }
              };
              
              // Inject the message into the ChatWindow component's props as 'query'
              if (lastMessage && messageComponentId === comp.id) {
                compData.props.query = lastMessage;
              }
              
              return compData;
            });
          }
        });
        
        unsubscribe();
        
        const schemaUrl = `${agentEndpoint}/api/schema`;
        
        const response = await fetch(schemaUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error('Failed to load schema');
        const newSchema = await response.json();
        
        // Use update to apply delta based on current schema
        update(currentSchema => applyDelta(currentSchema, newSchema));
      } catch (e) {
        console.error("Failed to load schema from API", e);
      }
    },
    
    // Direct set for initial load (faster)
    setSchema(newSchema) {
      set(newSchema);
    }
  };
}

export const schema = createSchemaStore();
