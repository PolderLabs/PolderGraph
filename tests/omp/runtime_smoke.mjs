import assert from "node:assert/strict";
import { once } from "node:events";
import { spawn } from "node:child_process";
import { createServer } from "node:http";
import { mkdtemp, mkdir, readFile, rm, writeFile, chmod } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const root = await mkdtemp(join(tmpdir(), "poldergraph-omp-smoke-"));
const binDir = join(root, "bin");
const fixtureRoot = join(root, "fixture");
const agentDir = join(root, "agent");
const callLog = join(root, "poldergraph-calls.jsonl");
const modelRequests = [];
const server = createServer(async (request, response) => {
	if (request.method !== "POST") {
		response.writeHead(200, { "content-type": "application/json" });
		response.end(JSON.stringify({ data: [] }));
		return;
	}
	const chunks = [];
	for await (const chunk of request) chunks.push(chunk);
	modelRequests.push(JSON.parse(Buffer.concat(chunks).toString("utf8")));
	response.writeHead(200, { "content-type": "text/event-stream" });
	response.end([
		`data: ${JSON.stringify({ id: "smoke", object: "chat.completion.chunk", created: 1, model: "gpt-4o-mini", choices: [{ index: 0, delta: { role: "assistant", content: "runtime smoke passed" }, finish_reason: null }] })}\n\n`,
		`data: ${JSON.stringify({ id: "smoke", object: "chat.completion.chunk", created: 1, model: "gpt-4o-mini", choices: [{ index: 0, delta: {}, finish_reason: "stop" }] })}\n\n`,
		"data: [DONE]\n\n",
	].join(""));
});

let child;
try {
	await mkdir(binDir, { recursive: true });
	await mkdir(fixtureRoot, { recursive: true });
	await mkdir(agentDir, { recursive: true });
	await mkdir(join(fixtureRoot, ".git"));
	await writeFile(join(fixtureRoot, "auth.py"), "class AuthService:\n    pass\n");
	await writeFile(callLog, "");
	const stub = `#!/usr/bin/env node\nconst fs = await import('node:fs');\nconst args = process.argv.slice(2);\nfs.appendFileSync(${JSON.stringify(callLog)}, JSON.stringify(args) + '\\n');\nif (args[0] === '--version') process.stdout.write('poldergraph smoke\\n');\nelse if (args[0] === 'agent-ready') process.stdout.write(JSON.stringify({ok:true,data:{state:'ready'}}));\nelse if (args[0] === 'context') process.stdout.write(JSON.stringify({ok:true,data:{evidence_cursor:'opaque-cursor',snippets:[{path:'auth.py',text:'class AuthService: pass'}]}}));\nelse process.exitCode = 2;\n`;
	const cli = join(binDir, "poldergraph");
	await writeFile(cli, stub);
	await chmod(cli, 0o755);
	server.listen(0, "127.0.0.1");
	await once(server, "listening");
	const address = server.address();
	assert(address && typeof address === "object");
	await writeFile(join(agentDir, "models.yml"), `providers:\n  openai:\n    baseUrl: http://127.0.0.1:${address.port}/v1\n    apiKey: runtime-smoke-key\n    api: openai-completions\n    models:\n      - id: gpt-4o-mini\n        name: Runtime smoke model\n        contextWindow: 128000\n        maxTokens: 4096\n`);
	const omp = process.env.OMP_BIN ?? "omp";
	child = spawn(omp, [
		"--extension", resolve("omp/index.ts"), "--print", "--no-session", "--no-title",
		"--cwd", fixtureRoot, "--model", "openai/gpt-4o-mini", "Where is AuthService?",
	], {
		cwd: fixtureRoot,
		stdio: ["ignore", "pipe", "pipe"],
		env: {
			...process.env,
			PATH: `${binDir}${process.platform === "win32" ? ";" : ":"}${process.env.PATH}`,
			PI_CODING_AGENT_DIR: agentDir,
		},
	});
	const stdout = [];
	const stderr = [];
	child.stdout.on("data", (chunk) => stdout.push(chunk));
	child.stderr.on("data", (chunk) => stderr.push(chunk));
	const [code] = await once(child, "close");
	const cliCalls = (await readFile(callLog, "utf8")).trim().split("\n").filter(Boolean).map(JSON.parse);
	assert.equal(code, 0, Buffer.concat(stderr).toString("utf8"));
	assert(cliCalls.some((args) => args[0] === "agent-ready"), "session start did not bootstrap PolderGraph");
	assert(cliCalls.some((args) => args[0] === "context" && args.includes("--offline")), "task start did not request offline context");
	const systemMessages = modelRequests.flatMap((request) => request.messages ?? []).filter((message) => message.role === "system");
	assert(systemMessages.some((message) => JSON.stringify(message.content).includes("class AuthService: pass")), "grounded PolderGraph context was not sent to the model");
	assert(Buffer.concat(stdout).toString("utf8").includes("runtime smoke passed"));
	console.log("OMP 18 runtime loaded the extension, auto-bootstrapped PolderGraph, and sent grounded context to the model.");
} finally {
	child?.kill();
	server.close();
	await rm(root, { recursive: true, force: true });
}
