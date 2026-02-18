import path from "node:path";
import zlib from "node:zlib";
import tar from "tar-fs";
import { getAppId } from "./getAppId.js";
import { shouldAutoUpdate } from "./shouldAutoUpdate.js";
import { getInstalledSanityVersion, dirIsEmptyOrNonExistent, getOrCreateUserApplicationFromConfig, getOrCreateApplication, debug, checkDir, createDeployment } from "./helpers.js";
import buildSanityApp from "./buildAction.js";
async function deployAppAction(args, context) {
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
    cliConfig
  }), installedSanityVersion = await getInstalledSanityVersion(), appId = getAppId({
    cliConfig,
    output
  }), client = apiClient({
    requireUser: !0,
    requireProject: !1
    // custom apps are not project-specific
  }).withConfig({
    apiVersion: "v2024-08-01"
  });
  if (customSourceDir) {
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
  let spinner = output.spinner("Checking application info").start(), userApplication;
  try {
    const configParams = {
      client,
      context,
      spinner
    };
    appId ? userApplication = await getOrCreateUserApplicationFromConfig({
      ...configParams,
      appId,
      appHost: void 0
    }) : userApplication = await getOrCreateApplication(configParams);
  } catch (err) {
    if (err.message) {
      output.error(chalk.red(err.message));
      return;
    }
    throw debug("Error creating user application", err), err;
  }
  if (flags.build) {
    const buildArgs = {
      ...args,
      extOptions: flags,
      argsWithoutOptions: [customSourceDir].filter(Boolean)
    }, {
      didCompile
    } = await buildSanityApp(buildArgs, context, {
      basePath: "/"
    });
    if (!didCompile)
      return;
  }
  spinner = output.spinner("Verifying local content").start();
  try {
    await checkDir(sourceDir), spinner.succeed();
  } catch (err) {
    throw spinner.fail(), debug("Error checking directory", err), err;
  }
  const parentDir = path.dirname(sourceDir), base = path.basename(sourceDir), tarball = tar.pack(parentDir, {
    entries: [base]
  }).pipe(zlib.createGzip());
  spinner = output.spinner("Deploying...").start();
  try {
    if (await createDeployment({
      client,
      applicationId: userApplication.id,
      version: installedSanityVersion,
      isAutoUpdating,
      tarball,
      isSdkApp: !0
    }), spinner.succeed(), output.print(`
Success! Application deployed`), !appId) {
      const example = `Example:
export default defineCliConfig({
  //\u2026
  deployment: {
    ${chalk.cyan`appId: '${userApplication.id}'`},
  },
  //\u2026
})`;
      output.print(`
Add ${chalk.cyan(`appId: '${userApplication.id}'`)}`), output.print("to the `deployment` section in sanity.cli.js or sanity.cli.ts"), output.print("to avoid prompting for appId on next deploy."), output.print(`
${example}`);
    }
  } catch (err) {
    throw spinner.fail(), debug("Error deploying application", err), err;
  }
}
export {
  deployAppAction as default
};
//# sourceMappingURL=deployAction.js.map
