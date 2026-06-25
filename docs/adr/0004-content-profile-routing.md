# ADR-0004: Content Profile as the routing model

- **Status:** Accepted (not yet implemented)
- **Date:** 2026-06-22

## Context

Today the classifier makes a single binary decision — `classify_url` returns
`ContentType.VIDEO` or `ContentType.ARTICLE` — and that one value selects the
extractor. The prompt and the template are fixed regardless of what was clipped.

This is too coarse for content that is neither a plain article nor a video. The
motivating case is **GitHub repositories**, which Matt clips frequently: a repo page
is technically HTML (so the article extractor handles it), but a good summary should
prompt specifically for language, repository activity, and README structure — and may
warrant a dedicated template. More cases will follow.

Hardcoding GitHub logic into the classifier would not scale and would re-introduce the
personalization leakage that [ADR-0003](0003-personalization-boundary.md) forbids.

## Decision

Introduce the **Content Profile** as the routing model. A Content Profile is a named
bundle of behavior selected per clipping:

- **matcher** — how the profile is selected (e.g. a URL regex).
- **extractor** — *optional*. If omitted, the profile inherits the default
  classifier-driven extractor. A profile MAY override it when a source deserves a
  different ingestion path.
- **prompt** — what the LLM is asked to do for this kind of content.
- **template** — how the resulting processed note is rendered.

The existing `VIDEO` and `ARTICLE` `ContentType`s become the two built-in **default
profiles**. Custom profiles (GitHub first) layer on top.

**Layered model (Model B):** a profile conceptually owns all four axes, but in the
common case it overrides only **prompt + template** and inherits the default
extractor. The extractor axis is pluggable but optional — GitHub can start as
"article extractor + GitHub prompt + GitHub template" and graduate to a dedicated
extractor later without the concept changing.

Canonical illustration of the optional extractor axis: a forker adding LinkedIn
support could define a LinkedIn profile whose extractor calls a third-party scraper API
(e.g. Bright Data) instead of fighting LinkedIn's scraping protections — without
touching the pipeline.

## Consequences

- **Good:** content-type-specific summarization (better, more relevant summaries)
  without special-casing the classifier.
- **Good:** new content types are additive — define a profile, not a code branch.
- **Good:** profiles' prompts/templates are personalization surface and fall cleanly
  under [ADR-0003](0003-personalization-boundary.md); the pipeline stays vault- and
  source-agnostic.
- **Good:** the optional extractor override gives forkers a clean extension point
  (the LinkedIn/Bright Data case) without forking the pipeline.
- **Cost / open questions (to resolve at implementation):** how profiles are
  configured (in `config.yaml` vs a dedicated registry); matcher precedence when
  several match; how a profile's extractor override composes with the existing
  classifier; and the interaction with the v2 design's URL classifier, which this
  generalizes.
- **Status note:** Accepted as direction so future work does not hardcode GitHub
  logic into the classifier. No code exists yet; implementation may refine the shape,
  but should reopen this ADR rather than silently diverge.
