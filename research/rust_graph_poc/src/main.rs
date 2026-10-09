use std::collections::VecDeque;
use std::env;
use std::fs;
use std::time::Instant;

fn parse_arg(args: &[String], index: usize, default: usize) -> usize {
    args.get(index)
        .and_then(|value| value.parse().ok())
        .unwrap_or(default)
}

fn peak_rss_kb() -> Option<usize> {
    let status = fs::read_to_string("/proc/self/status").ok()?;
    status.lines().find_map(|line| {
        line.strip_prefix("VmHWM:")
            .and_then(|value| value.split_whitespace().next())
            .and_then(|value| value.parse().ok())
    })
}

fn main() {
    let args: Vec<String> = env::args().collect();
    let nodes = parse_arg(&args, 1, 100);
    let queries = parse_arg(&args, 2, 32);
    let max_depth = parse_arg(&args, 3, 4);
    let degree = 8;

    // Compact CSR graph, built from the exact same deterministic edge formula
    // as python_baseline.py. No external crates or parser/download work.
    let mut offsets = Vec::with_capacity(nodes + 1);
    let mut edges = Vec::with_capacity(nodes * degree);
    offsets.push(0);
    for node in 0..nodes {
        for offset in 1..=degree {
            edges.push((node + offset * offset + offset * 31) % nodes);
        }
        offsets.push(edges.len());
    }

    let started = Instant::now();
    let mut distances = vec![usize::MAX; nodes];
    let mut checksum = 0_u64;
    let query_count = queries.max(1);
    for query in 0..query_count {
        distances.fill(usize::MAX);
        let seed = (query * 7919) % nodes;
        let mut queue = VecDeque::new();
        distances[seed] = 0;
        queue.push_back(seed);
        while let Some(node) = queue.pop_front() {
            let depth = distances[node];
            if depth >= max_depth {
                continue;
            }
            for &neighbor in &edges[offsets[node]..offsets[node + 1]] {
                if distances[neighbor] == usize::MAX {
                    distances[neighbor] = depth + 1;
                    queue.push_back(neighbor);
                }
            }
        }
        checksum += distances.iter().filter(|&&depth| depth != usize::MAX).count() as u64;
        checksum = checksum.wrapping_add(
            distances
                .iter()
                .enumerate()
                .filter(|(_, depth)| **depth != usize::MAX)
                .map(|(node, depth)| node as u64 * (*depth as u64 + 1))
                .sum::<u64>(),
        );
    }
    let elapsed_ns = started.elapsed().as_nanos();
    let peak = peak_rss_kb()
        .map(|value| value.to_string())
        .unwrap_or_else(|| "null".to_string());
    println!(
        "nodes={nodes} edges={} queries={query_count} depth={max_depth} checksum={checksum} elapsed_ns={elapsed_ns} peak_rss_kb={peak}",
        edges.len()
    );
}
