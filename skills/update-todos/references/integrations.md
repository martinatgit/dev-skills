# Optional cross-skill integration contract

This is a **soft contract**. Other skills MAY honour it; nothing in `update-todos` requires it. If your project does not use the listed skills, ignore this file entirely.

## Producers (skills that may emit signals into the TODO corpus)

| Skill (example) | Action |
|---|---|
| `project-audit` (or any audit-style skill) | Emits one TODO per identified spec/implementation gap. |
| `developer-diary update` | When editing a diary node whose `references[]` overlap edited files, prompts: "does this change resolve / touch TODO-X?" |

## Consumers (skills that may read from the TODO corpus)

| Skill (example) | Signal consumed | Behaviour |
|---|---|---|
| `project-context` (session start) | Open-TODO count, clarify-pending count, blocked-with-resolved-blocker count, expiring-within-7-days count, orphan count | Surface as a session-start summary so users see the TODO state without invoking `list`. |
| `superpowers:brainstorming` | TODOs with `next-step: brainstorm` | May be picked up as brainstorming candidates. |
| `superpowers:writing-plans` | TODOs with `priority: high` and `next-step: implementation` | May be picked up as planning candidates. |
| `superpowers:systematic-debugging` | TODOs with `next-step: reproduce` | May be picked up as bug-reproduction starting points. |

## Naming conventions for related links

When `clarify` enforces "≥1 related link", honour these conventions if your project has them:

- Other TODO ids: `TODO-YYYYMMDD-NNNN`.
- Diary nodes: relative path to the `diary-entry.md`, plus optional `#section` anchor.
- Spec sections: relative path to the spec file, plus `#§x.y` style anchor.
- External references: full URL.

## Bidirectional contract with `developer-diary`

If your project uses both `update-todos` and `developer-diary`:

- Every TODO's `discovered-in-task` frontmatter SHOULD identify the diary node where the observation surfaced.
- Every diary-entry "Open questions" or "Special instructions for next reader" item MUST either reference a TODO id, or be resolved inline that session.
- `update-todos review` validates both directions and reports violations under "Warnings" in `<root_dir>/index.md`.

## Disabling integrations

To disable any integration, simply remove or rename the consumer skill. `update-todos` itself never depends on these skills being present — it produces a self-consistent TODO corpus regardless.
