import { describe, it, expect } from 'vitest';

/**
 * Tests for the agent form validation logic used in AgentManager.svelte.
 *
 * The validation rules are extracted from saveAgent() and tested as pure
 * functions so no Svelte rendering is required.
 */

// ---------------------------------------------------------------------------
// Validation helpers (mirrors AgentManager.svelte logic)
// ---------------------------------------------------------------------------

function validateEndpoint(endpoint) {
  if (!endpoint) return '';
  if (!/^https?:\/\/.+/.test(endpoint.trim())) {
    return 'Endpoint URL must start with http:// or https://';
  }
  return '';
}

function validateExtrasJson(extrasStr) {
  if (!extrasStr || !extrasStr.trim()) return '';
  try {
    JSON.parse(extrasStr);
    return '';
  } catch {
    return 'Invalid JSON in extras field';
  }
}

function validateLangGraphForm({ connection_type, assistant_name }) {
  if (connection_type !== 'langgraph') return '';
  if (!assistant_name) return 'Please select an assistant for the LangGraph connection';
  return '';
}

function validateOpenAIForm({ connection_type, openai_model }) {
  if (connection_type !== 'openai') return '';
  if (!openai_model) return 'Please select a model for the OpenAI connection';
  return '';
}

// ---------------------------------------------------------------------------
// Endpoint URL validation
// ---------------------------------------------------------------------------

describe('Endpoint URL validation', () => {
  it('accepts http:// URLs', () => {
    expect(validateEndpoint('http://localhost:8000')).toBe('');
  });

  it('accepts https:// URLs', () => {
    expect(validateEndpoint('https://api.example.com')).toBe('');
  });

  it('rejects URLs without protocol', () => {
    expect(validateEndpoint('api.example.com')).not.toBe('');
  });

  it('rejects ftp:// URLs', () => {
    expect(validateEndpoint('ftp://example.com')).not.toBe('');
  });

  it('allows empty endpoint (optional field)', () => {
    expect(validateEndpoint('')).toBe('');
  });

  it('rejects plain text', () => {
    expect(validateEndpoint('not-a-url')).not.toBe('');
  });
});

// ---------------------------------------------------------------------------
// Extras JSON validation
// ---------------------------------------------------------------------------

describe('Extras JSON validation', () => {
  it('accepts valid JSON object', () => {
    expect(validateExtrasJson('{"key": "value"}')).toBe('');
  });

  it('accepts valid JSON with nested objects', () => {
    expect(validateExtrasJson('{"a": {"b": 1}}')).toBe('');
  });

  it('rejects malformed JSON', () => {
    expect(validateExtrasJson('{bad json}')).not.toBe('');
  });

  it('accepts empty string (extras not required)', () => {
    expect(validateExtrasJson('')).toBe('');
  });

  it('accepts whitespace-only string', () => {
    expect(validateExtrasJson('   ')).toBe('');
  });
});

// ---------------------------------------------------------------------------
// LangGraph-specific validation
// ---------------------------------------------------------------------------

describe('LangGraph form validation', () => {
  it('requires assistant_name for langgraph connection', () => {
    expect(validateLangGraphForm({ connection_type: 'langgraph', assistant_name: '' }))
      .not.toBe('');
  });

  it('passes when assistant_name is provided', () => {
    expect(validateLangGraphForm({ connection_type: 'langgraph', assistant_name: 'my-assistant' }))
      .toBe('');
  });

  it('skips validation for non-langgraph connections', () => {
    expect(validateLangGraphForm({ connection_type: 'http', assistant_name: '' }))
      .toBe('');
  });
});

// ---------------------------------------------------------------------------
// OpenAI-specific validation
// ---------------------------------------------------------------------------

describe('OpenAI form validation', () => {
  it('requires a model for openai connection', () => {
    expect(validateOpenAIForm({ connection_type: 'openai', openai_model: '' }))
      .not.toBe('');
  });

  it('passes when model is selected', () => {
    expect(validateOpenAIForm({ connection_type: 'openai', openai_model: 'gpt-4o' }))
      .toBe('');
  });

  it('skips validation for non-openai connections', () => {
    expect(validateOpenAIForm({ connection_type: 'http', openai_model: '' }))
      .toBe('');
  });
});

// ---------------------------------------------------------------------------
// Combined form validation scenario
// ---------------------------------------------------------------------------

describe('Full agent form validation', () => {
  function validateAgentForm(form) {
    const endpointErr = validateEndpoint(form.endpoint);
    if (endpointErr) return endpointErr;

    const extrasErr = validateExtrasJson(form.extras);
    if (extrasErr) return extrasErr;

    const lgErr = validateLangGraphForm(form);
    if (lgErr) return lgErr;

    const oaiErr = validateOpenAIForm(form);
    if (oaiErr) return oaiErr;

    return '';
  }

  it('rejects form with invalid endpoint', () => {
    const form = { endpoint: 'not-a-url', extras: '', connection_type: 'http', assistant_name: '', openai_model: '' };
    expect(validateAgentForm(form)).not.toBe('');
  });

  it('rejects form with invalid extras JSON', () => {
    const form = { endpoint: 'https://x.com', extras: '{bad}', connection_type: 'http', assistant_name: '', openai_model: '' };
    expect(validateAgentForm(form)).not.toBe('');
  });

  it('accepts valid http form', () => {
    const form = { endpoint: 'https://api.example.com', extras: '{}', connection_type: 'http', assistant_name: '', openai_model: '' };
    expect(validateAgentForm(form)).toBe('');
  });

  it('accepts valid openai form with model selected', () => {
    const form = { endpoint: 'https://api.openai.com', extras: '', connection_type: 'openai', assistant_name: '', openai_model: 'gpt-4o' };
    expect(validateAgentForm(form)).toBe('');
  });
});
