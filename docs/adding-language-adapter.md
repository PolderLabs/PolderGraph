# Adding a language adapter

PolderGraph indexes every tree-sitter-supported language at baseline (file + definition symbols). Strong adapters add semantic extraction: imports, calls, inheritance, type references and resolver integration.

## Steps

### 1. Add the language to the language maps

In `src/poldergraph/discovery/languages.py`:
- Add to `STRONG_LANGUAGES` if it gets a strong adapter
- Add extension mappings to `EXTENSION_MAP`
- Add grammar name to `GRAMMAR_NAMES`

### 2. Create the adapter

Create `src/poldergraph/parsing/languages/<language>_adapter.py`.

The adapter must implement:
- `language: str` — the language key
- `supports() -> bool` — always returns `True` when the grammar is available
- `parse(source: bytes, path: str) -> ParseResult` — extracts symbols, references, imports and exports

Use the tree-sitter engine helpers:
- `get_parser(grammar)` — load the grammar
- `node_text(source, node)` — extract node text
- `field_text(source, node, field)` — extract a named field
- `walk(node)` — depth-first iteration
- `children_of_type(node, *types)` — filter children by type

### Line numbers must be 1-based

Tree-sitter reports `node.start_point[0]` counted from **zero**, but every
public surface — stored spans, CLI output, JSON, the HTTP API, MCP payloads —
is 1-based, matching `grep -n` and every editor.

Adapters therefore copy the raw coordinate into `ParsedSymbol.start_line`, and
`ParseEngine.parse` converts the whole `ParseResult` to 1-based once, at the
single boundary every adapter returns through. Do **not** add `+ 1` inside an
adapter: that would double-convert.

Anything that slices a file by a stored span must subtract 1 to get a list
index, e.g. `lines[entity.start_line - 1 : entity.end_line]`.

A parser fixture should assert this against real text: the line named by
`start_line` must contain the symbol's name.

### 3. Register the adapter

In `src/poldergraph/parsing/languages/__init__.py`, add the import and register call:

```python
from .my_language_adapter import MyLanguageAdapter
register(MyLanguageAdapter, "my_language")
```

### 4. Add parser fixtures

In `tests/fixtures/parser_samples.py`, add a sample that exercises:
- Nested declarations
- Imports/re-exports
- Aliases
- Methods/calls
- Inheritance/interfaces

### 5. Run the tests

```bash
python -m pytest tests/unit/test_parsing_and_indexing.py -q
```

Every adapter must produce at least one symbol for its sample, have no duplicate qualified names, and not raise on parse errors.

## Design rules

- Extract facts from the syntax tree, never regex
- Every relationship has explicit provenance (`extracted`, `resolved`, `inferred`)
- Never silently choose an arbitrary same-name target for resolution
- A failed parse still indexes the file with whatever the grammar could extract
- Preserve ambiguous candidates rather than guessing