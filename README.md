# Claude Code provider for Pi

Prefer Pi's agent interface? This experimental provider connects Pi to your existing Claude Code subscription sign-in. The official Claude Code CLI handles authentication and inference; Pi keeps its agent loop, tools, approvals, transcript and compaction.

[Website](https://pi-claude-code.ngoquochuy.com) · [Source](https://github.com/nqh-packages/pi-claude-code-provider) · [CI](https://github.com/nqh-packages/pi-claude-code-provider/actions/workflows/acceptance.yml)

> **Experimental, with no billing safeguard.** CLI updates can break this adapter. It is not an Anthropic endorsement or an account-policy guarantee. Review [Anthropic's authentication policy](https://code.claude.com/docs/en/legal-and-compliance#authentication-and-credential-use) before use. [Usage credits](https://support.claude.com/en/articles/12429409-manage-usage-credits-for-paid-claude-plans) can incur separate charges when enabled. Pi's cost figures are not subscription charges; this provider cannot cap spending or prevent overages.

## Build and try locally

Install the official [Claude Code CLI](https://code.claude.com/docs/en/setup) and Pi. Use the Pi host versions in `peerDependencies`, Node minimum in `engines` and pnpm version in `packageManager` of [`package.json`](package.json). Python must support the transport; tested CLI/Python prerequisites are pinned in the [CI workflow](.github/workflows/acceptance.yml), with exercised versions recorded in acceptance receipts.

```sh
git clone https://github.com/nqh-packages/pi-claude-code-provider.git
cd pi-claude-code-provider
pnpm install --frozen-lockfile --ignore-scripts
pnpm check
pnpm build

claude auth status
# If signed out, run: claude auth login

pi --offline -e . --model 'claude-code/claude-sonnet-5-5[1m]'
```

Pi loads the generated `dist/index.js`, which Git does not include. Build before local use and after updating the checkout. The command above loads the provider for one invocation without installing it. `--offline` disables Pi's automatic network activity, not inference.

In Pi, `/claude-code-status` checks the CLI sign-in and `/model` lists available `claude-code` routes. Only models with matching Pi capability metadata are advertised. Thinking choices come from the pinned transport and Pi catalog, so mandatory-thinking models do not offer `off`.

### Keep it installed

After building, use Pi's [local-package mechanism](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/packages.md). Pi loads this checkout without copying it.

```sh
pi install /absolute/path/to/pi-claude-code-provider
```

Remove it with `pi remove /absolute/path/to/pi-claude-code-provider`. Installation is optional for the one-invocation command above.

## How it works

```text
Pi history + tool inventory
            │
     TypeScript provider
            │ JSONL
     Python transport
            │
     Official Claude Code CLI · auth + inference ──► Claude
            │
     Complete response / tool call
            │
     Pi executes the tool ──► Pi sends its result
```

## Boundaries

- **CLI compatibility.** Official [headless CLI flags](https://code.claude.com/docs/en/cli-reference) and Pi provider registration are public interfaces. Native-history replay, initialization/picker handling and `CLAUDE_CODE_EXTRA_BODY` are pinned implementation details, not documented public contracts. CLI updates can break them.
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
```

The opt-in live check makes real subscription requests. Run it only when you authorize inference with your existing native sign-in.

```sh
pnpm acceptance:live
```

The deterministic scenario covers a Pi-owned write, tool-result replay, session restart, refusal safety, cache TTL usage and malformed optional accounting. The opt-in live scenario combines attachment recognition, a durable write and final text, observes provider hooks, then aborts an active generation and checks captured process exits. It disables retries and deletes only its own ephemeral Pi/workspace state.

Each run writes a candidate/version-bound receipt under `.artifacts/`, including failures. Paid/live requests are never a fallback for a synthetic failure. The CI definition runs only the deterministic check; it is not proof of real subscription access. The tested runner versions are pinned there. Broader Pi, CLI, Python or OS compatibility requires fresh receipts.

## Credits and provenance

Inspired by Nous Research's [Hermes Claude subscription plugin](https://github.com/NousResearch/hermes-plugin-claude-subscription-directsdk), this provider reuses its MIT-licensed Python transport. It also reuses schema-sanitizer and reasoning-effort helpers from [Hermes core](https://github.com/NousResearch/hermes-agent). The build inlines Pi's pinned [`transformMessages` transcript normalization helper](https://github.com/earendil-works/pi/blob/main/packages/ai/src/api/transform-messages.ts) while keeping host SDK modules external.

[`vendor/source.json`](vendor/source.json) owns the original revisions and hashes; [`vendor/PATCHES.md`](vendor/PATCHES.md) records local changes. Preserve the MIT notices for the [transport](vendor/transport/LICENSE), [Hermes core helpers](vendor/LICENSE.hermes-core) and [Pi helper](vendor/LICENSE.pi-ai) when redistributing.
