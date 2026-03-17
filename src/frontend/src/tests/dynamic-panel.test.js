import { describe, it, expect } from 'vitest';

/**
 * Tests for DynamicPanel logic.
 * These are unit tests for the JS logic extracted from DynamicPanel.svelte.
 */

// Helper: simulate the componentState initialization logic from DynamicPanel
function initializeComponentState(elements, existing = {}) {
  const patch = {};
  for (const el of elements) {
    if (el.type === 'text_input' && !(el.id in existing)) {
      patch[el.id] = { value: el.value || '' };
    }
  }
  return { ...existing, ...patch };
}

describe('DynamicPanel – componentState initialization', () => {
  it('initializes text_input elements with default empty value', () => {
    const elements = [{ id: 'input1', type: 'text_input' }];
    const state = initializeComponentState(elements);
    expect(state['input1']).toBeDefined();
    expect(state['input1'].value).toBe('');
  });

  it('uses element.value as default if provided', () => {
    const elements = [{ id: 'input1', type: 'text_input', value: 'hello' }];
    const state = initializeComponentState(elements);
    expect(state['input1'].value).toBe('hello');
  });

  it('does not overwrite existing state for an input', () => {
    const elements = [{ id: 'input1', type: 'text_input', value: 'new' }];
    const existing = { input1: { value: 'user-typed' } };
    const state = initializeComponentState(elements, existing);
    expect(state['input1'].value).toBe('user-typed');
  });

  it('does not initialize state for non-text_input elements', () => {
    const elements = [
      { id: 'btn1', type: 'button' },
      { id: 'tbl1', type: 'table', columns: [], rows: [] },
    ];
    const state = initializeComponentState(elements);
    expect(state['btn1']).toBeUndefined();
    expect(state['tbl1']).toBeUndefined();
  });

  it('initializes multiple text inputs', () => {
    const elements = [
      { id: 'a', type: 'text_input' },
      { id: 'b', type: 'text_input', value: 'preset' },
    ];
    const state = initializeComponentState(elements);
    expect(state['a'].value).toBe('');
    expect(state['b'].value).toBe('preset');
  });

  it('initializes mixed element types but only for text_input', () => {
    const elements = [
      { id: 'input1', type: 'text_input' },
      { id: 'button1', type: 'button' },
      { id: 'input2', type: 'text_input', value: 'value2' },
      { id: 'table1', type: 'table' },
    ];
    const state = initializeComponentState(elements);
    expect(Object.keys(state)).toHaveLength(2);
    expect(state['input1']).toBeDefined();
    expect(state['input2']).toBeDefined();
    expect(state['button1']).toBeUndefined();
    expect(state['table1']).toBeUndefined();
  });

  it('preserves all existing state when merging', () => {
    const elements = [{ id: 'input1', type: 'text_input', value: 'new' }];
    const existing = {
      input1: { value: 'preserved' },
      input2: { value: 'other' },
    };
    const state = initializeComponentState(elements, existing);
    expect(state['input1'].value).toBe('preserved');
    expect(state['input2'].value).toBe('other');
  });
});

// Helper: simulate the panel elements persistence logic
function savePanelElements(panelElementsByConv, conversationId, elements) {
  if (!conversationId) return panelElementsByConv;
  return { ...panelElementsByConv, [conversationId]: elements };
}

function restorePanelElements(panelElementsByConv, conversationId) {
  return panelElementsByConv[conversationId] || [];
}

describe('Panel elements persistence', () => {
  it('saves elements keyed by conversationId', () => {
    const store = {};
    const updated = savePanelElements(store, 'conv-1', [{ id: 'el1', type: 'table' }]);
    expect(updated['conv-1']).toHaveLength(1);
  });

  it('restores elements for a given conversationId', () => {
    const store = { 'conv-1': [{ id: 'el1', type: 'table' }] };
    const restored = restorePanelElements(store, 'conv-1');
    expect(restored).toHaveLength(1);
    expect(restored[0].id).toBe('el1');
  });

  it('returns empty array for unknown conversationId', () => {
    const store = {};
    const restored = restorePanelElements(store, 'unknown');
    expect(restored).toEqual([]);
  });

  it('does not save when conversationId is null', () => {
    const store = {};
    const updated = savePanelElements(store, null, [{ id: 'el1', type: 'table' }]);
    expect(Object.keys(updated)).toHaveLength(0);
  });

  it('does not save when conversationId is undefined', () => {
    const store = {};
    const updated = savePanelElements(store, undefined, [{ id: 'el1', type: 'table' }]);
    expect(Object.keys(updated)).toHaveLength(0);
  });

  it('does not save when conversationId is empty string', () => {
    const store = {};
    const updated = savePanelElements(store, '', [{ id: 'el1', type: 'table' }]);
    expect(Object.keys(updated)).toHaveLength(0);
  });

  it('overwrites previous elements for same conversation', () => {
    let store = {};
    store = savePanelElements(store, 'conv-1', [{ id: 'el1' }]);
    store = savePanelElements(store, 'conv-1', [{ id: 'el1' }, { id: 'el2' }]);
    expect(store['conv-1']).toHaveLength(2);
  });

  it('maintains separate element lists for different conversations', () => {
    let store = {};
    store = savePanelElements(store, 'conv-1', [{ id: 'el1' }]);
    store = savePanelElements(store, 'conv-2', [{ id: 'el2' }, { id: 'el3' }]);
    expect(store['conv-1']).toHaveLength(1);
    expect(store['conv-2']).toHaveLength(2);
    expect(restorePanelElements(store, 'conv-1')[0].id).toBe('el1');
    expect(restorePanelElements(store, 'conv-2')).toHaveLength(2);
  });

  it('saves empty element arrays', () => {
    const store = {};
    const updated = savePanelElements(store, 'conv-1', []);
    expect(updated['conv-1']).toEqual([]);
  });

  it('preserves other conversations when saving a new one', () => {
    let store = { 'conv-1': [{ id: 'el1' }] };
    store = savePanelElements(store, 'conv-2', [{ id: 'el2' }]);
    expect(store['conv-1']).toHaveLength(1);
    expect(store['conv-2']).toHaveLength(1);
  });
});
