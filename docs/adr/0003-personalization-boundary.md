# ADR-0003: Personalization confined to config.yaml and templates/

- **Status:** Accepted
- **Date:** 2026-06-22

## Context

The repository is public. The project is built first for Matt's personal vault and
workflow, but it should be reusable: a stranger who stumbles onto it should be able to
run it on their own system without it being hopelessly specific to Matt's setup.

The risk is the usual one for personal tooling — vault paths, frontmatter conventions,
and Dataview queries leaking into core code until the project only works for its
author.

## Decision

All personalization is confined to **two locations**, and core pipeline code carries
no assumptions about any particular vault:

- **`config.yaml`** — paths (clippings/processed dirs), LLM provider/model/credentials,
  extraction and summarization knobs. A committed `config.example.yaml` is the
  template; the real `config.yaml` is gitignored.
- **`templates/`** — the entire output note format: frontmatter fields, the "My Notes"
  section, the Projects/Domains Dataview query, the failed-extraction layout.

The core pipeline (classifier, extractors, quality gate, providers, factory,
watcher) must remain vault-agnostic.

## Consequences

- **Good:** onboarding for a forker is "copy the example config, edit paths + LLM,
  run." No code edits required for the common case.
- **Good:** a clear test for where a change belongs — if it encodes a personal
  preference, it goes in config or a template, never in pipeline code.
- **Known gap:** the templates **currently violate the spirit** of this boundary.
  They are more coupled to Matt's vault than they should be (specific frontmatter,
  Dataview query assuming a Projects/Domains structure). Making templates cleanly
  replaceable is tracked as near-future work; this ADR sets the target state.
- **Interaction with profiles:** when Content Profiles land
  ([ADR-0004](0004-content-profile-routing.md)), per-profile prompts and templates are
  also personalization surface and live under this same boundary.
