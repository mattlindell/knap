# Context

The single-context anchor for Knap. Read this before exploring the
codebase; it defines what the project is, the vocabulary it uses, and where it's
headed. Point-in-time decisions live in [`docs/adr/`](docs/adr/); the mechanical
architecture lives in [`docs/architecture.md`](docs/architecture.md).

## Purpose

Knap is a personal, always-on background service that watches the Obsidian Web
Clipper's output folder and turns raw web clippings (articles and videos) into
AI-summarized, Dataview-linkable notes — degrading gracefully to a "needs-review"
note rather than hallucinating when extraction fails.

The name is a nod to *knapping*, the craft of striking obsidian to flake away what
isn't needed and leave a sharp edge. It is the project's name only — the glossary
below, not the metaphor, governs the vocabulary used in code and output.

**Primary user:** a single person (Matt), one vault, local-first (Ollama by
default). **Secondary audience:** anyone who clones the public repo. The project is
personal in its *configuration*, not in its *code*.

## Reusability boundary

General-purpose by default; personalization is confined to two places:

- **`config.yaml`** — paths, LLM provider/model, extraction and summarization knobs.
- **`templates/`** — the output note format (frontmatter, sections, Dataview query).

The core pipeline code (extractors, classifier, quality gate, LLM providers, factory)
carries **no assumptions about Matt's specific vault**. A stranger should be able to
`cp config.example.yaml config.yaml`, edit the paths and LLM choice, and run.

> The templates are currently the weakest part of this boundary — they are more
> coupled to Matt's vault (specific frontmatter, "My Notes" prompts, a
> Projects/Domains Dataview query) than they should be. Making them cleanly
> replaceable is near-future work.

## Glossary

Use these terms exactly. When output names one of these concepts — an issue title, a
prompt, a test name, a refactor proposal — use the canonical term, not a synonym.

| Concept | Canonical term | Avoid |
| --- | --- | --- |
| The raw `.md` file the Web Clipper drops into the watched folder | **Clipping** | "clip", "note", "article" |
| The AI-summarized output file written to `Processed/` | **Processed note** | "summary file", "output" |
| Getting usable text out of a source | **Extraction** | "scraping" (scraping is *one* extraction technique — BeautifulSoup scrapes; yt-dlp pulls subtitles) |
| The minimum-length check that runs before the LLM | **Quality gate** | "validation", "filter" |
| The LLM backend behind the provider abstraction | **Provider** | "model", "backend", "engine" |
| Never-raise failure handling: return empty/`None`, keep running | **Graceful degradation** | "fallback" (a fallback is a *specific* mechanism, e.g. video subtitles → description) |
| The current `VIDEO`/`ARTICLE` enum that routes extraction | **ContentType** | — |
| A named bundle of `{matcher, extractor, prompt, template}` selected per clipping | **Content Profile** | "handler", "rule", "type" |

### Content Profile (forward-looking)

The most important term that does **not yet exist in code**. Today, the classifier
makes one binary `ContentType` decision (`VIDEO` vs `ARTICLE`) and that single value
drives extractor selection; prompt and template are fixed. A **Content Profile**
generalizes this: a URL/content matcher selects a bundle of behavior —

- **matcher** — e.g. a URL regex (`github.com/...`)
- **extractor** — *optional*; inherits the default classifier-driven extractor unless overridden
- **prompt** — what the LLM is asked to do for this kind of content
- **template** — how the processed note is rendered

The built-in `VIDEO` and `ARTICLE` `ContentType`s become the two default profiles.
GitHub is the motivating custom profile (repos are neither "video" nor generic
"article" — they have a language, activity, and README structure worth prompting
for specifically). See [ADR-0004](docs/adr/0004-content-profile-routing.md).

## Current state (shipped)

The v2 pipeline is fully implemented and running:

- **Watcher** — `clipping_watcher.py`, watchdog-based, orchestrates the pipeline.
- **Classifier** — regex URL match → `ContentType.VIDEO` / `ARTICLE`.
- **Extractors** — video (yt-dlp: manual subs → auto captions → description), article
  (BeautifulSoup), behind a `ContentResult` exchange dataclass.
- **Quality gate** — configurable minimum content length (default 100 chars).
- **LLM providers** — Ollama (default) and OpenAI-compatible, via a factory.
- **Templates** — `summary.md.j2` and `failed_extraction.md.j2` (Jinja2).
- **Config** — YAML with deep-merged defaults. Has grown past the original v2 spec: a
  `summarization` block now tunes temperature, max tokens, input-char budget, request
  timeout, retries, and an optional `system_prompt` override (tuned for a 32k-context
  model).

Error handling is **graceful degradation** end to end — see
[ADR-0001](docs/adr/0001-graceful-degradation.md).

## Near-future direction

Three features are actively on the horizon. `CONTEXT.md` and the ADRs establish the
seams they need:

1. **Replaceable templates** — decouple the output format from Matt's vault so a
   forker can swap it cleanly. Tightens the reusability boundary above.
2. **Local audio transcription (Whisper)** — via `whisper.cpp` running locally on the
   processing PC. Note: this supersedes the v2 design's "when the Jetson is running"
   assumption — it does **not** need a server; whisper.cpp runs well on most PCs.
3. **Content Profiles** — URL-pattern routing of prompt + template (+ optional
   extractor), starting with GitHub. See [ADR-0004](docs/adr/0004-content-profile-routing.md).

## Decisions

| ADR | Decision | Status |
| --- | --- | --- |
| [0001](docs/adr/0001-graceful-degradation.md) | Graceful degradation everywhere — components never raise | Accepted |
| [0002](docs/adr/0002-local-first-provider-agnostic-llm.md) | Local-first, provider-agnostic LLM | Accepted |
| [0003](docs/adr/0003-personalization-boundary.md) | Personalization confined to `config.yaml` + `templates/` | Accepted |
| [0004](docs/adr/0004-content-profile-routing.md) | Content Profile as the routing model | Accepted (not yet implemented) |

If your work contradicts an ADR, surface it explicitly (e.g. "Contradicts ADR-0004,
but worth reopening because…") rather than silently overriding it.
