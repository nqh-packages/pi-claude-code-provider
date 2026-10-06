# Claude Code provider for Pi

Use your existing Claude Code sign-in for inference. Pi keeps its agent loop, tools, approvals, transcript and compaction.

```text
Pi history + tool inventory
            │
     TypeScript provider
            │ JSONL
     Python transport
            │
     Official Claude Code CLI ──► Claude
            │
     Complete response / tool call
            │
     Pi executes the tool ──► Pi sends its result
```

## Run it

Install the official [Claude Code CLI](https://code.claude.com/docs/en/setup) and the Pi host versions declared in [`package.json`](package.json). Node's minimum is in `engines`; Python must support the transport, with the exercised version recorded in acceptance receipts.

```sh
claude auth status
# If signed out:
claude auth login

cd /path/to/pi-claude-code-provider
pnpm install --frozen-lockfile
pnpm check
pnpm build

pi --offline -e . --model 'claude-code/claude-sonnet-5-5[1m]'
```

This loads the provider for that invocation; it does not install the package globally. In Pi, `/claude-code-status` checks the CLI sign-in. `/model` lists available `claude-code` routes. Only models with matching Pi capability metadata are advertised. Thinking choices come from the pinned transport and Pi catalog, so mandatory-thinking models do not offer `off`.

For persistent installation, use Pi's [local-package mechanism](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md): `pi install /absolute/path/to/pi-claude-code-provider`. Remove it with `pi remove /absolute/path/to/pi-claude-code-provider`. Neither command is required for the invocation above.

## Boundaries

- **Experimental.** Official [headless CLI flags](https://code.claude.com/docs/en/cli-reference) and Pi provider registration are public interfaces. Native-history replay, initialization/picker handling and `CLAUDE_CODE_EXTRA_BODY` are pinned implementation details, not documented public contracts. CLI updates can break them. This adapter is not an Anthropic endorsement or an account-policy guarantee.
- **Pi executes tools.** Native tools are disabled. An inert MCP inventory exposes Pi's tool schemas; an HTTP admission gate limits each model call to one upstream inference request. Only a complete, validated tool batch can reach Pi. Refused or truncated responses cannot execute tools.
- **CLI owns authentication.** The adapter asks the CLI for status and lets it supply/refresh credentials. It does not read credential files or extract tokens. Inherited API keys, endpoint overrides or alternative backends are rejected by the production transport rather than silently mixing subscription and API access.
- **Workspace isolation is not a sandbox.** Each provider lifetime owns a private native cwd. Pi tools still run under Pi's permissions. Prompt content, images and tool results are sent to Claude.
- **Cancellation is protocol-first.** Python closes its owned native client before a bounded Python hard-kill fallback. Normal request cancellation and descendant exit are exercised by the live check. A hung interpreter's hard-kill fallback is not a guarantee that all descendants exit. Windows and Linux are not runtime-qualified by the macOS receipts.
- **Costs are estimates, not subscription charges.** A usable native list-price total takes precedence; components remain catalog estimates and may not sum to that total. Otherwise known catalog pricing is used, preserving reported one-hour cache writes. Missing prices use numeric zero only to satisfy Pi's schema, with `unknown`/`unavailable` diagnostics. Never interpret that zero as free usage or use it as a billing/overage control. Diagnostics are attached to the assistant message; Pi's normal cost footer does not show all provenance.
- Custom fetch, deferred inference, provider-level retries and custom headers other than `traceparent` are unsupported. Pi owns retry policy. Arbitrary provider/model migrations are not native replay parity claims.

## Configuration

No token configuration is required. Optional process settings:

- `PI_CLAUDE_CODE_COMMAND`: official CLI executable path.
- `PI_CLAUDE_CODE_CONFIG_DIR`: alternate native CLI configuration directory.
- `PI_CLAUDE_CODE_PYTHON`: Python executable path.
- `PI_CLAUDE_CODE_TELEMETRY=false`: suppress the transport's nonessential CLI traffic. The default permits it. Suppression may force model discovery to use the pinned catalog.

The CLI's `CLAUDE_CONFIG_DIR` is also honored. Process settings do not copy or migrate a login.

## Verify

```sh
pnpm check
pnpm acceptance       # Real Pi + CLI, synthetic auth, owned loopback peer, no Anthropic inference
pnpm acceptance:live  # Real subscription requests; requires your existing native sign-in
```

The deterministic scenario covers a Pi-owned write, tool-result replay, session restart, refusal safety, cache TTL usage and malformed optional accounting. The opt-in live scenario combines attachment recognition, a durable write and final text, observes provider hooks, then aborts an active generation and checks captured process exits. It disables retries and deletes only its own ephemeral Pi/workspace state.

Each run writes a candidate/version-bound receipt under `.artifacts/`, including failures. Paid/live requests are never a fallback for a synthetic failure. The CI definition runs only the deterministic check; it is not proof of real subscription access. The tested runner versions are pinned there. Broader Pi, CLI, Python or OS compatibility requires fresh receipts.

## Transport ownership

The vendored MIT transport comes from Nous Research. The build also inlines Pi's pinned transcript normalization helper while keeping host SDK modules external. Original revisions/hashes are in [`vendor/source.json`](vendor/source.json); local changes are recorded in [`vendor/PATCHES.md`](vendor/PATCHES.md). Preserve the upstream notices in `vendor/transport/LICENSE`, `vendor/LICENSE.hermes-core` and `vendor/LICENSE.pi-ai` when redistributing.
