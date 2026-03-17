// Generic action execution for dashboard widgets.
// This is intentionally conservative: only a small, safe set of actions
// is supported and callers must explicitly pass any context needed.

/**
 * Execute a configured action.
 *
 * @param {{ type: string, config?: any }} action
 * @param {{ project?: string, user?: any, fields?: Record<string, any>, state?: Record<string, any> }} context
 */
export function executeAction(action, context = {}) {
  if (!action || !action.type) {
    return;
  }

  const type = action.type;
  const config = action.config || {};

  switch (type) {
    case "open_url": {
      const url = interpolate(config.url, context);
      if (!url) return;
      const target = config.target === "_self" ? "_self" : "_blank";
      window.open(url, target);
      break;
    }
    case "navigate": {
      const route = interpolate(config.route, context);
      if (!route) return;
      const prefix = context.project ? `/${encodeURIComponent(context.project)}` : "";
      const normalizedRoute = route.startsWith("/") ? route : "/" + route;
      const fullRoute = normalizedRoute.startsWith(prefix) ? normalizedRoute : prefix + normalizedRoute;
      window.history.pushState({}, "", fullRoute);
      window.dispatchEvent(new PopStateEvent("popstate"));
      break;
    }
    case "download": {
      const url = interpolate(config.url, context);
      if (!url) return;
      const a = document.createElement("a");
      a.href = url;
      a.download = config.filename
        ? interpolate(config.filename, context) || config.filename
        : "";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      break;
    }
    case "send_chat_message": {
      // In the dashboard context, we dispatch an event that ChatWidget can listen for.
      const message = interpolate(config.message, context);
      if (!message) return;
      window.dispatchEvent(
        new CustomEvent("dashboard:send_chat_message", {
          detail: {
            message,
            agentId: config.agent_id || null,
            project: context.project || null,
            fields: context.fields || {},
          },
        }),
      );
      break;
    }
    default:
      // Unknown or unsupported action type; ignore for now.
      break;
  }
}

/**
 * Very small, JSON-safe templating helper using {{ }} placeholders.
 */
function interpolate(template, context) {
  if (!template || typeof template !== "string") return template;

  return template.replace(/{{\s*([^}]+)\s*}}/g, (_, expr) => {
    try {
      const path = expr.split(".");
      let value = context;
      for (const key of path) {
        if (value == null) return "";
        value = value[key];
      }
      return value == null ? "" : String(value);
    } catch {
      return "";
    }
  });
}

