import { describe, it, expect } from 'vitest';
import { renderMarkdown } from '../lib/markdown.js';

describe('renderMarkdown', () => {
  it('renders plain text as a paragraph', () => {
    const result = renderMarkdown('Hello world');
    expect(result).toContain('Hello world');
  });

  it('renders bold text', () => {
    const result = renderMarkdown('**bold**');
    expect(result).toContain('<strong>bold</strong>');
  });

  it('renders italic text', () => {
    const result = renderMarkdown('*italic*');
    expect(result).toContain('<em>italic</em>');
  });

  it('renders headings', () => {
    const result = renderMarkdown('# Heading 1');
    expect(result).toContain('<h1');
  });

  it('renders h2 headings', () => {
    const result = renderMarkdown('## Heading 2');
    expect(result).toContain('<h2');
  });

  it('renders code blocks', () => {
    const result = renderMarkdown('```js\nconsole.log("hi")\n```');
    expect(result).toContain('<code');
  });

  it('renders inline code', () => {
    const result = renderMarkdown('`inline code`');
    expect(result).toContain('<code>inline code</code>');
  });

  it('renders unordered lists', () => {
    const result = renderMarkdown('- item 1\n- item 2');
    expect(result).toContain('<ul');
    expect(result).toContain('<li>item 1</li>');
    expect(result).toContain('<li>item 2</li>');
  });

  it('renders ordered lists', () => {
    const result = renderMarkdown('1. first\n2. second');
    expect(result).toContain('<ol');
  });

  it('renders links', () => {
    const result = renderMarkdown('[link](https://example.com)');
    expect(result).toContain('<a');
    expect(result).toContain('href="https://example.com"');
    expect(result).toContain('link</a>');
  });

  it('renders blockquotes', () => {
    const result = renderMarkdown('> This is a quote');
    expect(result).toContain('<blockquote');
  });

  it('renders strikethrough', () => {
    const result = renderMarkdown('~~strikethrough~~');
    expect(result).toContain('<del');
  });

  it('returns empty string for empty input', () => {
    const result = renderMarkdown('');
    expect(typeof result).toBe('string');
    expect(result).toBe('');
  });

  it('returns empty string for null input', () => {
    const result = renderMarkdown(null);
    expect(typeof result).toBe('string');
    expect(result).toBe('');
  });

  it('sanitizes XSS attempts with script tags', () => {
    const result = renderMarkdown('<script>alert("xss")</script>');
    expect(result).not.toContain('<script>');
  });

  it('sanitizes XSS attempts with onerror attributes', () => {
    const result = renderMarkdown('<img onerror="alert(\'xss\')" src="x">');
    expect(result).not.toContain('onerror');
  });

  it('preserves safe HTML attributes', () => {
    const result = renderMarkdown('[link](https://example.com "title")');
    expect(result).toContain('href="https://example.com"');
  });

  it('handles mixed markdown with emphasis and code', () => {
    const result = renderMarkdown('**bold** and `code` and *italic*');
    expect(result).toContain('<strong>bold</strong>');
    expect(result).toContain('<code>code</code>');
    expect(result).toContain('<em>italic</em>');
  });

  it('handles nested formatting', () => {
    const result = renderMarkdown('***bold and italic***');
    expect(result).toContain('<strong');
    expect(result).toContain('<em');
  });

  it('converts newlines to breaks', () => {
    const result = renderMarkdown('line 1\nline 2');
    expect(result).toContain('<br');
  });
});
