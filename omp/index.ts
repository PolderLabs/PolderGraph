import type { ExtensionAPI } from "@oh-my-pi/pi-coding-agent";
import { spawn } from "node:child_process";
import { stat } from "node:fs/promises";
import { dirname, join, resolve } from "node:path";

const CONTEXT_BUDGET = 3000;
const COMMAND_TIMEOUT_MS = 30 * 60 * 1000;
const MAX_TOOL_OUTPUT = 24_000;
const POLDERGRAPH_SOURCE = "git+https://github.com/PolderLabs/PolderGraph.git";

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
	const indexing = new Map<string, Promise<void>>();
	const workspaceRoots = new Map<string, string>();
	let cliPath: string | undefined;
	let cliSetup: Promise<string> | undefined;

	async function resolveWorkspaceRoot(cwd: string): Promise<string> {
		const original = resolve(cwd);
		const cached = workspaceRoots.get(original);
		if (cached) return cached;
		let candidate = original;
		while (true) {
			try {
				await stat(join(candidate, ".git"));
				workspaceRoots.set(original, candidate);
				return candidate;
			} catch {
				const parent = dirname(candidate);
				if (parent === candidate) break;
				candidate = parent;
			}
		}
		return original;
	}

	async function resolveCli(cwd: string): Promise<string> {
		if (cliPath) return cliPath;
		if (cliSetup) return cliSetup;
		cliSetup = (async () => {
			const found = await pi.exec("poldergraph", ["--version"], { cwd, timeout: 10_000 });
			if (found.code === 0) return "poldergraph";
			const uv = await pi.exec("uv", ["--version"], { cwd, timeout: 10_000 });
			if (uv.code !== 0) throw new Error("PolderGraph and uv are both unavailable; install uv to enable automatic PolderGraph setup.");
			const bin = await pi.exec("uv", ["tool", "dir", "--bin"], { cwd, timeout: 10_000 });
			if (bin.code !== 0 || !bin.stdout.trim()) throw new Error(bin.stderr || "Could not locate the uv tool executable directory.");
			const candidate = join(bin.stdout.trim(), process.platform === "win32" ? "poldergraph.exe" : "poldergraph");
			let installed = await pi.exec(candidate, ["--version"], { cwd, timeout: 10_000 });
			if (installed.code !== 0) {
				const install = await pi.exec("uv", ["tool", "install", `poldergraph @ ${POLDERGRAPH_SOURCE}`], { cwd, timeout: COMMAND_TIMEOUT_MS });
				if (install.code !== 0 || install.killed) throw new Error(install.stderr || "Automatic PolderGraph installation failed.");
				installed = await pi.exec(candidate, ["--version"], { cwd, timeout: 10_000 });
			}
			if (installed.code !== 0) throw new Error(installed.stderr || "PolderGraph installation did not produce a working executable.");
			return candidate;
		})();
		try {
			cliPath = await cliSetup;
			return cliPath;
		} finally {
			cliSetup = undefined;
		}
	}

	async function run(
		args: string[],
		cwd: string,
		signal?: AbortSignal,
	): Promise<{ code: number; stdout: string; stderr: string; killed: boolean }> {
		const root = await resolveWorkspaceRoot(cwd);
		return pi.exec(await resolveCli(root), args, { cwd: root, signal, timeout: COMMAND_TIMEOUT_MS });
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

	async function ensureIndex(cwd: string): Promise<void> {
		const root = await resolveWorkspaceRoot(cwd);
		const active = indexing.get(root);
		if (active) return active;
		const work = (async () => {
			const ready = await runJson(["agent-ready", "--quiet"], root);
			if (!ready.ok) throw new Error(formatResult(ready));
			if ((ready.data as { state?: string } | undefined)?.state === "unavailable") return;
		})();
		indexing.set(root, work);
		try {
			await work;
		} finally {
			indexing.delete(root);
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

	// Start indexing without blocking session startup. The first task joins this
	// job before receiving context, and later turns refresh stale data.
	pi.on("session_start", (_event, ctx) => {
		void ensureIndex(ctx.cwd).catch((error) => {
			pi.logger.warn(`PolderGraph automatic setup failed: ${error instanceof Error ? error.message : String(error)}`);
		});
	});
	pi.on("tool_result", (event, ctx) => {
		if (event.isError || (event.toolName !== "edit" && event.toolName !== "write")) return;
		void ensureIndex(ctx.cwd).catch((error) => {
			pi.logger.warn(`PolderGraph background refresh failed: ${error instanceof Error ? error.message : String(error)}`);
		});
	});

	pi.registerTool({
		name: "poldergraph_status",
		label: "PolderGraph Status",
		description: "Check whether the local PolderGraph repository index exists and is fresh.",
		parameters: z.object({}),
		async execute(_id, _params, signal, _onUpdate, ctx) {
			return toolResult(["status"], ctx.cwd, signal);
		},
	});

	// Add grounded repository context before each task from the local index.
	pi.on("before_agent_start", async (event, ctx) => {
		if (!event.prompt.trim()) return;
		try {
			await ensureIndex(ctx.cwd);

			const context = await runJson(
				["context", event.prompt, "--budget", String(CONTEXT_BUDGET), "--offline"],
				ctx.cwd,
			);
			if (!context.ok || !context.data) return;
			const contextData = context.data as { plan?: { skipped?: boolean } };
			if (contextData.plan?.skipped) return;
			return {
				systemPrompt: [
					...event.systemPrompt,
					"PolderGraph repository context (local index; use as navigation evidence, then inspect the cited source files. Semantic similarity is not proof of a dependency):\n" +
						JSON.stringify(context.data),
					"PolderGraph memory is shared locally across projects. Relevant user preferences and project notes are already included above. Context retrieval is read-only. Save a durable preference only through an explicit memory action when the user directly asks; save durable project knowledge with poldergraph_remember. If a user corrects a preference, update or forget the older note. Never store credentials or one-off task details.",
				],
			};
		} catch (error) {
			return {
				systemPrompt: [
					...event.systemPrompt,
					`PolderGraph automatic setup or refresh failed: ${error instanceof Error ? error.message : String(error)}. Continue with normal repository inspection and retry PolderGraph on a later task.`,
				],
			};
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
		name: "poldergraph_memory_search",
		label: "PolderGraph Memory Search",
		description: "Recall semantically related user preferences and this project's durable notes from the shared local memory store.",
		parameters: z.object({
			query: z.string().describe("Current task, preference, or project concept to recall"),
			scope: z.enum(["all", "project", "user"]).default("all"),
			limit: z.number().int().min(1).max(50).default(10),
		}),
		async execute(_id, params, signal, _onUpdate, ctx) {
			return toolResult(["memory", "search", params.query, "--scope", params.scope, "--limit", String(params.limit)], ctx.cwd, signal);
		},
	});

	pi.registerTool({
		name: "poldergraph_memory_list",
		label: "PolderGraph Memory List",
		description: "List shared user memories and memories scoped to the current project.",
		parameters: z.object({
			scope: z.enum(["all", "project", "user"]).default("all"),
			limit: z.number().int().min(1).max(100).default(50),
		}),
		async execute(_id, params, signal, _onUpdate, ctx) {
			return toolResult(["memory", "list", "--scope", params.scope, "--limit", String(params.limit)], ctx.cwd, signal);
		},
	});

	pi.registerTool({
		name: "poldergraph_remember",
		label: "PolderGraph Remember",
		description: "Save a durable project fact, decision, or user preference to the shared local memory. Never save secrets or transient task details.",
		parameters: z.object({
			content: z.string().min(1).describe("One concise, reusable fact, preference, decision, or workflow"),
			scope: z.enum(["project", "user"]).default("project"),
			kind: z.enum(["fact", "preference", "decision", "workflow", "reference"]).default("fact"),
			tags: z.array(z.string()).max(20).default(() => []),
		}),
		async execute(_id, params, signal, _onUpdate, ctx) {
			const args = ["memory", "add", params.content, "--scope", params.scope, "--kind", params.kind];
			for (const tag of params.tags) args.push("--tag", tag);
			return toolResult(args, ctx.cwd, signal);
		},
	});

	pi.registerTool({
		name: "poldergraph_memory_forget",
		label: "PolderGraph Forget Memory",
		description: "Delete a user or current-project memory by ID from the shared local store.",
		parameters: z.object({ memory_id: z.string() }),
		async execute(_id, params, signal, _onUpdate, ctx) {
			return toolResult(["memory", "forget", params.memory_id], ctx.cwd, signal);
		},
	});

	pi.registerTool({
		name: "poldergraph_memory_update",
		label: "PolderGraph Update Memory",
		description: "Update the text, type, or tags for one user or current-project memory.",
		parameters: z.object({
			memory_id: z.string(),
			content: z.string().optional(),
			kind: z.enum(["fact", "preference", "decision", "workflow", "reference"]).optional(),
			tags: z.array(z.string()).max(20).optional(),
			clear_tags: z.boolean().default(false),
		}),
		async execute(_id, params, signal, _onUpdate, ctx) {
			const args = ["memory", "update", params.memory_id];
			if (params.content !== undefined) args.push("--content", params.content);
			if (params.kind !== undefined) args.push("--kind", params.kind);
			for (const tag of params.tags ?? []) args.push("--tag", tag);
			if (params.clear_tags) args.push("--clear-tags");
			return toolResult(args, ctx.cwd, signal);
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
		description: "Open the graph dashboard, configure PolderGraph, or run an index command",
		handler: async (args, ctx) => {
			const parsed = splitCommandLine(args);
			const subcommand = parsed[0] || "status";
			if (subcommand === "ui" || subcommand === "dashboard") {
				try {
					await ensureIndex(ctx.cwd);
					const root = await resolveWorkspaceRoot(ctx.cwd);
					const child = spawn(await resolveCli(root), ["ui"], {
						cwd: root,
						detached: true,
						stdio: "ignore",
						windowsHide: true,
					});
					child.once("error", (error) => pi.logger.warn(`Could not start PolderGraph dashboard: ${error.message}`));
					child.unref();
					ctx.ui.notify("PolderGraph dashboard: http://127.0.0.1:7432", "info");
				} catch (error) {
					ctx.ui.notify(error instanceof Error ? error.message : String(error), "warning");
				}
				return;
			}
			const allowed = new Set(["status", "search", "context", "memory", "explain", "path", "related", "impact", "update", "config"]);
			if (!allowed.has(subcommand)) {
				ctx.ui.notify("Supported commands: ui, config, status, search, context, explain, path, related, impact, update", "warning");
				return;
			}
			const commandArgs = [subcommand, ...parsed.slice(1)];
			if (!(subcommand === "config" && parsed[1] === "set")) commandArgs.push("--json");
			const result = await run(commandArgs, ctx.cwd);
			const output = result.stdout || result.stderr || `poldergraph ${subcommand} exited with code ${result.code}`;
			ctx.ui.notify(output.slice(0, 1000), result.code === 0 ? "info" : "warning");
		},
	});
}
