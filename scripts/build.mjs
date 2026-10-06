import { build } from "esbuild";

const result = await build({
  entryPoints: ["src/index.ts"], outfile: "dist/index.js",
  bundle: true, platform: "node", format: "esm", target: "node22", metafile: true,
  plugins: [{
    name: "pi-host-modules",
    setup(builder) {
      // Package-wide externals also exclude private subpaths that Pi cannot resolve.
      builder.onResolve({ filter: /^@earendil-works\/(?:pi-coding-agent|pi-ai(?:\/providers\/all)?)$/ },
        ({ path }) => ({ path, external: true }));
    },
  }],
});
const unexpected = Object.keys(result.metafile.inputs).filter((path) => path.includes("node_modules/") &&
  !path.endsWith("@earendil-works/pi-ai/dist/api/transform-messages.js"));
if (unexpected.length) {
  throw new Error(`Build bundled unsupported dependencies: ${unexpected.join(", ")}. Only Pi's pinned transcript helper may be bundled; keep host SDK modules external.`);
}
