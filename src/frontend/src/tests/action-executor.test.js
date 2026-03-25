import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { executeAction } from '../lib/ActionExecutor.js';

// ---------------------------------------------------------------------------
// Setup / teardown
// ---------------------------------------------------------------------------

let openSpy;
let pushStateSpy;
let dispatchEventSpy;
let appendChildSpy;
let removeChildSpy;
let clickSpy;

beforeEach(() => {
  openSpy = vi.spyOn(window, 'open').mockImplementation(() => {});
  pushStateSpy = vi.spyOn(window.history, 'pushState').mockImplementation(() => {});
  dispatchEventSpy = vi.spyOn(window, 'dispatchEvent').mockImplementation(() => {});
  clickSpy = vi.fn();
  appendChildSpy = vi.spyOn(document.body, 'appendChild').mockImplementation((el) => {
    // Simulate the anchor click that download triggers
    if (el && el.click) el.click = clickSpy;
  });
  removeChildSpy = vi.spyOn(document.body, 'removeChild').mockImplementation(() => {});
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---------------------------------------------------------------------------
// open_url
// ---------------------------------------------------------------------------

describe('executeAction — open_url', () => {
  it('calls window.open with the configured URL', () => {
    executeAction({ type: 'open_url', config: { url: 'https://example.com' } });
    expect(openSpy).toHaveBeenCalledWith('https://example.com', '_blank');
  });

  it('opens in _self when target is "_self"', () => {
    executeAction({ type: 'open_url', config: { url: 'https://example.com', target: '_self' } });
    expect(openSpy).toHaveBeenCalledWith('https://example.com', '_self');
  });

  it('does nothing when url is empty', () => {
    executeAction({ type: 'open_url', config: { url: '' } });
    expect(openSpy).not.toHaveBeenCalled();
  });

  it('interpolates context into the URL', () => {
    // Use no spaces inside {{ }} to avoid trailing-space capture issues
    executeAction(
      { type: 'open_url', config: { url: 'https://example.com/{{project}}' } },
      { project: 'my-project' },
    );
    expect(openSpy).toHaveBeenCalledWith('https://example.com/my-project', '_blank');
  });
});

// ---------------------------------------------------------------------------
// navigate
// ---------------------------------------------------------------------------

describe('executeAction — navigate', () => {
  it('calls history.pushState with the route', () => {
    executeAction({ type: 'navigate', config: { route: '/dashboard' } }, { project: 'proj' });
    expect(pushStateSpy).toHaveBeenCalled();
    const url = pushStateSpy.mock.calls[0][2];
    expect(url).toContain('/dashboard');
  });

  it('dispatches a popstate event after navigation', () => {
    executeAction({ type: 'navigate', config: { route: '/page' } }, {});
    expect(dispatchEventSpy).toHaveBeenCalled();
  });

  it('does nothing when route is empty', () => {
    executeAction({ type: 'navigate', config: { route: '' } });
    expect(pushStateSpy).not.toHaveBeenCalled();
  });

  it('prepends project prefix when project is in context', () => {
    executeAction({ type: 'navigate', config: { route: '/settings' } }, { project: 'alpha' });
    const url = pushStateSpy.mock.calls[0][2];
    expect(url).toContain('alpha');
  });
});

// ---------------------------------------------------------------------------
// download
// ---------------------------------------------------------------------------

describe('executeAction — download', () => {
  it('appends an anchor element and removes it after click', () => {
    executeAction({ type: 'download', config: { url: '/files/report.csv' } });
    expect(appendChildSpy).toHaveBeenCalled();
    expect(removeChildSpy).toHaveBeenCalled();
  });

  it('sets the anchor href to the configured URL', () => {
    let capturedEl = null;
    appendChildSpy.mockImplementation((el) => { capturedEl = el; });
    executeAction({ type: 'download', config: { url: '/files/data.csv', filename: 'data.csv' } });
    expect(capturedEl.href).toContain('/files/data.csv');
    expect(capturedEl.download).toBe('data.csv');
  });

  it('does nothing when url is empty', () => {
    executeAction({ type: 'download', config: { url: '' } });
    expect(appendChildSpy).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// send_chat_message
// ---------------------------------------------------------------------------

describe('executeAction — send_chat_message', () => {
  it('dispatches a dashboard:send_chat_message event', () => {
    executeAction(
      { type: 'send_chat_message', config: { message: 'Hello {{fields.name}}' } },
      { project: 'proj', fields: { name: 'Alice' } },
    );
    expect(dispatchEventSpy).toHaveBeenCalledOnce();
    const event = dispatchEventSpy.mock.calls[0][0];
    expect(event.type).toBe('dashboard:send_chat_message');
    expect(event.detail.message).toBe('Hello Alice');
    expect(event.detail.project).toBe('proj');
  });

  it('does nothing when message is empty after interpolation', () => {
    executeAction({ type: 'send_chat_message', config: { message: '' } });
    expect(dispatchEventSpy).not.toHaveBeenCalled();
  });
});

// ---------------------------------------------------------------------------
// Unknown / missing action type
// ---------------------------------------------------------------------------

describe('executeAction — unknown / missing', () => {
  it('does nothing for an unknown action type', () => {
    executeAction({ type: 'unknown_action', config: {} });
    expect(openSpy).not.toHaveBeenCalled();
    expect(pushStateSpy).not.toHaveBeenCalled();
  });

  it('does nothing when action is null', () => {
    expect(() => executeAction(null)).not.toThrow();
  });

  it('does nothing when action.type is missing', () => {
    expect(() => executeAction({ config: {} })).not.toThrow();
  });
});

// ---------------------------------------------------------------------------
// Return value
// ---------------------------------------------------------------------------

describe('executeAction — return value', () => {
  it('returns undefined for all action types', () => {
    expect(executeAction({ type: 'open_url', config: { url: 'https://x.com' } })).toBeUndefined();
    expect(executeAction({ type: 'unknown', config: {} })).toBeUndefined();
    expect(executeAction(null)).toBeUndefined();
  });
});
