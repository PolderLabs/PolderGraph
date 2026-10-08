# Papers and empirical results

**Reviewed 2026-10-08**. Reported numbers below belong to authors' evaluations, **not PolderGraph performance**. Each paper has a different agent, dataset, baseline and success metric; never directly compare percentages across papers.

## Highest relevance to automatic repository intelligence

### RepoAtlas — evolving task-conditioned views (September 2026)
[RepoAtlas: Guiding Coding Agents via Evolving Multimodal Repository Views](https://arxiv.org/abs/2609.16936)

- Maintains evolving repository context with **select → project → refresh**, driven by issue evidence and agent exploration state.
- Paper reports +2.4 point SWE-bench Verified resolve rate relative to its strongest multimodal graph baseline, with 5.8% fewer input tokens and 7.8% fewer model calls.
- **PG application:** task-aware context snapshots, refresh trigger on changed exploration/edits, delta-context packs, explicit context lifetime. Do **not** require graph screenshots/multimodal model input; text/structured evidence remains primary.

### Agent Retrieval Bench — workflow-specific retrieval + abstention (July 2026)
[Paper](https://arxiv.org/abs/2607.24882) · [dataset/implementation](https://github.com/eyuansu62/agent-retrieval-bench)

- 427 workflow signals from 25 repositories, with `code2test`, `comment2context`, `trace2code`, `edit2ripple`, plus natural and counterfactual no-gold examples.
- Reports no single retrieval family wins every task; natural no-gold abstention remained difficult under counterfactual-calibrated thresholds.
- **PG application:** route retrieval by work signal; use separate selection heads for tests, root cause, review, ripple effects; benchmark safe abstention beyond fabricated unrelated queries.
- Freeze repo commit, inspect dataset licensing and build reproducible fixtures before claims.

### SWE-Explore — region retrieval under budget (June 2026)
[SWE-Explore: Benchmarking How Coding Agents Explore Repositories](https://arxiv.org/abs/2606.07297)

- 848 issues / 203 repositories / 10 languages, with ranked code-region retrieval under a line budget and reference traces derived from independently successful repair trajectories.
- **PG application:** evaluate **line-level** coverage/ranking and token/line efficiency, not only correct file or Hit@5. Treat trajectory-derived ground truth as approximate: valid fixes may take different paths.

### RepoNavigator — fewer, stronger navigation tools (ICML 2026)
[One Tool Is Enough: Reinforcement Learning of LLM Agents for Repository-Level Code Navigation](https://proceedings.mlr.press/v306/zhang26an.html)

- An execution-aware jump-to-definition interface facilitates repository issue localization. Paper attributes its results to the trained agent and tool design together.
- **PG application:** compact, stable symbols and navigation primitives. Do not infer that adding a tool alone will reproduce an RL-trained agent's results.

### ARISE — statement-level def-use slicing (May 2026)
[ARISE: A Repository-level Graph Representation and Toolset for Agentic Fault Localization and Program Repair](https://arxiv.org/abs/2605.03117)

- Extends code graphs with intra-procedural statement-level definition/use edges; benchmark on SWE-bench Lite (300 issues, Python); paper reports +17.0 Function Recall@1, +15.0 Line Recall@1, +4.7 Pass@1 points over its SWE-agent baseline.
- **PG application:** optional lazy per-function def-use/slicing index for debug/trace tasks; avoid exploding baseline graph size for every AST statement. Return variable-flow evidence with uncertainty for dynamic behavior.

### Repository Intelligence Graph / SPADE — build and test architecture (January 2026)
[Repository Intelligence Graph: Deterministic Architectural Map for LLM Code Assistants](https://arxiv.org/abs/2601.10112)

- Represents buildable components, runners, tests, dependencies and package managers using deterministic build/test definitions; initial extractor targets CMake File API/CTest.
- Authors report +12.2% mean agent architecture-answer accuracy and 53.9% lower completion time across their setup.
- **PG application:** source-backed build/test/CI dependency edges, not merely function calls. Add dedicated parsers for package manifests/build graphs/test runners and preserve provenance/unsupported-file warnings.

## Supporting work

- [CodexGraph (NAACL 2025)](https://aclanthology.org/2025.naacl-long.7/): graph-query interface for repository agents; support structured relationship queries but shield model from unbounded raw graph execution.
- [DependEval (ACL Findings 2025)](https://aclanthology.org/2025.findings-acl.373/): repository dependency understanding benchmark; add cross-file/transitive understanding cases.
- [CodeRAG-Bench (NAACL Findings 2025)](https://aclanthology.org/2025.findings-naacl.176/): retrieval quality and downstream code-generation quality are distinct; instrument both.
- [RepoMaster (2025 preprint)](https://arxiv.org/abs/2505.21577): progressive exploration of core graph components instead of indiscriminately loading code.
- [Graph of Trace (ACL Demo 2026)](https://aclanthology.org/2026.acl-demo.29/): execution events as structured traces; relevant to opt-in agent-action provenance, **not** automatic full transcript capture.
- [MemoryAgentBench](https://arxiv.org/abs/2507.05257), [MemoryArena](https://proceedings.mlr.press/v306/he26am.html), [APEX-MEM](https://arxiv.org/abs/2604.14362), [MAGE](https://www.microsoft.com/en-us/research/publication/beyond-semantic-organization-memory-as-execution-state-management-for-long-horizon-agents/): covered by existing [issue #22](https://github.com/PolderLabs/PolderGraph/issues/22); do not implement an unrelated memory platform ahead of code-index autonomy.

## Research interpretation

1. Better retrieval is **task-state aware**, not simply a larger embedding model.
2. Structural correctness (source links and precise symbol identity) matters especially for debugging, test selection and hidden dependencies.
3. Local-first graph retrieval should **abstain** when the repository does not support an answer.
4. Automatically *using* a tool is a distinct research question from whether it yields good results when called.
5. Evidence freshness and accuracy must be measured independently of latency/token efficiency.
