# Configuration reference

## Configuration precedence

Lowest to highest:
1. Built-in defaults
2. User config (`~/.config/poldergraph/config.toml`)
3. Workspace config (`.poldergraph/config.toml`)
4. Environment variables (`POLDERGRAPH_` prefix, `__` nesting)
5. CLI flags

`poldergraph config show --effective` prints merged values and origins.

## Default configuration

```toml
version = 1

[index]
dimensions = 256
include_media = true
include_generated = false
follow_symlinks = false
max_file_bytes = 5000000

[embedding]
backend = "native"
model = "google/embeddinggemma-2"
batch_size = 0
device = "auto"
normalize = true
ollama_host = "http://127.0.0.1:11434"
ollama_model = "embeddinggemma"
api_provider = "openai"
api_endpoint = ""
api_model = ""
api_timeout = 30.0
api_retries = 2
api_batch_size = 64
max_tokens = 2048

[semantic_edges]
enabled = true
top_k = 12
mutual_preferred = true
max_degree = 8
minimum_similarity = "auto"

[graph]
community_algorithm = "leiden"
compute_structural_communities = true
compute_hybrid_communities = true

[retrieval]
semantic_candidates = 40
lexical_candidates = 40
graph_hops = 2
max_graph_candidates = 150
default_context_tokens = 6000

[ui]
host = "127.0.0.1"
port = 7432
open_browser = true

[privacy]
allow_model_downloads = true
allow_remote_embedding = false
allow_remote_decisions = false
telemetry = false

[decisions]
provider = "disabled"
remote_providers = []
model = ""
endpoint = ""
timeout = 3.0
confidence_threshold = 0.9
```

## Environment variables

Use the `POLDERGRAPH_` prefix with double underscores for nesting:

```bash
POLDERGRAPH_EMBEDDING__DEVICE=cuda
POLDERGRAPH_INDEX__DIMENSIONS=512
POLDERGRAPH_UI__PORT=8080
POLDERGRAPH_DECISIONS__PROVIDER=typesafe
```

## Configuration sections

### `[index]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `dimensions` | int | 256 | Embedding vector width (1–3072); native Gemma/Ollama support 128, 256, 512, 768 |
| `include_media` | bool | true | Index image/audio/video files |
| `include_generated` | bool | false | Index generated/vendor files |
| `follow_symlinks` | bool | false | Follow symbolic links during discovery |
| `max_file_bytes` | int | 5000000 | Maximum file size to index |

### `[embedding]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `backend` | string | "native" | Embedding backend: "native", "ollama", "api", "none" |
| `model` | string | "google/embeddinggemma-2" | Model identifier |
| `batch_size` | int | 0 | Embedding batch size (0 = auto) |
| `device` | string | "auto" | Compute device: "auto", "cpu", "cuda", "mps" |
| `normalize` | bool | true | L2-normalize vectors |
| `ollama_host` | string | "http://127.0.0.1:11434" | Ollama server URL |
| `api_endpoint` | string | provider default | Optional API base URL; custom endpoints must come from trusted config |
| `api_model` | string | provider default | Remote embedding model |
| `api_provider` | string | "openai" | API provider: "openai", "voyage", or "cohere" |
| `api_timeout` | float | 30.0 | Remote request timeout in seconds |
| `api_retries` | int | 2 | Bounded retries for transient network, HTTP 429 and server errors (0–5) |
| `api_batch_size` | int | 64 | Maximum inputs per API request (1–128) |
| `max_tokens` | int | 2048 | Maximum sequence length |

