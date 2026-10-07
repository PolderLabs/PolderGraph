# Adding an embedding/vector backend

PolderGraph's embedding and vector storage layers are behind replaceable interfaces, so new backends can be added without changing the indexing or retrieval pipeline.

## Embedding backend

Implement the `EmbeddingBackend` protocol defined in `src/poldergraph/embedding/protocol.py`:

```python
class EmbeddingBackend(Protocol):
    def capabilities(self) -> set[str]: ...
    def model_info(self) -> ModelInfo: ...
    def embed_texts(self, items: list[str], *, task: str, dimensions: int) -> list[list[float]]: ...
    def embed_images(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: ...
    def embed_audio(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: ...
    def embed_video(self, requests: list[MediaRequest], *, dimensions: int) -> list[list[float]]: ...
```

### Key requirements

- Return vectors in the requested `dimensions` (use Matryoshka truncation if the model outputs more)
- L2-normalize vectors when `normalize=True`
- Use the correct task prompt for query vs corpus embeddings
- Record `model_id` and `model_revision` so stale vectors can be invalidated
- Never fail silently: raise `BackendUnavailableError` with a remediation message

### Registration

In `src/poldergraph/embedding/gemma.py::create_backend`, add a case for your backend name:

```python
if backend_name == "my_backend":
    from .my_backend import MyBackend
    return MyBackend(...)
```

### Testing

- Verify vector dimensions match the requested dimensions
- Verify normalization (unit norm within tolerance)
- Verify query and corpus embeddings use different task prompts
- Verify `model_info()` returns consistent identity

## Vector backend

Implement the `VectorStore` protocol defined in `src/poldergraph/storage/vectors.py`:

```python
class VectorStore(Protocol):
    def upsert(self, records: list[VectorRecord]) -> None: ...
    def delete(self, ids: list[str]) -> None: ...
    def search(self, vector: list[float], *, top_k: int, filters: dict | None) -> list[VectorHit]: ...
    def available(self) -> bool: ...
```

### Key requirements

- Vectors are stored normalized; search uses cosine similarity
- `search` returns results sorted by similarity descending
- Each hit includes `entity_id` and `embedding_id`
- Support `modality` filter if the backend supports multimodal embeddings

### Registration

In `create_vector_store`, add your backend as a fallback:

```python
def create_vector_store(...):
    store = SQLiteVecStore(...)
    if store.available():
        return store
    return MyCustomStore(...)
```

### Testing

- Verify `upsert` + `search` round-trip
- Verify cosine similarity matches the mathematical expectation
- Verify `delete` removes entries
- Verify both backends agree on the same query