"""Python list-of-lists reference for the dependency-free Rust BFS POC."""

from __future__ import annotations

import sys
import time
from collections import deque
from pathlib import Path


def peak_rss_kb() -> int | None:
    try:
        for line in Path("/proc/self/status").read_text().splitlines():
            if line.startswith("VmHWM:"):
                return int(line.split()[1])
    except (OSError, ValueError, IndexError):
        return None
    return None


def main() -> None:
    nodes = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    queries = int(sys.argv[2]) if len(sys.argv) > 2 else 32
    max_depth = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    degree = 8
    adjacency = [
        [(node + offset * offset + offset * 31) % nodes for offset in range(1, degree + 1)]
        for node in range(nodes)
    ]

    started = time.perf_counter_ns()
    checksum = 0
    for query in range(max(1, queries)):
        distances = [-1] * nodes
        seed = (query * 7919) % nodes
        distances[seed] = 0
        queue = deque([seed])
        while queue:
            node = queue.popleft()
            depth = distances[node]
            if depth >= max_depth:
                continue
            for neighbor in adjacency[node]:
                if distances[neighbor] == -1:
                    distances[neighbor] = depth + 1
                    queue.append(neighbor)
        visited = [(node, depth) for node, depth in enumerate(distances) if depth != -1]
        checksum += len(visited)
        checksum += sum(node * (depth + 1) for node, depth in visited)

    elapsed_ns = time.perf_counter_ns() - started
    peak = peak_rss_kb()
    print(
        f"nodes={nodes} edges={nodes * degree} queries={max(1, queries)} "
        f"depth={max_depth} checksum={checksum} elapsed_ns={elapsed_ns} "
        f"peak_rss_kb={peak if peak is not None else 'null'}"
    )


if __name__ == "__main__":
    main()
