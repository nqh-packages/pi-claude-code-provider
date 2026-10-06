# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

This record owns the public presentation of the Claude Code provider for Pi. The provider itself runs inside Pi using Node.js and a Python transport.

## Stack

Astro, approved by the user on 2026-10-06. The website is a static, separate package under `site/`, with minimal browser JavaScript. Local previews do not provision cloud resources. Alchemy owns production deployment to `pi-claude-code.ngoquochuy.com`.

## Users

People with a Claude subscription who want to use it outside Claude Code's agent interface. This provider serves that goal specifically in Pi. A signed-in official Claude Code CLI is a prerequisite, not the primary story. The user clarified this audience and goal on 2026-10-06 after the "Page story" question.

## Product purpose

Reuse the official Claude Code CLI's sign-in for inference while Pi retains its agent loop, tools, approvals, transcript and compaction. Help a prospective user understand the boundary, inspect the source and complete the documented setup.

## Positioning and approved story

People want to choose where they use their Claude subscription rather than be confined to Claude Code's agent interface. This experimental provider brings native Claude Code inference into Pi, where Pi owns the agent loop and tool execution. The official CLI still runs underneath; this is not a claim that the CLI is removed or that every third-party tool is supported.

Their stated goal: "Is there any way to use pi coding agent with the claude max subscription instead of extra usage?" Reported by mario-talentiqa on 2026-04-08 in [Pi discussion #2950](https://github.com/earendil-works/pi/discussions/2950#discussion-9847354).

The quotation establishes an individual goal, not a billing guarantee or widespread demand. The user's explicit story is subscription choice beyond Claude Code, prompted by Anthropic restricting third-party subscription access. Describe those restrictions only where current source evidence supports them. The page will not lead with SDK/JSONL mechanics, promised savings, OAuth workarounds or account-policy assurances.

Drafted by the primary agent; the original audience was checked against the actual discussion and repository by `provider-audience-reviewer`, task `audience-review`, run `run_muwld5fs_z888tp`. The user approved it in the "Page story" question, then superseded the stay-in-Pi framing with the explicit instruction that the story is allowing people to use their Claude Code subscription outside Claude Code because Anthropic has been restricting them. Decision date: 2026-10-06. This approval covers the README and project landing page. The corrected framing was confirmed by `subscription-story-reviewer`, task `corrected-story`, run `run_mux147p4_fc132b`, against the actual discussion, complete README and current [Anthropic authentication policy](https://code.claude.com/docs/en/legal-and-compliance#authentication-and-credential-use). The evidence supports interface choice specifically in Pi, not Anthropic's motives or blanket third-party permission. [Enabled usage credits](https://support.claude.com/en/articles/12429409-manage-usage-credits-for-paid-claude-plans) may incur separate charges.

## Operating context

Users install and sign in to the official Claude Code CLI, build this provider from source, install the local package in Pi and select a `claude-code` model. Native authentication stays with the CLI. Setup instructions and runtime boundaries belong to `README.md`; package prerequisites and entry points belong to `package.json`.

## Capabilities and constraints

- Pi executes tools. The native CLI receives an inert inventory rather than permission to run Pi tools itself.
- The transport validates complete tool batches and suppresses execution on refusal or truncation.
- Native replay, picker initialization and extra-body handling depend on pinned implementation details. CLI updates can break them.
- The adapter does not read credential files or extract OAuth tokens. Prompts, images and tool results go to Claude.
- Account entitlements, plan limits and extra-usage settings remain Anthropic's. Cost values are estimates, not invoices or an overage control.
- Qualified runtime and deterministic checks are described in `README.md#verify`. Do not imply all-platform support, unlimited usage, guaranteed policy compliance or endorsement.

## Brand commitments

The project name is "Claude Code provider for Pi". The public repository is `nqh-packages/pi-claude-code-provider`. The user requested an indie-tool landing page and credit to Hermes.

Credit Hermes as inspiration and explicitly acknowledge the reused MIT transport from [Nous Research's Hermes plugin](https://github.com/NousResearch/hermes-plugin-claude-subscription-directsdk). Preserve attribution to Hermes core and Pi's bundled helper. `vendor/source.json` owns exact provenance; existing license notices remain unchanged.

## Evidence on hand

The source, notices, deterministic acceptance scenario and GitHub CI are public. Existing local receipts qualify specific subscription, tool, replay, cache and cancellation paths, but private receipts and transcripts are not website assets. There are no supplied testimonials, customer counts, performance benchmarks or account-policy guarantees.

## Product principles

- Make the Pi/native CLI ownership boundary understandable.
- Give usable setup instructions before implementation detail.
- Keep experimental and billing limits visible.
- Credit the code actually reused, not just the idea.
- Keep the website separate from provider behavior and packaging.
