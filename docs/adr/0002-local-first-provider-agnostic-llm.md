# ADR-0002: Local-first, provider-agnostic LLM

- **Status:** Accepted
- **Date:** 2026-06-22

## Context

The summarizer sends extracted content to an LLM for summarization. That content is
personal reading material, and the tool runs continuously, so two concerns dominate:
**privacy** (don't ship everything I read to a third party by default) and **cost**
(continuous summarization against a paid API adds up). At the same time, a stranger
who clones the repo may have no local GPU and may prefer a cloud endpoint — and Matt
himself may want a more capable cloud model for specific content.

## Decision

The LLM is accessed through a **provider abstraction** with a single method,
`summarize(text, prompt) -> Optional[str]`. Two providers ship:

- **`OllamaProvider`** — a local Ollama instance, the **default**.
- **`OpenAICompatibleProvider`** — any OpenAI-compatible endpoint (Claude API, OpenAI,
  etc.) via configurable `base_url` + `api_key`.

The provider is chosen by `llm.provider` in `config.yaml` and constructed by
`llm/factory.py`. Switching from local to cloud is a **config change, not a code
change**. New providers implement the base interface and register in the factory.

## Consequences

- **Good:** private and free by default (local Ollama); no content leaves the machine
  unless the user opts into a cloud provider.
- **Good:** the cloud path is first-class, not a hack — good for forkers without local
  inference and for Matt when a heavier model is warranted.
- **Good:** the abstraction is the seam for future providers without touching the
  pipeline.
- **Cost:** the lowest-common-denominator interface is just `summarize()`. Provider-
  specific features (streaming, tool use, structured output) are not exposed; adding
  them means widening the interface deliberately, for all providers.
- **Related:** `summarization` config (temperature, max tokens, input-char budget,
  timeout, retries, optional `system_prompt`) is provider-agnostic and applies to
  whichever provider is active.
