# Project website

Static Astro presentation for the provider. `src/pages/index.astro` owns the page, and `alchemy.run.ts` owns its Cloudflare Worker, assets and custom domain. Provider usage and runtime limits belong to the [root README](../README.md).

## Local preview

From the repository root:

```sh
pnpm install --frozen-lockfile --ignore-scripts
pnpm --dir site dev
```

Development binds to loopback and does not provision cloud resources. For the compiled page:

```sh
pnpm --dir site build
pnpm --dir site preview
```

## Production deployment

Alchemy uses the `pi-claude-code-site` authentication profile and the explicit `prod` stage. Connect the Cloudflare account that owns the active `ngoquochuy.com` zone through Alchemy's supported profile flow:

```sh
cd site
pnpm exec alchemy profile create pi-claude-code-site
pnpm exec alchemy profile edit --profile pi-claude-code-site --add Cloudflare
```

Create the profile only if it does not exist. For OAuth, select only the permissions needed for Workers, custom domains, zone/DNS inspection and account selection. Review the browser consent before approving. Do not paste credentials into source or command arguments.

Alchemy normally disables interactive prompts in agent environments. If an actual interactive terminal is incorrectly detected, its supported `ALCHEMY_TUI=1` override enables the normal prompt flow. Browser authorization is still required.

Build and inspect the plan before publishing:

```sh
pnpm build
pnpm plan
pnpm run deploy
```

The assets-only Worker serves `dist/`. Its custom domain manages DNS and TLS; there is no separate DNS script or Astro server adapter. Workers.dev and version-preview URLs are disabled. Existing DNS records or another Worker's domain attachment must be investigated rather than adopted or overwritten.

`Alchemy.localState()` keeps ownership under ignored `.alchemy/state/`. Preserve a private backup of that state before moving deployment to another checkout or machine. Do not use `--adopt`, rename the stack, or destroy resources to work around missing state. This setup has no cloud-backed development environment or deployment credentials in CI.

After deployment, open `https://pi-claude-code.ngoquochuy.com`, follow the install link, and check the copy control and mobile layout. Confirm the actual served page, styles and fonts rather than relying only on the deploy command's exit code.
