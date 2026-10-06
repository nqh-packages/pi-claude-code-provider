import * as Alchemy from "alchemy";
import * as Cloudflare from "alchemy/Cloudflare";
import * as Effect from "effect/Effect";

export default Alchemy.Stack(
  "PiClaudeCodeWebsite",
  {
    providers: Cloudflare.providers(),
    state: Alchemy.localState(),
  },
  Effect.gen(function* () {
    const website = yield* Cloudflare.Workers.Worker("Website", {
      assets: { directory: "./dist" },
      domain: "pi-claude-code.ngoquochuy.com",
      workersDev: false,
    });
    return { url: website.url };
  }),
);
