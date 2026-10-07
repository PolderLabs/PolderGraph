# Privacy and security

## Network policy

PolderGraph performs no telemetry and no remote inference by default. The explicit policy:

```toml
[privacy]
allow_model_downloads = true
allow_remote_embedding = false
telemetry = false
```

Only model/package downloads are allowed by default. Indexed source content, embeddings, metadata and search queries never leave the machine under default configuration.

## Threat model

PolderGraph indexes untrusted repositories. Inputs are treated as hostile.

### Path traversal protection

Every filesystem access goes through `safe_join`, which:
- Rejects absolute paths
- Rejects `..` traversal
- Rejects null bytes
- Resolves symlinks and rejects escapes outside the configured root
- The dashboard source endpoint only serves files inside configured roots

### Parser execution

- Tree-sitter parsers are in-process trusted libraries, not external processes
- External media helpers (ffprobe, ffmpeg) are spawned with `subprocess.run` using argv arrays, never shell strings
- All subprocess calls have explicit timeouts
- File size limits prevent decompression bombs

### Dashboard security

- Default host is `127.0.0.1` (loopback only)
- Binding to non-loopback requires an explicit `--host` flag with a warning
- All labels, paths and signatures are escaped as React text nodes; `dangerouslySetInnerHTML` is never used
- The source endpoint rejects any path outside configured roots
- API responses use the documented JSON envelope with `api_version`

### Subprocess safety

- Never build shell strings from repository content
- Pass argv arrays and enforce timeouts for all subprocess calls
- Validate all user input before passing to parsers or file operations

### Network

- Indexed content is never sent remotely under default configuration
- Remote embedding is opt-in only via explicit configuration
- Model downloads are the only network operation allowed by default

## Model cache

The embedding model cache lives at `.poldergraph/cache/model/` and is not committed to version control. The `.poldergraph/` directory is added to `.gitignore` during `poldergraph init`.

## Data at rest

- All indexed data is stored in a single SQLite database (`.poldergraph/index.sqlite3`)
- Vectors are stored as float32 blobs in the database
- No separate database server or external service is required
- The database can be backed up by copying the `.poldergraph/` directory