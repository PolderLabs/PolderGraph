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

## References

- [TypeSafe System One API](https://api.typesafe.ai/docs)
- [OpenAI Decisions API guide](https://developers.openai.com/api/docs/guides/decisions)
- [Convai Innovations Laya model](https://huggingface.co/convaiinnovations/laya)
- [Laya Python SDK](https://github.com/NandhaKishorM/laya)
