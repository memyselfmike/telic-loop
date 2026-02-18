import { createHash } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve, join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Worker } from "node:worker_threads";
import { minutesToMilliseconds } from "date-fns";
import readPkgUp from "read-pkg-up";
import { readModuleVersion, getTimer } from "./timing.js";
const __dirname$1 = dirname(fileURLToPath(import.meta.url)), MANIFEST_FILENAME = "create-manifest.json", SCHEMA_FILENAME_SUFFIX = ".create-schema.json", TOOLS_FILENAME_SUFFIX = ".create-tools.json", FEATURE_ENABLED_ENV_NAME = "SANITY_CLI_EXTRACT_MANIFEST_ENABLED", EXTRACT_MANIFEST_ENABLED = process.env[FEATURE_ENABLED_ENV_NAME] !== "false", EXTRACT_MANIFEST_LOG_ERRORS = process.env.SANITY_CLI_EXTRACT_MANIFEST_LOG_ERRORS === "true", CREATE_TIMER = "create-manifest", EXTRACT_TASK_TIMEOUT_MS = minutesToMilliseconds(2);
async function extractManifestSafe(args, context) {
  if (EXTRACT_MANIFEST_ENABLED)
    try {
      await extractManifest(args, context);
      return;
    } catch (err) {
      return EXTRACT_MANIFEST_LOG_ERRORS && context.output.error(err), err;
    }
}
async function extractManifest(args, context) {
  const {
    output,
    workDir
  } = context, flags = args.extOptions, defaultOutputDir = resolve(join(workDir, "dist")), outputDir = resolve(defaultOutputDir), defaultStaticPath = join(outputDir, "static"), staticPath = flags.path ?? defaultStaticPath, path = join(staticPath, MANIFEST_FILENAME), rootPkgPath = readPkgUp.sync({
    cwd: __dirname$1
  })?.path;
  if (!rootPkgPath)
    throw new Error("Could not find root directory for `sanity` package");
  const timer = getTimer();
  timer.start(CREATE_TIMER);
  const spinner = output.spinner({}).start("Extracting manifest");
  try {
    const workspaceManifests = await getWorkspaceManifests({
      rootPkgPath,
      workDir
    });
    await mkdir(staticPath, {
      recursive: !0
    });
    const workspaceFiles = await writeWorkspaceFiles(workspaceManifests, staticPath), manifest = {
      /**
       * Version history:
       * 1: Initial release.
       * 2: Added tools file.
       * 3. Added studioVersion field.
       */
      version: 3,
      createdAt: (/* @__PURE__ */ new Date()).toISOString(),
      workspaces: workspaceFiles,
      studioVersion: await readModuleVersion(workDir, "sanity")
    };
    await writeFile(path, JSON.stringify(manifest, null, 2));
    const manifestDuration = timer.end(CREATE_TIMER);
    spinner.succeed(`Extracted manifest (${manifestDuration.toFixed()}ms)`);
  } catch (err) {
    throw spinner.fail(err.message), err;
  }
}
async function getWorkspaceManifests({
  rootPkgPath,
  workDir
}) {
  const workerPath = join(dirname(rootPkgPath), "lib", "_internal", "cli", "threads", "extractManifest.cjs"), worker = new Worker(workerPath, {
    workerData: {
      workDir
    },
    env: process.env
  });
  let timeout = !1;
  const timeoutId = setTimeout(() => {
    timeout = !0, worker.terminate();
  }, EXTRACT_TASK_TIMEOUT_MS);
  try {
    return await new Promise((resolveWorkspaces, reject) => {
      const buffer = [];
      worker.addListener("message", (message) => buffer.push(message)), worker.addListener("exit", (exitCode) => {
        exitCode === 0 ? resolveWorkspaces(buffer) : timeout && reject(new Error(`Extract manifest was aborted after ${EXTRACT_TASK_TIMEOUT_MS}ms`));
      }), worker.addListener("error", reject);
    });
  } finally {
    clearTimeout(timeoutId);
  }
}
function writeWorkspaceFiles(manifestWorkspaces, staticPath) {
  const output = manifestWorkspaces.reduce((workspaces, workspace) => [...workspaces, writeWorkspaceFile(workspace, staticPath)], []);
  return Promise.all(output);
}
async function writeWorkspaceFile(workspace, staticPath) {
  const [schemaFilename, toolsFilename] = await Promise.all([createFile(staticPath, workspace.schema, SCHEMA_FILENAME_SUFFIX), createFile(staticPath, workspace.tools, TOOLS_FILENAME_SUFFIX)]);
  return {
    ...workspace,
    schema: schemaFilename,
    tools: toolsFilename
  };
}
const createFile = async (path, content, filenameSuffix) => {
  const stringifiedContent = JSON.stringify(content, null, 2), filename = `${createHash("sha1").update(stringifiedContent).digest("hex").slice(0, 8)}${filenameSuffix}`;
  return await writeFile(join(path, filename), stringifiedContent), filename;
};
export {
  MANIFEST_FILENAME,
  extractManifestSafe
};
//# sourceMappingURL=extractManifestAction.js.map
