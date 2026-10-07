import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";

const CONTEXT_BUDGET = 3000;
const COMMAND_TIMEOUT_MS = 120_000;
const MAX_TOOL_OUTPUT = 24_000;

type JsonEnvelope = {
	ok?: boolean;
	command?: string;
	index?: { fresh?: boolean; root?: string };
	data?: unknown;
	error?: { code?: string; message?: string; remediation?: string } | null;
	warnings?: string[];
};

function formatResult(result: JsonEnvelope): string {
	if (!result.ok) {
		const error = result.error;
		return [error?.message ?? "PolderGraph command failed.", error?.remediation]
			.filter(Boolean)
			.join("\n");
	}
	return JSON.stringify(result, null, 2);
}

function splitCommandLine(input: string): string[] {
	const parts: string[] = [];
	let current = "";
	let quote: "'" | '"' | null = null;
	let escaped = false;
	for (const char of input) {
		if (escaped) {
			current += char;
			escaped = false;
		} else if (char === "\\" && quote !== "'") {
			escaped = true;
		} else if (quote) {
			if (char === quote) quote = null;
			else current += char;
		} else if (char === "'" || char === '"') {
			quote = char;
		} else if (/\s/.test(char)) {
			if (current) parts.push(current);
			current = "";
		} else {
			current += char;
		}
	}
	if (escaped) current += "\\";
	if (current) parts.push(current);
	return parts;
}

