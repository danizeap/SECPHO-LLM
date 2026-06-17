# Token-Smart Standards

## Purpose

Keep agent work efficient without losing the context needed to be accurate.

Token-smart means choosing the smallest reliable context, model, and tool output for the job. It does not mean skipping verification or avoiding the source of truth.

## Model And Reasoning Defaults

Before substantial work, recommend a model and reasoning setting.

- Use a smaller/cheaper model for quick lookups, identity checks, simple docs, summaries, and low-risk cleanup.
- Use a standard strong model with medium reasoning for normal coding, debugging, integration, and SDD+ work.
- Use a higher-reasoning model for architecture, security incidents, ambiguous production bugs, high-stakes data changes, complex design-to-code work, or multi-system planning.

If the task grows beyond the original setting, pause briefly and recommend switching before continuing.

## Context Budgeting

Start narrow, then expand only when evidence requires it.

- Read `PROJECT_CONTEXT.md`, `AGENTS.md`, and relevant standards first.
- Prefer targeted file searches and explicit queries over broad dumps.
- Read only the sections of large files needed for the current decision.
- Summarize long findings into SDD+ instead of re-reading them later.

## Tool Output Discipline

- Select explicit columns or counts instead of returning entire tables.
- Fetch file metadata before fetching full file content.
- Avoid fetching full PDFs/documents unless content extraction or ingestion is the goal.
- Use file-scoped diffs before broad repository diffs.
- Use focused search patterns and paths.

## When To Spend More Tokens

Spend the context when accuracy matters:

- security incidents
- production data
- secrets, auth, permissions, or billing
- customer-facing behavior
- hard-to-undo operations
- ambiguous identity or data mapping
- architecture or major refactors

## Subagent Guidance

Do not use subagents by default.

Use subagents only when parallel investigation is likely to save meaningful time or context, such as broad audits, multi-source comparisons, or large design/code reviews.
