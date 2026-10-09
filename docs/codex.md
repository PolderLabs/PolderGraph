# Codex lifecycle integration

PolderGraph can add repository context to Codex automatically with Codex's
`UserPromptSubmit` lifecycle hook. The hook receives the user prompt and
workspace path from Codex, resolves nested working directories to their
enclosing Git repository or worktree, refreshes the local index when needed, and returns
context through Codex's documented `hookSpecificOutput.additionalContext`
field. It does not need the model to call an MCP tool first.

Install or update the Codex integration with:

```bash
poldergraph setup-agent --agent codex --hooks
```

`--hooks` is explicit because it adds a command to `.codex/hooks.json`. The
setup preserves other hook events and handlers, and repeated runs do not add a
second PolderGraph handler. Without `--hooks`, setup only adds the Codex skill
and MCP configuration.

Automatic context uses offline CLI calls. On the first user task it creates a
structural index without downloading an embedding model. It retrieves compact
context for relevant tasks and skips social prompts. No user prompt is saved
to PolderGraph memory. To use semantic context, warm an already selected local
model explicitly with `poldergraph update`.

The hook can be disabled by removing the PolderGraph `UserPromptSubmit`
handler from `.codex/hooks.json`; MCP and skill guidance continue to work.
PolderGraph only writes this hook when `--hooks` is supplied.

The integration follows Codex's lifecycle-hook contract: the
`UserPromptSubmit` input includes `prompt`, `cwd`, `session_id`, and `turn_id`,
and its command output can provide `hookSpecificOutput` with
`hookEventName: "UserPromptSubmit"` and `additionalContext`. See the [Codex
lifecycle hooks documentation](https://developers.openai.com/codex/config-advanced#lifecycle-hooks).
