# Typed decisions API

PolderGraph exposes one provider-neutral Python function for asking typed
questions about text or structured state. Select a backend explicitly for each
call: `typesafe` (hosted Jev), `openai` (OpenAI Decisions API), or `laya`
(local model). Nothing is selected or called by default.

## Install

Jev and OpenAI use Python's standard HTTP library, so no additional package is
needed. Set the appropriate API key in the environment:

```bash
export TYPESAFE_API_KEY="..."  # Linux/macOS
# PowerShell: $env:TYPESAFE_API_KEY = "..."
```

```bash
export OPENAI_API_KEY="..."
# PowerShell: $env:OPENAI_API_KEY = "..."
```

Laya runs locally and has a separate optional dependency:

```bash
pip install 'poldergraph[decision-laya]'
```

The first local Laya call loads/downloads the checkpoint and can take time and
memory. The loaded model is cached in-process for later calls. Use `model=` to
select a Laya checkpoint; the default is `convaiinnovations/laya`.

## Example

```python
from poldergraph.decisions import choice, decide, predicate, score

state = {
    "request": "Please remember that this repo uses pnpm, not npm.",
    "source": "explicit user statement",
}
questions = {
    "action": choice(
        "action",
        "Should this become a durable user or project memory?",
        {
            "store": "The statement is explicit, durable, and useful later.",
            "reject": "It is temporary, ambiguous, or not a memory.",
        },
    ),
    "explicit": predicate(
        "explicit", "The user directly stated this preference or fact."
    ),
    "durability": score(
        "durability",
        "How likely is this fact to remain useful over future tasks?",
        ["one-off", "short-lived", "durable"],
    ),
}

# Choose one: "typesafe", "openai", or "laya".
result = decide(state, questions, provider="laya")
print(result["answers"]["action"]["choice"])
```

The function accepts helper objects or provider-neutral mappings. Choice
options map labels to descriptions; score levels are ordered low-to-high. The
returned mapping contains `provider`, `model`, `answers`, and `usage`. Choice
answers include per-option probabilities; predicate answers include a
probability; score answers include a numeric score and level distribution.
Choice/score probabilities use label-to-probability mappings across providers.

### Hosted provider details

```python
result = decide(state, questions, provider="typesafe", model="jev-latest")
result = decide(state, questions, provider="openai", model="gpt-6-luna")
```

Jev uses `POST /v1/systemone` with `state` and a named question map. OpenAI
uses `POST /v1/decisions` with `input` and a questions list. An optional
`endpoint=` argument can point to a compatible gateway or test server. The
default endpoints are `https://api.typesafe.ai` and
`https://api.openai.com/v1`.

## Privacy and safe use

The `state` is sent to the selected hosted provider when using Jev or OpenAI.
Choose `laya` to keep inference local, or do not call the API. PolderGraph does
not fall back from local to hosted inference and never silently chooses a
provider. Treat model probabilities as estimates, not truth. Calibrate any
threshold for the application and retain human review for uncertain or
high-impact decisions. A decision response does not write, update, or delete
PolderGraph memories by itself.

## Automatic PolderGraph integration

The shared query service and agent memory pipeline use the same API when a
provider is explicitly enabled in user or project configuration:

```toml
[decisions]
provider = "typesafe" # typesafe, openai, laya, or disabled
confidence_threshold = 0.9
timeout = 3.0
```

Use `POLDERGRAPH_DECISIONS__PROVIDER` to select the provider through the
environment. Hosted credentials remain in `TYPESAFE_API_KEY` or
`OPENAI_API_KEY`; they are never written to PolderGraph config. With decisions
enabled:

- Graph search asks typed questions to classify and route only ambiguous
  natural-language searches. Exact and high-coverage lexical hits keep the
  fast deterministic path. A confident lexical route skips vector search; a
  graph route adds bounded structural expansion.
- Agent context asks about candidate memory relevance in one batched request
  and removes only weak matches that are confidently irrelevant.
- Automatic user-preference capture remains bounded by local
  explicit-statement rules; candidates are evaluated together in one request,
  and a confident model rejection can veto a candidate but cannot invent or
  expand saved memories.
- CLI, MCP, and dashboard search use the shared routing and memory logic.

Uncertain results, missing credentials, timeouts, refusals, and provider errors
fall back to deterministic retrieval and memory behavior. Decisions are cached
for five minutes by content hash; raw prompts and memory text are not retained
in that cache. Hosted providers receive only the short query or candidate
excerpts needed for each decision. Enabling a hosted provider is an explicit
data-sharing choice; the default remains fully local.

## References

- [TypeSafe System One API](https://api.typesafe.ai/docs)
- [OpenAI Decisions API guide](https://developers.openai.com/api/docs/guides/decisions)
- [Convai Innovations Laya model](https://huggingface.co/convaiinnovations/laya)
- [Laya Python SDK](https://github.com/NandhaKishorM/laya)
