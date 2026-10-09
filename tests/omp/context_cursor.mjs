import assert from "node:assert/strict";
import extension from "../../omp/index.ts";

const handlers = new Map();
const contextCalls = [];
let readyCalls = 0;
const chain = () => ({
	int() { return this; }, min() { return this; }, max() { return this; },
	default() { return this; }, describe() { return this; }, optional() { return this; },
});
const zod = {
	object: (value) => value,
	string: chain,
	number: chain,
	enum: chain,
	array: () => ({ max() { return this; }, default() { return this; }, optional() { return this; } }),
	boolean: chain,
};
const pi = {
	zod,
	setLabel() {},
	on(name, callback) { handlers.set(name, callback); },
	registerTool() {},
	registerCommand() {},
	logger: { warn(message) { throw new Error(message); } },
	async exec(_command, args) {
		if (args[0] === "--version") return { code: 0, stdout: "poldergraph test", stderr: "", killed: false };
		if (args[0] === "agent-ready") {
			readyCalls += 1;
			await new Promise((resolve) => setTimeout(resolve, 10));
			return { code: 0, stdout: JSON.stringify({ ok: true, data: { state: "ready" } }), stderr: "", killed: false };
		}
		if (args[0] !== "context") throw new Error(`Unexpected PolderGraph command: ${args[0]}`);
		contextCalls.push(args);
		const repeat = contextCalls.length > 1;
		const stale = contextCalls.length > 2;
		return {
			code: 0,
			stderr: "",
			killed: false,
			stdout: JSON.stringify({
				ok: true,
				data: {
					evidence_cursor: "opaque-cursor",
					new_evidence_count: repeat ? 0 : 1,
					index: { fresh: !stale },
					entities: repeat && !stale ? [] : [{ name: "AuthService" }],
					snippets: repeat && !stale ? [] : [{ path: "auth.py", text: "class AuthService: pass" }],
				},
			}),
		};
	},
};

extension(pi);
await handlers.get("session_start")({}, { cwd: process.cwd() });
const event = { prompt: "Where is AuthService?", systemPrompt: [] };
const context = await handlers.get("before_agent_start")(event, { cwd: process.cwd() });
assert(context?.systemPrompt?.some((item) => item.includes("AuthService")));

const repeated = await handlers.get("before_agent_start")(event, { cwd: process.cwd() });
assert.equal(repeated, undefined, "fresh repeated evidence should not be injected again");
assert(contextCalls[1].includes("--new-evidence-since"), "subsequent retrieval must use the opaque cursor");

const stale = await handlers.get("before_agent_start")(event, { cwd: process.cwd() });
assert(stale?.systemPrompt?.some((item) => item.includes("AuthService")), "stale index evidence remains visible");
assert.equal(contextCalls.length, 3);

const setupCount = readyCalls;
handlers.get("tool_result")({ toolName: "edit", isError: false }, { cwd: process.cwd() });
handlers.get("tool_result")({ toolName: "write", isError: false }, { cwd: process.cwd() });
await new Promise((resolve) => setTimeout(resolve, 30));
assert.equal(readyCalls - setupCount, 1, "concurrent successful edits should coalesce into one refresh");
console.log("OMP cursor suppresses repeated fresh evidence, preserves stale context, and coalesces edit refreshes.");
