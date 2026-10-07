"""Canonical SQLite schema and ordered migrations.

Schema version and index format version are tracked separately: a schema change
that alters stored representations also bumps the format version so embeddings
and caches can be invalidated precisely.
"""

from __future__ import annotations

#: Bump when table/column layout changes.
SCHEMA_VERSION = 1

#: Bump when the semantics of stored representations change (entity IDs,
#: semantic text construction, edge identity) so derived data is rebuilt.
INDEX_FORMAT_VERSION = 1

#: Ordered migrations. Each entry is (target_version, sql_statements).
MIGRATIONS: list[tuple[int, list[str]]] = [
    (
        1,
        [
            """
            CREATE TABLE IF NOT EXISTS meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS roots (
                root_id     TEXT PRIMARY KEY,
                path        TEXT NOT NULL,
                name        TEXT NOT NULL,
                is_primary  INTEGER NOT NULL DEFAULT 0,
                vcs_branch  TEXT,
                vcs_head    TEXT,
                created_at  INTEGER NOT NULL,
                updated_at  INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS entities (
                id             TEXT PRIMARY KEY,
                root_id        TEXT NOT NULL,
                kind           TEXT NOT NULL,
                language       TEXT,
                name           TEXT NOT NULL,
                qualified_name TEXT,
                path           TEXT,
                parent_id      TEXT,
                start_byte     INTEGER,
                end_byte       INTEGER,
                start_line     INTEGER,
                end_line       INTEGER,
                visibility     TEXT,
                signature      TEXT,
                docstring      TEXT,
                content_hash   TEXT,
                semantic_hash  TEXT,
                is_generated   INTEGER NOT NULL DEFAULT 0,
                is_external    INTEGER NOT NULL DEFAULT 0,
                metadata_json  TEXT NOT NULL DEFAULT '{}',
                created_at     INTEGER NOT NULL,
                updated_at     INTEGER NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_entities_root ON entities(root_id)",
            "CREATE INDEX IF NOT EXISTS idx_entities_kind ON entities(kind)",
            "CREATE INDEX IF NOT EXISTS idx_entities_lang ON entities(language)",
            "CREATE INDEX IF NOT EXISTS idx_entities_parent ON entities(parent_id)",
            "CREATE INDEX IF NOT EXISTS idx_entities_path ON entities(root_id, path)",
            "CREATE INDEX IF NOT EXISTS idx_entities_qname ON entities(qualified_name)",
            "CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name)",
            "CREATE INDEX IF NOT EXISTS idx_entities_semantic_hash ON entities(semantic_hash)",
            """
            CREATE TABLE IF NOT EXISTS edges (
                id              TEXT PRIMARY KEY,
                source_id       TEXT NOT NULL,
                target_id       TEXT NOT NULL,
                type            TEXT NOT NULL,
                provenance      TEXT NOT NULL,
                confidence      REAL NOT NULL,
                resolver        TEXT,
                source_path     TEXT,
                source_line     INTEGER,
                source_col      INTEGER,
                metadata_json   TEXT NOT NULL DEFAULT '{}',
                created_at      INTEGER NOT NULL,
                updated_at      INTEGER NOT NULL,
                UNIQUE(source_id, target_id, type, provenance, resolver)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)",
            "CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)",
            "CREATE INDEX IF NOT EXISTS idx_edges_type ON edges(type)",
            "CREATE INDEX IF NOT EXISTS idx_edges_provenance ON edges(provenance)",
            """
            CREATE TABLE IF NOT EXISTS embeddings (
                embedding_id   TEXT PRIMARY KEY,
                entity_id      TEXT,
                chunk_id       TEXT,
                modality       TEXT NOT NULL,
                model_id       TEXT NOT NULL,
                model_revision TEXT NOT NULL,
                dimensions     INTEGER NOT NULL,
                task_type      TEXT NOT NULL,
                input_hash     TEXT NOT NULL,
                norm           REAL,
                created_at     INTEGER NOT NULL,
                FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_embeddings_entity ON embeddings(entity_id)",
            "CREATE INDEX IF NOT EXISTS idx_embeddings_hash ON embeddings(input_hash)",
            "CREATE INDEX IF NOT EXISTS idx_embeddings_lookup ON embeddings(model_id, dimensions, task_type)",
            """
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id     TEXT PRIMARY KEY,
                entity_id    TEXT NOT NULL,
                ordinal      INTEGER NOT NULL,
                modality     TEXT NOT NULL,
                content      TEXT,
                content_hash TEXT NOT NULL,
                token_count  INTEGER,
                start_line   INTEGER,
                end_line     INTEGER,
                start_time   REAL,
                end_time     REAL,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                FOREIGN KEY(entity_id) REFERENCES entities(id) ON DELETE CASCADE
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_chunks_entity ON chunks(entity_id, ordinal)",
            """
            CREATE TABLE IF NOT EXISTS files (
                root_id        TEXT NOT NULL,
                path           TEXT NOT NULL,
                size           INTEGER NOT NULL,
                mtime_ns       INTEGER NOT NULL,
                content_hash   TEXT NOT NULL,
                language       TEXT,
                parse_status   TEXT NOT NULL,
                is_generated   INTEGER NOT NULL DEFAULT 0,
                is_media       INTEGER NOT NULL DEFAULT 0,
                last_indexed_at INTEGER NOT NULL,
                PRIMARY KEY(root_id, path)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_files_hash ON files(content_hash)",
            """
            CREATE TABLE IF NOT EXISTS communities (
                community_id TEXT NOT NULL,
                algorithm     TEXT NOT NULL,
                mode          TEXT NOT NULL,
                resolution    REAL NOT NULL,
                label         TEXT,
                size          INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT NOT NULL DEFAULT '{}',
                computed_at   INTEGER NOT NULL,
                PRIMARY KEY(community_id, algorithm, mode)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS community_members (
                community_id TEXT NOT NULL,
                algorithm    TEXT NOT NULL,
                mode         TEXT NOT NULL,
                entity_id    TEXT NOT NULL,
                weight       REAL NOT NULL DEFAULT 1.0,
                PRIMARY KEY(community_id, algorithm, mode, entity_id)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_community_members_entity ON community_members(entity_id)",
            """
            CREATE TABLE IF NOT EXISTS metrics (
                entity_id  TEXT NOT NULL,
                metric     TEXT NOT NULL,
                value      REAL NOT NULL,
                computed_at INTEGER NOT NULL,
                PRIMARY KEY(entity_id, metric)
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_metrics_metric ON metrics(metric, value DESC)",
            """
            CREATE TABLE IF NOT EXISTS unresolved_refs (
                id          TEXT PRIMARY KEY,
                source_id   TEXT NOT NULL,
                name        TEXT NOT NULL,
                path        TEXT,
                line        INTEGER,
                edge_type   TEXT NOT NULL,
                resolver    TEXT,
                candidates  TEXT NOT NULL DEFAULT '[]',
                root_id     TEXT,
                FOREIGN KEY(source_id) REFERENCES entities(id) ON DELETE CASCADE
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_unresolved_source ON unresolved_refs(source_id)",
            """
            CREATE VIRTUAL TABLE IF NOT EXISTS entity_fts USING fts5(
                entity_id UNINDEXED,
                name,
                qualified_name,
                path,
                signature,
                docstring,
                semantic_text,
                tokenize = 'unicode61 remove_diacritics 2'
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS change_events (
                event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                kind        TEXT NOT NULL,
                entity_ids  TEXT NOT NULL DEFAULT '[]',
                created_at  INTEGER NOT NULL
            )
            """,
            "CREATE INDEX IF NOT EXISTS idx_change_events_created ON change_events(created_at)",
        ],
    ),
]