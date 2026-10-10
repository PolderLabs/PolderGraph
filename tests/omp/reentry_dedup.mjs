import assert from "node:assert/strict";
import extension from "../../omp/index.ts";

// Host re-entry for a turn already handled must not inject the same context
// twice, even when the server cannot help: the cursor is absent from the
// response, so the client-side prompt guard is the only defense.

const handlers = new Map();
let contextCalls = 0;
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
	logger: { warn() {} },
	async exec(_command, args) {
		if (args[0] === "--version") return { code: 0, stdout: "poldergraph test", stderr: "", killed: false };
		if (args[0] === "agent-ready") {
			return { code: 0, stdout: JSON.stringify({ ok: true, data: { state: "ready" } }), stderr: "", killed: false };
		}
		if (args[0] !== "context") throw new Error(`Unexpected PolderGraph command: ${args[0]}`);
		contextCalls += 1;
		// No evidence_cursor is returned, so cursor-based suppression cannot apply.
		return {
			code: 0,
			stderr: "",
			killed: false,
			stdout: JSON.stringify({
				ok: true,
				data: {
					new_evidence_count: 0,
					index: { fresh: true },
					entities: [{ name: "AuthService" }],
					snippets: [],
				},
			}),
		};
	},
};

extension(pi);
await handlers.get("session_start")({}, { cwd: process.cwd() });
const event = { prompt: "Where is AuthService?", systemPrompt: [] };

const first = await handlers.get("before_agent_start")(event, { cwd: process.cwd() });
assert(first?.systemPrompt?.some((item) => item.includes("AuthService")), "first turn injects context");

const reentry = await handlers.get("before_agent_start")(event, { cwd: process.cwd() });
assert.equal(reentry, undefined, "host re-entry for the same turn must not inject again");

const otherPrompt = { prompt: "Where is Session defined?", systemPrompt: [] };
const distinct = await handlers.get("before_agent_start")(otherPrompt, { cwd: process.cwd() });
assert(distinct?.systemPrompt?.some((item) => item.includes("AuthService")), "a new prompt still injects");

handlers.get("tool_result")({ toolName: "edit", isError: false }, { cwd: process.cwd() });
await new Promise((resolve) => setTimeout(resolve, 30));
const afterEdit = await handlers.get("before_agent_start")(otherPrompt, { cwd: process.cwd() });
assert(afterEdit?.systemPrompt?.some((item) => item.includes("AuthService")), "an edit re-opens injection");

console.log("OMP suppresses duplicate injection on hook re-entry and re-opens after an edit.");