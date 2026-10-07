#!/usr/bin/env python3
"""Measure local agent-memory retrieval quality and latency on a fixed coding set.

This is a retrieval benchmark, not an LLM task-success benchmark. It uses the
production local embedding backend and compares against a no-memory baseline.
"""

from __future__ import annotations

import argparse
import json
import statistics
import tempfile
import time
from pathlib import Path
from typing import Any

from poldergraph.config.models import EMBEDDING_MODEL
from poldergraph.embedding.gemma import NativeGemmaBackend
from poldergraph.memory import MemoryStore
from poldergraph.retrieval.context import estimate_tokens

CASES: list[dict[str, Any]] = [
    {
        "content": "The package supports Python 3.11 and newer; CI covers 3.11, 3.12, and 3.13.",
        "scope": "project",
        "kind": "fact",
        "tags": ["python", "compatibility"],
        "query": "What is the oldest Python version this repo supports?",
    },
    {
        "content": "Use the versioned JSON envelope for every CLI and MCP response.",
        "scope": "project",
        "kind": "decision",
        "tags": ["api", "json", "mcp"],
        "query": "How should new tool responses be formatted?",
    },
    {
        "content": "PolderGraph stores code indexes and agent memories on the local machine; it does not send source to a hosted service.",
        "scope": "project",
        "kind": "decision",
        "tags": ["privacy", "local-first"],
        "query": "Does this application upload repository source anywhere?",
    },
    {
        "content": "The central agent memory database uses SQLite FTS5 plus local vectors for hybrid retrieval.",
        "scope": "project",
        "kind": "decision",
        "tags": ["memory", "sqlite", "vectors"],
        "query": "Which search indexes power persistent agent memory?",
    },
    {
        "content": "Run the Python test suite with pytest; fast tests do not require downloading the embedding model.",
        "scope": "project",
        "kind": "workflow",
        "tags": ["tests", "pytest"],
        "query": "What command runs the unit and integration checks?",
    },
    {
        "content": "Build the dashboard with pnpm --dir web build; the wheel bundles web/dist.",
        "scope": "project",
        "kind": "workflow",
        "tags": ["dashboard", "build", "release"],
        "query": "How does the web UI get packaged into Python distributions?",
    },
    {
        "content": "The MCP server exposes project memory through pg_memory_search and pg_memory_add.",
        "scope": "project",
        "kind": "fact",
        "tags": ["mcp", "memory"],
        "query": "Which MCP tools let an agent recall and save long-term notes?",
    },
    {
        "content": "Project memories are keyed by the resolved absolute workspace root; user preferences are visible across projects.",
        "scope": "project",
        "kind": "decision",
        "tags": ["scope", "memory", "isolation"],
        "query": "How does memory separate repository details from global user preferences?",
    },
    {
        "content": "The default local text embedding model is google/embeddinggemma-2 with 256 dimensions.",
        "scope": "project",
        "kind": "fact",
        "tags": ["embedding", "model"],
        "query": "What model and vector size are used for default text search?",
    },
    {
        "content": "After changing source files, refresh the index with poldergraph update --quiet.",
        "scope": "project",
        "kind": "workflow",
        "tags": ["index", "update"],
        "query": "How do I rebuild the code graph after implementation changes?",
    },
    {
        "content": "The OMP extension adds repository context before each agent task and refreshes after edit and write tools.",
        "scope": "project",
        "kind": "fact",
        "tags": ["omp", "automation"],
        "query": "When does the Oh My Pi plugin inject and refresh codebase knowledge?",
    },
    {
        "content": "Never save passwords, API tokens, private keys, or transient task details in agent memory.",
        "scope": "project",
        "kind": "decision",
        "tags": ["memory", "privacy", "secrets"],
        "query": "Which information is explicitly forbidden from persistent notes?",
    },
    {
        "content": "The dashboard uses Sigma.js v4 alpha for interactive code graph visualization.",
        "scope": "project",
        "kind": "fact",
        "tags": ["frontend", "graph", "sigma"],
        "query": "What JavaScript graph renderer powers the frontend?",
    },
    {
        "content": "MCP tools return a stable versioned JSON envelope and must not bypass the shared retrieval service.",
        "scope": "project",
        "kind": "decision",
        "tags": ["mcp", "architecture"],
        "query": "What API contract and service design should new MCP tools follow?",
    },
    {
        "content": "Create release distributions with python -m build and attach dist/* to the GitHub release.",
        "scope": "project",
        "kind": "workflow",
        "tags": ["release", "wheel", "sdist"],
        "query": "How should installers get the wheel and source archive for a release?",
    },
    {
        "content": "The user prefers concise explanations with concrete examples when they clarify a decision.",
        "scope": "user",
        "kind": "preference",
        "tags": ["style", "communication"],
        "query": "What response style does the user prefer?",
    },
    {
        "content": "The user wants coding agents to use memory automatically and avoid asking for routine guidance.",
        "scope": "user",
        "kind": "preference",
        "tags": ["agent", "autonomy"],
        "query": "How should agents handle ordinary implementation choices?",
    },
    {
        "content": "The user prefers local-first tools that keep source code and personal data on their machine.",
        "scope": "user",
        "kind": "preference",
        "tags": ["privacy", "local-first"],
        "query": "What privacy model does the user favor in developer tools?",
    },
    {
        "content": "The user expects complete implementation, verification, and delivery rather than stopping at a partial draft.",
        "scope": "user",
        "kind": "preference",
        "tags": ["workflow", "delivery"],
        "query": "What level of completion should an agent aim for?",
    },
    {
        "content": "The CLI is built with Typer and shared input validation errors use PolderGraphError subclasses.",
        "scope": "project",
        "kind": "fact",
        "tags": ["cli", "python", "errors"],
        "query": "Which framework and error type pattern are used for commands?",
    },
]

