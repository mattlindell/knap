# Issue Tracker

Issues for this repo are tracked in **Linear**, accessed through the **Linear MCP**
(no `gh`/`glab` CLI). Skills like `to-issues`, `triage`, `to-prd`, and `qa` should
create and read issues using the Linear MCP tools (`mcp__linear__*`).

## Where issues live

- **Workspace team:** Photon Ventures (key `PV`, id `9e1c5abb-f150-44d7-9edc-edc40933c57e`)
- **Project:** Tool Chest (id `138e9455-b8cb-4bc4-81d6-959fa5c4884f`)
  — https://linear.app/photn/project/tool-chest-5a4b43a8e77c
- **Required label:** every issue for this repo gets the `summarizer` label
  (id `92d91a25-45ce-4525-b140-16fc264c9c8b`)

## Creating an issue

Use `mcp__linear__save_issue` (the create/update tool) with:

- `team`: `Photon Ventures` (or id `9e1c5abb-f150-44d7-9edc-edc40933c57e`)
- `project`: `Tool Chest` (or id `138e9455-b8cb-4bc4-81d6-959fa5c4884f`)
- `labels`: include `summarizer` plus any triage label (see `triage-labels.md`)
- `title` / `description`: markdown body, real newlines (no escaped `\n`)

## Reading / finding issues

Use `mcp__linear__list_issues` filtered by `team` + `project` (+ `label` `summarizer`),
or `mcp__linear__get_issue` for a specific one.

## Conventions

- Always apply the `summarizer` label so the repo's work is filterable inside the
  shared Tool Chest project.
- Apply exactly one triage state label at a time (they're a mutually-exclusive group).