For OpenAI set `backend = "api"` and provide `OPENAI_API_KEY`. To use Voyage,
set `api_provider = "voyage"` and provide `VOYAGE_API_KEY`; its API uses the
provider-specific `input_type` and `output_dimension` fields. In both cases,
remote transmission remains disabled until `allow_remote_embedding = true` is
set in trusted user config or the host environment. Workspace config alone
cannot authorize egress. Do not put API keys in TOML.
To use Cohere's native v2 embed endpoint, set `api_provider = "cohere"` and
provide `COHERE_API_KEY`. The `embed-v4.0` model supports 256, 512, 1024, or
1536 output dimensions. PolderGraph maps query and document tasks to Cohere's
`search_query` and `search_document` input types.
Transient rate limits and server failures retry with bounded exponential backoff
and jitter, honoring numeric `Retry-After` values.
Changing the active provider, model, revision, dimensions, normalization, or task
policy causes `poldergraph update` and `pg_update` to re-index the corpus for
that vector space. Previously stored vectors remain isolated and can be reused
when switching back to an exact prior configuration.

### `[semantic_edges]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `enabled` | bool | true | Materialize semantic graph edges |
| `top_k` | int | 12 | Nearest neighbours per entity |
| `mutual_preferred` | bool | true | Prefer mutual-nearest-neighbour edges |
| `max_degree` | int | 8 | Maximum semantic degree per entity |
| `minimum_similarity` | float/"auto" | "auto" | Threshold; "auto" derives from distribution |

### `[graph]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `community_algorithm` | string | "leiden" | Community detection: "leiden", "louvain" |
| `compute_structural_communities` | bool | true | Compute structural community view |
| `compute_hybrid_communities` | bool | true | Compute hybrid community view |
| `compute_betweenness` | bool | false | Compute betweenness centrality |

### `[retrieval]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `semantic_candidates` | int | 40 | Semantic channel candidate limit |
| `lexical_candidates` | int | 40 | Lexical channel candidate limit |
| `graph_hops` | int | 2 | Structural expansion hops |
| `max_graph_candidates` | int | 150 | Structural expansion cap |
| `default_context_tokens` | int | 6000 | Default context budget |

### `[ui]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `host` | string | "127.0.0.1" | Dashboard bind address |
| `port` | int | 7432 | Dashboard port |
| `open_browser` | bool | true | Open browser on start |

### `[privacy]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `allow_model_downloads` | bool | true | Allow downloading the embedding model |
| `allow_remote_embedding` | bool | false | Allow remote embedding endpoints (requires trusted user config or environment) |
| `allow_remote_decisions` | bool | false | Trusted user-level consent for hosted decision providers; workspace config cannot grant consent |
| `telemetry` | bool | false | Send telemetry (always false by default) |

### `[decisions]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `provider` | string | `disabled` | `disabled`, `typesafe`, `openai`, or `laya`; workspace may select a provider but cannot authorize hosted calls |
| `remote_providers` | string[] | `[]` | Trusted user-level allowlist of hosted providers (`typesafe`, `openai`) that may receive decision data |
| `model` | string | empty | Optional model override |
| `endpoint` | string | empty | Optional compatible API endpoint override; custom hosted endpoints must come from trusted user config or the environment |
| `timeout` | float | 3.0 | Hosted request timeout or local Laya process deadline in seconds |
| `confidence_threshold` | float | 0.9 | Minimum probability for model decisions; uncertain answers keep the deterministic result |

Hosted providers read credentials from `TYPESAFE_API_KEY` or `OPENAI_API_KEY`.
`laya` uses the optional `poldergraph[decision-laya]` extra and runs locally in
a supervised process with a hard deadline. Its model stays warm for up to five
idle minutes and is shut down when the host process exits. Disable model
downloads with `[privacy].allow_model_downloads = false`; this also configures
the worker's Hugging Face clients for offline mode.
No provider is enabled by default. When enabled, PolderGraph sends only the
query or candidate memory text needed for a decision; hosted requests can
contain repository queries and excerpts from private memories. Search routing
uses typed decisions for ambiguous natural-language queries after exact and
high-confidence lexical matches. Memory automation drops only confidently
irrelevant context and confidently unsuitable auto-capture candidates;
uncertain answers and provider failures keep the existing local behavior.
