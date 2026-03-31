---
name: browser-tester
description: Runs browser and UI tests for the frontend project
tools: Read, Bash, Glob, Grep
model: sonnet
---

You are a senior frontend QA engineer...
```

The frontmatter defines metadata and configuration. The body becomes the system prompt. Sub-agents receive only this system prompt plus basic environment details — not the full Claude Code system prompt.

---

## The Core Sub-Agents to Create for a Frontend Project

Based on real-world pipelines, the recommended set is:

### 1. `planner-researcher` — Opus or Sonnet
Reads an enhancement or feature request, writes a working spec, asks clarifying questions, and sets status `READY_FOR_BUILD`.  Give it **read-only tools** (`Read, Glob, Grep`) so it can't accidentally modify anything.

### 2. `architect-reviewer` — Opus
Validates the plan against your project's constraints (component structure, state management patterns, design system rules). Produces an ADR (Architecture Decision Record).

### 3. `implementer` — Sonnet
The workhorse. Full tool access (`Read, Write, Edit, Bash`). Scoped strictly to its assigned files/domain. A frontend agent owns React components, UI state, and forms. A backend agent owns API routes. The critical rule: parallel only works when agents touch different files.

### 4. `browser-tester` — Sonnet
An expert debugger that systematically goes through error messages, stack traces, and logs to find the root cause of a problem.  For frontend: runs Playwright, checks console errors, validates responsive breakpoints. Give it `Read, Bash, Glob`.

### 5. `code-reviewer` — Sonnet
A read-only reviewer — deselect everything except read-only tools (`Read, Glob, Grep`). Reviews code for quality, security, and best practices.  Use `memory: user` so it learns your codebase's patterns over time.

### 6. `debugger` — Sonnet
Turns troubleshooting from a frustrating guessing game into a methodical process — cuts down time spent figuring out why something is broken.  Scoped to `Read, Bash, Grep` only — no write access.

---

## Key Best Practices

**Make Claude actually use your agents.** Claude Code will execute everything itself by default. To summon sub-agents more reliably, add explicit delegation rules to your `CLAUDE.md`  like:
```
During implementation, delegate tasks as follows:
- Use `planner-researcher` for feature planning
- Use `browser-tester` to run and analyze test results
- Use `code-reviewer` before any PR
