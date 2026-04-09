/**
 * Markdown rendering utility with syntax highlighting and sanitization.
 */

import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import hljs from 'highlight.js';
import taskLists from 'markdown-it-task-lists';

// Initialize markdown-it with options
const md = new MarkdownIt({
  html: true, // Enable HTML tags in source
  linkify: true, // Autoconvert URL-like text to links
  typographer: true, // Enable some language-neutral replacement + quotes beautification
  breaks: true, // Convert '\n' in paragraphs into <br>
  highlight: function (str, lang) {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return '<pre class="hljs"><code>' +
               hljs.highlight(str, { language: lang, ignoreIllegals: true }).value +
               '</code></pre>';
      } catch (__) {}
    }
    return '<pre class="hljs"><code>' + md.utils.escapeHtml(str) + '</code></pre>';
  }
}).use(taskLists);

// Enable markdown-it plugins for tables and other features
md.enable(['table', 'strikethrough']);

// Wrap tables with a toolbar for CSV download and copy
const defaultTableOpen = md.renderer.rules.table_open || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options);
};
const defaultTableClose = md.renderer.rules.table_close || function(tokens, idx, options, env, self) {
  return self.renderToken(tokens, idx, options);
};

md.renderer.rules.table_open = function(tokens, idx, options, env, self) {
  const toolbar = `<div class="table-wrapper"><div class="table-toolbar">` +
    `<button class="table-action-btn table-copy-btn" title="Copy to clipboard">` +
    `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>` +
    ` Copy</button>` +
    `<button class="table-action-btn table-csv-btn" title="Download as CSV">` +
    `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>` +
    ` CSV</button>` +
    `</div>`;
  return toolbar + defaultTableOpen(tokens, idx, options, env, self);
};

md.renderer.rules.table_close = function(tokens, idx, options, env, self) {
  return defaultTableClose(tokens, idx, options, env, self) + `</div>`;
};

/**
 * Render markdown text to sanitized HTML.
 *
 * @param {string} markdown - The markdown text to render
 * @returns {string} Sanitized HTML string
 */
export function renderMarkdown(markdown) {
  if (!markdown) return '';

  // Convert markdown to HTML
  const html = md.render(markdown);

  // Sanitize HTML to prevent XSS attacks
  const sanitized = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'p', 'br', 'strong', 'em', 'u', 's', 'code', 'pre',
      'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
      'ul', 'ol', 'li',
      'blockquote',
      'a',
      'img',
      'table', 'thead', 'tbody', 'tr', 'th', 'td',
      'hr',
      'del', 'ins',
      'div', 'button', 'span', 'svg', 'rect', 'path', 'polyline', 'line'
    ],
    ALLOWED_ATTR: [
      'href', 'title', 'alt', 'src', 'class',
      'viewBox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 'stroke-linejoin',
      'd', 'x', 'y', 'width', 'height', 'rx', 'ry', 'x1', 'y1', 'x2', 'y2', 'points'
    ],
    ALLOW_DATA_ATTR: false
  });

  return sanitized;
}
