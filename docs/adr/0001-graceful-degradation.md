# ADR-0001: Graceful degradation everywhere

- **Status:** Accepted
- **Date:** 2026-06-22

## Context

The summarizer runs unattended as a background watcher, processing clippings as the
Obsidian Web Clipper drops them. Sources are hostile and varied: paywalls, JS-rendered
pages, videos with no captions, malformed HTML, an LLM endpoint that is down or slow.

The original v1 failure mode was the worst possible one: when extraction produced
little or no text, the LLM **hallucinated** a summary from the title alone, writing a
confident but fabricated processed note. A crash would be better than a lie — but a
crash also stops the watcher and silently halts processing of every later clipping.

## Decision

Every component **degrades gracefully and never raises** out to the watcher loop:

1. **Extractors** return an empty `ContentResult` (`extraction_succeeded=False`) on
   failure — they never raise.
2. **Quality gate** catches empty/garbage extractions (below `min_content_length`)
   *before* the LLM ever sees them.
3. **LLM providers** return `None` on failure — they never raise.
4. **Pipeline** falls back to the `failed_extraction.md.j2` template when extraction
   or summarization fails, producing a `needs-review` processed note instead of a
   fabricated summary.
5. **Watcher** wraps per-clipping processing in a catch-all: it logs the error and
   keeps watching. One bad clipping never stops the service.

## Consequences

- **Good:** the service is resilient and unattended-safe; a failed clipping becomes a
  reviewable note, never a hallucination, and never halts the queue.
- **Good:** "did extraction succeed?" is an explicit, inspectable signal
  (`ContentResult.extraction_succeeded`), not an exception to be caught somewhere.
- **Cost:** failures are *quiet*. Problems surface as `needs-review` notes and log
  lines rather than loud errors, so monitoring depends on reviewing those.
- **Constraint on future work:** new extractors and providers MUST honor this
  contract — return the empty/`None` sentinel, do not raise. This is the load-bearing
  invariant the watcher's stability rests on.
