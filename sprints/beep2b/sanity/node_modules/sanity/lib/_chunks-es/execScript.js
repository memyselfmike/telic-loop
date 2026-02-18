import { spawn } from "node:child_process";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import readPkgUp from "read-pkg-up";
import { hideBin } from "yargs/helpers";
import yargs from "yargs/yargs";
const __dirname$1 = path.dirname(fileURLToPath(import.meta.url));
async function parseCliFlags(args) {
  return {
    ...await yargs(hideBin(args.argv || process.argv).slice(2)).option("with-user-token", {
      type: "boolean",
      default: !1
    }).option("mock-browser-env", {
      type: "boolean",
      default: !1
    }).argv,
    script: args.argsWithoutOptions[0]
  };
}
const execScript = async function(args, context) {
  const {
    withUserToken,
    mockBrowserEnv,
    script
  } = await parseCliFlags(args), {
    workDir
  } = context, scriptPath = path.resolve(script || "");
  if (!script)
    throw new Error("SCRIPT must be provided. `sanity exec <script>`");
  if (!await fs.stat(scriptPath).catch(() => !1))
    throw new Error(`${scriptPath} does not exist`);
  const sanityPkgPath = (await readPkgUp({
    cwd: __dirname$1
  }))?.path;
  if (!sanityPkgPath)
    throw new Error("Unable to resolve `sanity` module root");
  const sanityDir = path.dirname(sanityPkgPath), threadsDir = path.join(sanityDir, "lib", "_internal", "cli", "threads"), esbuildPath = path.join(threadsDir, "esbuild.cjs"), browserEnvPath = path.join(threadsDir, "registerBrowserEnv.cjs"), configClientPath = path.join(threadsDir, "configClient.cjs");
  if (!await fs.stat(esbuildPath).catch(() => !1))
    throw new Error("`sanity` module build error: missing threads");
  const baseArgs = mockBrowserEnv ? ["-r", browserEnvPath] : ["-r", esbuildPath], tokenArgs = withUserToken ? ["-r", configClientPath] : [], nodeArgs = [...baseArgs, ...tokenArgs, scriptPath, ...args.extraArguments];
  spawn(process.argv[0], nodeArgs, {
    stdio: "inherit",
    env: {
      ...process.env,
      SANITY_BASE_PATH: workDir
    }
  }).on("close", process.exit);
};
export {
  execScript as default
};
//# sourceMappingURL=execScript.js.map