export default function polderGraphExtension(pi: ExtensionAPI) {
	const z = pi.zod;

	async function run(
		args: string[],
		cwd: string,
		signal?: AbortSignal,
	): Promise<{ code: number; stdout: string; stderr: string; killed: boolean }> {
		return pi.exec("poldergraph", args, { cwd, signal, timeout: COMMAND_TIMEOUT_MS });
	}

	async function runJson(args: string[], cwd: string, signal?: AbortSignal): Promise<JsonEnvelope> {
		const result = await run([...args, "--json"], cwd, signal);
		if (result.killed) throw new Error("PolderGraph command timed out or was cancelled.");
		if (!result.stdout.trim()) {
			throw new Error(result.stderr.trim() || `poldergraph ${args[0]} exited with code ${result.code}`);
		}
		try {
			return JSON.parse(result.stdout) as JsonEnvelope;
		} catch {
			throw new Error(`PolderGraph returned invalid JSON: ${result.stderr || result.stdout}`);
		}
	}

	async function toolResult(args: string[], cwd: string, signal?: AbortSignal) {
		try {
			const result = await runJson(args, cwd, signal);
			const text = formatResult(result);
			return {
				content: [{ type: "text" as const, text: text.length > MAX_TOOL_OUTPUT ? `${text.slice(0, MAX_TOOL_OUTPUT)}\n[output truncated]` : text }],
				details: result,
				isError: !result.ok,
			};
		} catch (error) {
			return {
				content: [{ type: "text" as const, text: error instanceof Error ? error.message : String(error) }],
				isError: true,
			};
		}
	}

	pi.setLabel("PolderGraph");

	pi.registerTool({
		name: "poldergraph_status",
		label: "PolderGraph Status",
		description: "Check whether the local PolderGraph repository index exists and is fresh.",
		parameters: z.object({}),
		async execute(_id, _params, signal, _onUpdate, ctx) {
			return toolResult(["status"], ctx.cwd, signal);
		},
	});

	// Add grounded repository context before each user task. No content leaves the
	// machine: the extension invokes the local PolderGraph CLI in the active cwd.
	pi.on("before_agent_start", async (event, ctx) => {
		if (!event.prompt.trim()) return;
		try {
			const status = await runJson(["status"], ctx.cwd);
			if (!status.ok) return;

			if (status.index?.fresh === false) {
				const update = await run(["update", "--quiet"], ctx.cwd);
				if (update.code !== 0 || update.killed) {
					return {
						systemPrompt: [
							...event.systemPrompt,
							"PolderGraph index is stale and could not be refreshed. Treat any existing graph results as stale; run `poldergraph update --quiet` before relying on them.",
						],
					};
				}
			}

			const context = await runJson(
				["context", event.prompt, "--budget", String(CONTEXT_BUDGET)],
				ctx.cwd,
			);
			if (!context.ok || !context.data) return;
			return {
				systemPrompt: [
					...event.systemPrompt,
					"PolderGraph repository context (local index; use as navigation evidence, then inspect the cited source files. Semantic similarity is not proof of a dependency):\n" +
						JSON.stringify(context.data),
				],
			};
		} catch {
			// Keep agent startup usable when PolderGraph is absent or unavailable.
		}
	});

	pi.registerTool({
		name: "poldergraph_search",
		label: "PolderGraph Search",
		description: "Search the local PolderGraph code intelligence index using hybrid lexical, semantic, and structural retrieval.",
		parameters: z.object({ query: z.string().describe("Question, concept, symbol, or path to search for"), limit: z.number().int().min(1).max(50).default(10).describe("Maximum results") }),
		async execute(_id, params, signal, _onUpdate, ctx) {
			return toolResult(["search", params.query, "--limit", String(params.limit)], ctx.cwd, signal);
		},
	});

	pi.registerTool({
		name: "poldergraph_context",
		label: "PolderGraph Context",
		description: "Retrieve a focused, token-budgeted context pack for a repository task from PolderGraph.",
		parameters: z.object({ query: z.string().describe("Repository question or task"), budget: z.number().int().min(256).max(12000).default(CONTEXT_BUDGET).describe("Approximate context token budget") }),
		async execute(_id, params, signal, _onUpdate, ctx) {
			return toolResult(["context", params.query, "--budget", String(params.budget)], ctx.cwd, signal);
		},
	});

	pi.registerTool({
		name: "poldergraph_explain",
		label: "PolderGraph Explain",
		description: "Inspect a symbol or path and its indexed relationships in PolderGraph.",
		parameters: z.object({ entity: z.string().describe("Entity ID, symbol name, qualified name, or path") }),
		async execute(_id, params, signal, _onUpdate, ctx) {
			return toolResult(["explain", params.entity], ctx.cwd, signal);
		},
	});

	pi.registerTool({
		name: "poldergraph_path",
		label: "PolderGraph Path",
		description: "Find a relationship path between two repository entities.",
		parameters: z.object({ source: z.string(), target: z.string() }),
		async execute(_id, params, signal, _onUpdate, ctx) {
			return toolResult(["path", params.source, params.target], ctx.cwd, signal);
		},
	});

	pi.registerTool({
		name: "poldergraph_impact",
		label: "PolderGraph Impact",
		description: "Find code and tests that may be affected by changing an entity or path.",
		parameters: z.object({ target: z.string(), max_depth: z.number().int().min(1).max(8).default(3) }),
		async execute(_id, params, signal, _onUpdate, ctx) {
			return toolResult(["impact", params.target, "--max-depth", String(params.max_depth)], ctx.cwd, signal);
		},
	});

	pi.registerTool({
		name: "poldergraph_related",
		label: "PolderGraph Related",
		description: "Find semantically related entities and distinguish semantic neighbors from structural connections.",
		parameters: z.object({ entity: z.string(), limit: z.number().int().min(1).max(50).default(10) }),
		async execute(_id, params, signal, _onUpdate, ctx) {
			return toolResult(["related", params.entity, "--limit", String(params.limit)], ctx.cwd, signal);
		},
	});

	pi.registerTool({
		name: "poldergraph_update",
		label: "PolderGraph Update",
		description: "Incrementally refresh the local PolderGraph index after repository changes.",
		parameters: z.object({}),
		async execute(_id, _params, signal, _onUpdate, ctx) {
			const result = await run(["update", "--json"], ctx.cwd, signal);
			return {
				content: [{ type: "text" as const, text: result.stdout || result.stderr || `poldergraph update exited with code ${result.code}` }],
				isError: result.code !== 0 || result.killed,
			};
		},
	});

	pi.registerCommand("poldergraph", {
		description: "Show PolderGraph index status or run an index command",
		handler: async (args, ctx) => {
			const parsed = splitCommandLine(args);
			const subcommand = parsed[0] || "status";
			const allowed = new Set(["status", "search", "context", "explain", "path", "related", "impact", "update"]);
			if (!allowed.has(subcommand)) {
				ctx.ui.notify("Supported commands: status, search, context, explain, path, related, impact, update", "warning");
				return;
			}
			const result = await run([subcommand, ...parsed.slice(1), "--json"], ctx.cwd);
			const output = result.stdout || result.stderr || `poldergraph ${subcommand} exited with code ${result.code}`;
			ctx.ui.notify(output.slice(0, 1000), result.code === 0 ? "info" : "warning");
		},
	});
}
