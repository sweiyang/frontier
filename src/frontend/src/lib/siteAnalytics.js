/**
 * Lightweight site analytics tracker for published dashboard sites.
 *
 * Buffers events in memory and flushes every 5 seconds (or on page unload via
 * navigator.sendBeacon). All network calls are fire-and-forget.
 */

const FLUSH_INTERVAL_MS = 5000;
const MAX_BATCH = 50;

let _buffer = [];
let _project = null;
let _flushTimer = null;

function _getSessionId() {
  let sid = sessionStorage.getItem("_sa_sid");
  if (!sid) {
    sid = crypto.randomUUID();
    sessionStorage.setItem("_sa_sid", sid);
  }
  return sid;
}

function _push(event) {
  event.session_id = _getSessionId();
  _buffer.push(event);
  if (_buffer.length >= MAX_BATCH) {
    flush();
  }
}

/** Flush buffered events to the server. */
export function flush() {
  if (!_buffer.length || !_project) return;
  const events = _buffer.splice(0, MAX_BATCH);
  const url = `/projects/${encodeURIComponent(_project)}/dashboard/analytics`;
  const body = JSON.stringify({ events });
  try {
    navigator.sendBeacon(url, new Blob([body], { type: "application/json" }));
  } catch {
    // Fallback to fetch (sendBeacon may not be available in all contexts)
    fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
      keepalive: true,
    }).catch(() => {});
  }
}

/**
 * Initialise the tracker for a given project.
 * Safe to call multiple times — re-init resets the timer.
 */
export function initTracker(project) {
  _project = project;
  if (_flushTimer) clearInterval(_flushTimer);
  _flushTimer = setInterval(flush, FLUSH_INTERVAL_MS);
  window.addEventListener("beforeunload", flush);
}

/** Destroy the tracker and flush remaining events. */
export function destroyTracker() {
  flush();
  if (_flushTimer) {
    clearInterval(_flushTimer);
    _flushTimer = null;
  }
  window.removeEventListener("beforeunload", flush);
}

// --- Public tracking helpers ------------------------------------------------

export function trackPageView(pageId, pagePath) {
  _push({ event_type: "page_view", page_id: pageId, page_path: pagePath });
}

export function trackButtonClick(componentId, label) {
  _push({
    event_type: "button_click",
    component_id: componentId,
    component_type: "button",
    metadata: label ? { label } : undefined,
  });
}

export function trackFormSubmit(componentId) {
  _push({
    event_type: "form_submit",
    component_id: componentId,
    component_type: "form",
  });
}

export function trackTableAction(componentId, actionName) {
  _push({
    event_type: "table_action",
    component_id: componentId,
    component_type: "table",
    metadata: actionName ? { action: actionName } : undefined,
  });
}