NEGATIVE_QUERIES = [
    "How do I configure a Redis cluster for production caching?",
    "Which Kubernetes ingress controller terminates TLS?",
    "What is the database sharding strategy for PostgreSQL replicas?",
    "How does the mobile app refresh push notifications?",
    "Which payment provider handles subscription invoices?",
    "What encryption cipher is used for S3 object storage?",
    "How many web workers run in the cloud deployment?",
    "Where are customer analytics dashboards hosted?",
]


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round((len(ordered) - 1) * fraction))]


def run_benchmark(*, device: str = "auto", top_k: int = 5) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="poldergraph-memory-bench-") as temp:
        root = Path(temp) / "repo"
        root.mkdir()
        store = MemoryStore(root, Path(temp) / "memory.sqlite3")
        for case in CASES:
            store.add(case["content"], scope=case["scope"], kind=case["kind"], tags=case["tags"])

        backend = NativeGemmaBackend(model_id=EMBEDDING_MODEL, dimensions=256, device=device)
        # Warm the local model, backfill all vectors, and exclude startup from warm query latency.
        cold_started = time.perf_counter()
        store.search(CASES[0]["query"], limit=top_k, backend=backend)
        cold_ms = (time.perf_counter() - cold_started) * 1000

        hit_ranks: list[int | None] = []
        missed_queries: list[str] = []
        latencies: list[float] = []
        query_tokens: list[int] = []
        gold_similarities: list[float] = []
        for case in CASES:
            started = time.perf_counter()
            results = store.search(case["query"], limit=top_k, backend=backend)
            latencies.append((time.perf_counter() - started) * 1000)
            ids = [result["id"] for result in results]
            expected = next(
                item["id"]
                for item in store.list(scope=case["scope"], limit=100)
                if item["content"] == case["content"]
            )
            hit_ranks.append(ids.index(expected) + 1 if expected in ids else None)
            if expected not in ids:
                missed_queries.append(case["query"])
            gold_hit = next((item for item in results if item["id"] == expected), None)
            if gold_hit and gold_hit.get("semantic_score") is not None:
                gold_similarities.append(gold_hit["semantic_score"])
            query_tokens.append(sum(estimate_tokens(item["content"]) for item in results))

        negative_latencies: list[float] = []
        negative_nonempty = 0
        negative_top_scores: list[float] = []
        negative_traces: list[dict[str, Any]] = []
        for query in NEGATIVE_QUERIES:
            started = time.perf_counter()
            result = store.search(query, limit=top_k, backend=backend)
            negative_latencies.append((time.perf_counter() - started) * 1000)
            negative_nonempty += bool(result)
            if result and result[0].get("semantic_score") is not None:
                negative_top_scores.append(result[0]["semantic_score"])
            negative_traces.append(
                {
                    "query": query,
                    "top": [
                        {
                            key: item.get(key)
                            for key in (
                                "content",
                                "score",
                                "semantic_score",
                                "lexical_score",
                                "matched_terms",
                            )
                        }
                        for item in result[:2]
                    ],
                }
            )

        ranks = [rank for rank in hit_ranks if rank is not None]
        no_memory = {
            "hit_rate_at_5": 0.0,
            "mrr": 0.0,
            "negative_queries_with_false_recall": 0,
            "retrieved_tokens": 0,
        }
        result = {
            "benchmark": "PolderGraph coding-memory retrieval v1",
            "description": "20 synthetic coding-memory queries (single-hop, paraphrase, user/project scope) and 8 unrelated abstention queries.",
            "model": backend.model_id,
            "device": backend.device,
            "memories": len(CASES),
            "positive_queries": len(CASES),
            "negative_queries": len(NEGATIVE_QUERIES),
            "top_k": top_k,
            "no_memory_baseline": no_memory,
            "poldergraph_memory": {
                "hit_rate_at_5": round(len(ranks) / len(CASES), 4),
                "mrr": round(statistics.fmean(1 / rank for rank in ranks) if ranks else 0, 4),
                "recall_at_1": round(sum(rank == 1 for rank in hit_ranks) / len(CASES), 4),
                "negative_queries_with_false_recall": negative_nonempty,
                "negative_abstention_rate": round(1 - negative_nonempty / len(NEGATIVE_QUERIES), 4),
                "gold_similarity_min": round(min(gold_similarities), 4)
                if gold_similarities
                else None,
                "missed_queries": missed_queries,
                "negative_top_similarity_max": round(max(negative_top_scores), 4)
                if negative_top_scores
                else None,
                "negative_traces": negative_traces,
                "retrieved_tokens_mean": round(statistics.fmean(query_tokens), 1),
                "warm_latency_ms_mean": round(statistics.fmean(latencies), 2),
                "warm_latency_ms_p95": round(percentile(latencies, 0.95), 2),
                "cold_first_query_ms": round(cold_ms, 2),
                "negative_latency_ms_mean": round(statistics.fmean(negative_latencies), 2),
            },
            "limitations": [
                "Synthetic coding facts and paraphrases; not a measure of end-to-end agent task success.",
                "No-memory baseline cannot recall intentionally cross-session facts and retrieves no tokens.",
                "Run on the same machine, model cache, and device to compare revisions.",
            ],
        }
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", default="auto", help="Embedding device: auto, cpu, or cuda")
    parser.add_argument("--top-k", type=int, default=5, help="Maximum memories considered relevant")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON")
    args = parser.parse_args()
    result = run_benchmark(device=args.device, top_k=args.top_k)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0

    baseline = result["no_memory_baseline"]
    memory = result["poldergraph_memory"]
    print(f"{result['benchmark']} ({result['model']} on {result['device']})")
    print(
        f"Dataset: {result['memories']} memories, {result['positive_queries']} positive queries, {result['negative_queries']} abstention queries, k={result['top_k']}"
    )
    print("System                 Hit@5   MRR    False recall  Mean tokens/query")
    print(
        f"No memory              {baseline['hit_rate_at_5']:.3f}   {baseline['mrr']:.3f}   {baseline['negative_queries_with_false_recall']:>5}          {baseline['retrieved_tokens']:>5}"
    )
    print(
        f"PolderGraph memory     {memory['hit_rate_at_5']:.3f}   {memory['mrr']:.3f}   {memory['negative_queries_with_false_recall']:>5}          {memory['retrieved_tokens_mean']:>5.1f}"
    )
    print(
        f"Warm latency mean/p95: {memory['warm_latency_ms_mean']:.2f}/{memory['warm_latency_ms_p95']:.2f} ms; cold first query: {memory['cold_first_query_ms']:.2f} ms"
    )
    print(f"Negative abstention: {memory['negative_abstention_rate']:.1%}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
