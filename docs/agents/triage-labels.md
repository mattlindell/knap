# Triage Labels

The skills speak in terms of five canonical triage roles. In this repo they map 1:1
to existing labels in the Photon Ventures team's **"Agentic State Machine"** label
group in Linear.

| Canonical role    | Linear label      | Label id                               | Meaning                                  |
| ----------------- | ----------------- | -------------------------------------- | ---------------------------------------- |
| `needs-triage`    | `needs-triage`    | `a9de843a-bcf0-4906-83a1-aad4eecaeb59` | Maintainer needs to evaluate this issue  |
| `needs-info`      | `needs-info`      | `13054a54-9621-4f80-96e8-1021185fa227` | Waiting on reporter for more information |
| `ready-for-agent` | `ready-for-agent` | `ea516c06-a7a3-43f5-a0dc-c0f0855ad2e4` | Fully specified, ready for an AFK agent  |
| `ready-for-human` | `ready-for-human` | `47f69587-129e-477d-8957-29790bf88103` | Requires human implementation            |
| `wontfix`         | `wontfix`         | `ccef58cc-9cd1-43a2-90e1-432e96e5a83b` | Will not be actioned                     |

When a skill mentions a role (e.g. "apply the AFK-ready triage label"), apply the
corresponding Linear label via `mcp__linear__save_issue`.

## Mutual exclusivity

These labels form a **single-select state machine** in Linear — only one applies to an
issue at any time. When moving an issue to a new triage state, **remove the previous
state label as you add the new one** so an issue never carries two. Do not stack them.

The `summarizer` label (see `issue-tracker.md`) is separate from this group and stays
on the issue throughout.
