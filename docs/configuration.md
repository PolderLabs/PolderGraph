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
telemetry = false
```

## Environment variables

Use the `POLDERGRAPH_` prefix with double underscores for nesting:

```bash
POLDERGRAPH_EMBEDDING__DEVICE=cuda
POLDERGRAPH_INDEX__DIMENSIONS=512
POLDERGRAPH_UI__PORT=8080
```

## Configuration sections

### `[index]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `dimensions` | int | 256 | Embedding dimensions (128, 256, 512, 768) |
| `include_media` | bool | true | Index image/audio/video files |
| `include_generated` | bool | false | Index generated/vendor files |
| `follow_symlinks` | bool | false | Follow symbolic links during discovery |
| `max_file_bytes` | int | 5000000 | Maximum file size to index |

### `[embedding]`

| Key | Type | Default | Description |
|-----|------|---------|-------------|
| `backend` | string | "native" | Embedding backend: "native", "ollama", "none" |
| `model` | string | "google/embeddinggemma-2" | Model identifier |
| `batch_size` | int | 0 | Embedding batch size (0 = auto) |
| `device` | string | "auto" | Compute device: "auto", "cpu", "cuda", "mps" |
| `normalize` | bool | true | L2-normalize vectors |
| `ollama_host` | string | "http://127.0.0.1:11434" | Ollama server URL |
| `max_tokens` | int | 2048 | Maximum sequence length |

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
| `allow_remote_embedding` | bool | false | Allow remote embedding endpoints |
| `telemetry` | bool | false | Send telemetry (always false by default) |