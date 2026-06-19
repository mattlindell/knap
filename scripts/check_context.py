"""Probe whether the configured LLM actually honors a large context window.

Ollama silently caps context at ``num_ctx`` (default 2048 tokens) unless the
model's Modelfile or request raises it. Routing through a LiteLLM proxy hides
this -- the request succeeds, the model just never sees the start of a long
input. This script sends a long payload with a unique sentinel at the very
start and very end and asks the model to echo both. If the leading sentinel
comes back, the full input fit in context.

Usage:
    .venv/Scripts/python.exe scripts/check_context.py [approx_input_tokens]

Defaults to ~8000 tokens of filler, well above the 2048 default cap but inside
a real 32k window.
"""

import sys
from pathlib import Path

# Allow running as a standalone script from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import load_config  # noqa: E402
from llm.factory import create_provider  # noqa: E402

START = "SENTINEL_ALPHA_7f3c"
END = "SENTINEL_OMEGA_9b21"


def build_payload(approx_tokens: int) -> str:
    # ~4 chars per token is a rough but safe estimate for English filler.
    target_chars = approx_tokens * 4
    filler_lines = []
    i = 0
    size = 0
    while size < target_chars:
        line = f"Filler line {i:06d}: the quick brown fox jumps over the lazy dog.\n"
        filler_lines.append(line)
        size += len(line)
        i += 1
    return f"{START}\n" + "".join(filler_lines) + f"{END}\n"


def main() -> int:
    approx_tokens = int(sys.argv[1]) if len(sys.argv) > 1 else 8000

    config = load_config()
    provider = create_provider(config["llm"])
    summ = config.get("summarization", {})

    body = build_payload(approx_tokens)
    prompt = (
        "The text between the markers below begins with a START sentinel and "
        "ends with an END sentinel. Reply with ONLY those two sentinel tokens, "
        "the first one then the second one, separated by a space. Do not add "
        "anything else.\n\n" + body
    )

    print(f"Model: {config['llm']['model']}")
    print(f"Endpoint: {config['llm']['base_url']}")
    print(f"Sent ~{approx_tokens} tokens ({len(body)} chars).")
    print("Waiting for response...\n")

    response = provider.summarize(
        prompt,
        system="You are a precise echo tool. Follow the instructions exactly.",
        temperature=0.0,
        max_tokens=64,
        timeout=float(summ.get("request_timeout", 300)),
        max_retries=0,
    )

    if response is None:
        print("FAILED: no response from endpoint (connection/timeout error).")
        return 2

    print(f"Raw response: {response!r}\n")
    saw_start = START in response
    saw_end = END in response

    if saw_start and saw_end:
        print(f"PASS: both sentinels returned -> context holds >= ~{approx_tokens} tokens.")
        return 0
    if saw_end and not saw_start:
        print(
            "FAIL: only the END sentinel returned. The start of the input was "
            "truncated -- num_ctx is smaller than the input. Raise num_ctx in "
            "the Ollama Modelfile (PARAMETER num_ctx 32768) or the proxy config."
        )
        return 1
    print(
        "INCONCLUSIVE: model did not echo cleanly. Re-run; if it persists the "
        "model may just be ignoring the instruction rather than truncating."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
