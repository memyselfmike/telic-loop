import path from "node:path";
import { fileURLToPath } from "node:url";
import { Worker } from "node:worker_threads";
import zlib from "node:zlib";
import { minutesToMilliseconds } from "date-fns";
import readPkgUp from "read-pkg-up";
import tar from "tar-fs";
import { getAppId } from "./getAppId.js";
import { shouldAutoUpdate } from "./shouldAutoUpdate.js";
import buildSanityStudio from "./buildAction2.js";
import { deploySchemasAction } from "./deploySchemasAction.js";
import { createManifestExtractor } from "./schemaStoreOutStrings.js";
import { getInstalledSanityVersion, dirIsEmptyOrNonExistent, getOrCreateUserApplicationFromConfig, getOrCreateStudio, debug, checkDir, createDeployment } from "./helpers.js";
function extractClientConfig(client) {
  const config = client.config();
  return {
    ...JSON.parse(JSON.stringify(config)),
    // Ensure we use project hostname even if the original config didn't require project
    useProjectHostname: !0,
    // Suppress browser token warning since we mock browser environment in workers
    ignoreBrowserTokenWarning: !0
  };
}
async function deployStudioAction(args, context) {
  const {
    apiClient,
    workDir,
    chalk,
    output,
    prompt,
    cliConfig
  } = context, flags = {
    build: !0,
    ...args.extOptions
  }, customSourceDir = args.argsWithoutOptions[0], sourceDir = path.resolve(process.cwd(), customSourceDir || path.join(workDir, "dist")), isAutoUpdating = shouldAutoUpdate({
    flags,
    cliConfig,
    output
  }), isExternal = !!flags.external, urlType = isExternal ? "external" : "internal", installedSanityVersion = await getInstalledSanityVersion(), client = apiClient({
    requireUser: !0,
    requireProject: !0
  }).withConfig({
    apiVersion: "v2024-08-01"
  });
  if (customSourceDir === "graphql")
    throw new Error("Did you mean `sanity graphql deploy`?");
  if (customSourceDir && !isExternal) {
    let relativeOutput = path.relative(process.cwd(), sourceDir);
    if (relativeOutput[0] !== "." && (relativeOutput = `./${relativeOutput}`), !(await dirIsEmptyOrNonExistent(sourceDir) || await prompt.single({
      type: "confirm",
      message: `"${relativeOutput}" is not empty, do you want to proceed?`,
      default: !1
    }))) {
      output.print("Cancelled.");
      return;
    }
    output.print(`Building to ${relativeOutput}
`);
  }
  let spinner = output.spinner("Checking project info").start();
  const appId = getAppId({
    cliConfig,
    output
  }), configStudioHost = cliConfig && "studioHost" in cliConfig ? cliConfig.studioHost : void 0;
  let userApplication;
  try {
    appId || configStudioHost ? userApplication = await getOrCreateUserApplicationFromConfig({
      client,
      context,
      spinner,
      urlType,
      ...appId ? {
        appId,
        appHost: void 0
      } : {
        appId: void 0,
        appHost: configStudioHost
      }
    }) : userApplication = await getOrCreateStudio({
      client,
      context,
      spinner,
      urlType
    });
  } catch (err) {
    if (err.message) {
      output.error(chalk.red(err.message));
      return;
    }
    throw debug("Error creating user application", err), err;
  }
  const shouldBuild = flags.build && !isExternal;
  if (shouldBuild) {
    const buildArgs = {
      ...args,
      extOptions: flags,
      argsWithoutOptions: [customSourceDir].filter(Boolean)
    }, {
      didCompile
    } = await buildSanityStudio(buildArgs, context, {
      basePath: "/"
    });
    if (!didCompile)
      return;
  }
  (!isExternal || flags["schema-required"]) && await deploySchemasAction({
    // For external, always extract from source (no dist folder)
    "extract-manifest": isExternal ? !0 : shouldBuild,
    "manifest-dir": isExternal ? void 0 : `${sourceDir}/static`,
    "schema-required": flags["schema-required"],
    verbose: flags.verbose
  }, {
    ...context,
    manifestExtractor: createManifestExtractor(context)
  }), spinner = output.spinner("Generating studio manifest").start();
  const clientConfig = extractClientConfig(client), {
    studioManifest
  } = await runGenerateStudioManifestWorker(workDir, clientConfig, installedSanityVersion, spinner);
  if (spinner.succeed("Generated studio manifest"), flags.verbose)
    if (studioManifest)
      for (const workspace of studioManifest.workspaces)
        output.print(chalk.gray(`\u21B3 projectId: ${workspace.projectId}, dataset: ${workspace.dataset}, schemaDescriptorId: ${workspace.schemaDescriptorId}`));
    else
      output.print(chalk.gray("\u21B3 No workspaces found"));
  let tarball;
  if (!isExternal) {
    spinner = output.spinner("Verifying local content").start();
    try {
      await checkDir(sourceDir), spinner.succeed();
    } catch (err) {
      throw spinner.fail(), debug("Error checking directory", err), err;
    }
    const parentDir = path.dirname(sourceDir), base = path.basename(sourceDir);
    tarball = tar.pack(parentDir, {
      entries: [base]
    }).pipe(zlib.createGzip());
  }
  spinner = output.spinner(isExternal ? "Registering studio" : "Deploying to sanity.studio").start();
  try {
    const {
      location
    } = await createDeployment({
      client,
      applicationId: userApplication.id,
      version: installedSanityVersion,
      isAutoUpdating,
      tarball,
      manifest: studioManifest ?? void 0
    });
    if (spinner.succeed(), isExternal ? output.print(`
Success! Studio registered`) : output.print(`
Success! Studio deployed to ${chalk.cyan(location)}`), !appId) {
      const example = `Example:
export default defineCliConfig({
  //\u2026
  deployment: {
    ${chalk.cyan`appId: '${userApplication.id}'`},
  },
  //\u2026
})`;
      output.print(`
Add ${chalk.cyan(`appId: '${userApplication.id}'`)}`), output.print("to the `deployment` section in sanity.cli.js or sanity.cli.ts"), output.print("to avoid prompting for application id on next deploy."), output.print(`
${example}`);
    }
  } catch (err) {
    throw spinner.fail(), debug("Error deploying studio", err), err;
  }
}
const DEPLOY_WORKER_TIMEOUT_MS = minutesToMilliseconds(5), DEPLOY_WORKER_TIMEOUT_HUMAN = "5 minutes", __dirname$1 = path.dirname(fileURLToPath(import.meta.url));
async function runGenerateStudioManifestWorker(workDir, clientConfig, sanityVersion, spinner) {
  const rootPkgPath = readPkgUp.sync({
    cwd: __dirname$1
  })?.path;
  if (!rootPkgPath)
    throw new Error("Could not find root directory for `sanity` package");
  const workerPath = path.join(path.dirname(rootPkgPath), "lib", "_internal", "cli", "threads", "generateStudioManifest.cjs"), worker = new Worker(workerPath, {
    workerData: {
      workDir,
      clientConfig,
      sanityVersion
    },
    env: process.env
  });
  let timedOut = !1;
  const timeoutId = setTimeout(() => {
    timedOut = !0, worker.terminate();
  }, DEPLOY_WORKER_TIMEOUT_MS);
  try {
    const result = await new Promise((resolve, reject) => {
      worker.once("message", (message) => {
        resolve(message);
      }), worker.once("error", reject), worker.once("exit", (exitCode) => {
        if (exitCode !== 0) {
          const error = timedOut ? new Error(`Deploy worker was aborted after ${DEPLOY_WORKER_TIMEOUT_HUMAN}`) : new Error(`Deploy worker exited with code ${exitCode}`);
          reject(error);
        }
      });
    });
    if (result.type === "error")
      throw new Error(result.message);
    return result;
  } catch (err) {
    throw spinner.fail(), debug("Failed to process studio configuration", err), err;
  } finally {
    clearTimeout(timeoutId), await worker.terminate();
  }
}
export {
  deployStudioAction as default
};
//# sourceMappingURL=deployAction2.js.map
