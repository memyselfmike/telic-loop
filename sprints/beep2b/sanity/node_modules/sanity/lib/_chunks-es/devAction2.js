import path from "node:path";
import chalk from "chalk";
import logSymbols from "log-symbols";
import semver from "semver";
import { version } from "vite";
import { hideBin } from "yargs/helpers";
import yargs from "yargs/yargs";
import { isInteractive, debug as debug$2 } from "./_internal.js";
import { debug as debug$1, writeSanityRuntime, getViteConfig, extendViteConfigWithUserConfig } from "./runtime.js";
import { checkStudioDependencyVersions, checkRequiredDependencies, upgradePackages, getPackageManagerChoice } from "./upgradePackages.js";
import { shouldAutoUpdate, compareDependencyVersions } from "./shouldAutoUpdate.js";
import { getAppId } from "./getAppId.js";
import { gracefulServerDeath, getSharedServerConfig } from "./servers.js";
import { getTimer } from "./timing.js";
async function startDevServer(options) {
  const {
    cwd,
    httpPort,
    httpHost,
    basePath,
    reactStrictMode,
    vite: extendViteConfig,
    reactCompiler,
    entry,
    isApp,
    typegen,
    telemetryLogger,
    schemaExtraction
  } = options;
  debug$1("Writing Sanity runtime files"), await writeSanityRuntime({
    cwd,
    reactStrictMode,
    watch: !0,
    basePath,
    entry,
    isApp
  }), debug$1("Resolving vite config");
  const mode = "development";
  let viteConfig = await getViteConfig({
    basePath,
    mode: "development",
    server: {
      port: httpPort,
      host: httpHost
    },
    cwd,
    reactCompiler,
    isApp,
    typegen,
    telemetryLogger,
    schemaExtraction
  });
  extendViteConfig && (viteConfig = await extendViteConfigWithUserConfig({
    command: "serve",
    mode
  }, viteConfig, extendViteConfig)), debug$1("Creating vite server");
  const {
    createServer
  } = await import("vite"), server = await createServer(viteConfig);
  return debug$1("Listening on specified port"), await server.listen(), {
    server,
    close: () => server.close()
  };
}
const debug = debug$2.extend("dev"), baseUrl = process.env.SANITY_INTERNAL_ENV === "staging" ? "https://sanity.work" : "https://sanity.io", getDefaultDashboardURL = ({
  organizationId,
  url
}) => `${baseUrl}/@${organizationId}?${new URLSearchParams({
  dev: url
}).toString()}`, getDashboardURL = async ({
  fetchFn = globalThis.fetch,
  timeout = 5e3,
  organizationId,
  url
}) => {
  const abortController = new AbortController(), timer = setTimeout(() => abortController.abort(), timeout);
  try {
    const queryParams = new URLSearchParams({
      organizationId,
      url
    }), res = await fetchFn(`${baseUrl}/api/dashboard/mode/development/resolve-url?${queryParams.toString()}`, {
      signal: abortController.signal
    });
    return res.ok ? (await res.json()).url : (debug(`Failed to fetch dashboard URL: ${res.statusText}`), getDefaultDashboardURL({
      organizationId,
      url
    }));
  } catch (err) {
    return debug(`Failed to fetch dashboard URL: ${err.message}`), getDefaultDashboardURL({
      organizationId,
      url
    });
  } finally {
    clearTimeout(timer);
  }
}, getDashboardAppURL = async ({
  organizationId,
  httpHost = "localhost",
  httpPort = 3333
}) => await getDashboardURL({
  organizationId,
  url: `http://${httpHost}:${httpPort}`
});
function parseCliFlags(args) {
  return yargs(hideBin(args.argv || process.argv).slice(1)).options("host", {
    type: "string"
  }).options("port", {
    type: "number"
  }).options("auto-updates", {
    type: "boolean"
  }).option("load-in-dashboard", {
    type: "boolean",
    default: !1
  }).argv;
}
async function startSanityDevServer(args, context) {
  const timers = getTimer(), flags = await parseCliFlags(args), {
    output,
    apiClient,
    workDir,
    cliConfig,
    prompt,
    telemetry
  } = context, {
    loadInDashboard
  } = flags;
  if (timers.start("checkStudioDependencyVersions"), await checkStudioDependencyVersions(workDir), timers.end("checkStudioDependencyVersions"), (await checkRequiredDependencies(context)).didInstall)
    return;
  const {
    didInstall,
    installedSanityVersion
  } = await checkRequiredDependencies(context);
  if (didInstall)
    return;
  if (shouldAutoUpdate({
    flags,
    cliConfig
  })) {
    const cleanSanityVersion = semver.parse(installedSanityVersion)?.version;
    if (!cleanSanityVersion)
      throw new Error(`Failed to parse installed Sanity version: ${installedSanityVersion}`);
    const sanityDependencies = [{
      name: "sanity",
      version: cleanSanityVersion
    }, {
      name: "@sanity/vision",
      version: cleanSanityVersion
    }], appId = getAppId({
      cliConfig,
      output
    });
    output.print(`${logSymbols.info} Running with auto-updates enabled`);
    let result;
    try {
      result = await compareDependencyVersions(sanityDependencies, workDir, {
        appId
      });
    } catch (err) {
      console.warn(new Error("Failed to compare local versions against auto-updating versions", {
        cause: err
      }));
    }
    if (result?.length) {
      const message = `The following local package versions are different from the versions currently served at runtime.
When using auto updates, we recommend that you run with the same versions locally as will be used when deploying. 

${result.map((mod) => ` - ${mod.pkg} (local version: ${mod.installed}, runtime version: ${mod.remote})`).join(`
`)} 

`;
      isInteractive ? await prompt.single({
        type: "confirm",
        message: chalk.yellow(`${message}Do you want to upgrade local versions?`),
        default: !0
      }) && await upgradePackages({
        packageManager: (await getPackageManagerChoice(workDir, {
          interactive: !1
        })).chosen,
        packages: result.map((res) => [res.pkg, res.remote])
      }, context) : output.print(chalk.yellow(message));
    }
  }
  cliConfig?.schemaExtraction?.enabled && output.print(`${logSymbols.info} Running dev server with schema extraction enabled`);
  const config = getDevServerConfig({
    flags,
    workDir,
    cliConfig,
    output
  }), projectId = cliConfig?.api?.projectId;
  let organizationId;
  if (loadInDashboard) {
    projectId || (output.error("Project Id is required to load in dashboard"), process.exit(1));
    const client = apiClient({
      requireUser: !0,
      requireProject: !0
    });
    try {
      organizationId = (await client.request({
        uri: `/projects/${projectId}`
      })).organizationId;
    } catch (err) {
      debug(`Failed to get organization Id from project Id: ${err}`), output.error("Failed to get organization Id from project Id"), process.exit(1);
    }
  }
  try {
    const startTime = Date.now(), spinner = output.spinner("Starting dev server").start(), {
      server
    } = await startDevServer({
      ...config,
      telemetryLogger: telemetry
    }), {
      info: loggerInfo
    } = server.config.logger, {
      port
    } = server.config.server, httpHost = config.httpHost || "localhost";
    if (spinner.succeed(), loadInDashboard)
      organizationId || (output.error("Organization Id not found for project"), process.exit(1)), output.print(`Dev server started on ${config.httpPort} port`), output.print("View your app in the Sanity dashboard here:"), output.print(chalk.blue(chalk.underline(await getDashboardAppURL({
        organizationId,
        httpHost: config.httpHost,
        httpPort: config.httpPort
      }))));
    else {
      const startupDuration = Date.now() - startTime, url = `http://${httpHost || "localhost"}:${port}${config.basePath}`;
      loggerInfo(`Sanity Studio using ${chalk.cyan(`vite@${version}`)} ready in ${chalk.cyan(`${Math.ceil(startupDuration)}ms`)} and running at ${chalk.cyan(url)}`);
    }
  } catch (err) {
    debug(`Failed to start dev server: ${err}`), gracefulServerDeath("dev", config.httpHost, config.httpPort, err);
  }
}
function getDevServerConfig({
  flags,
  workDir,
  cliConfig,
  output
}) {
  const configSpinner = output.spinner("Checking configuration files..."), baseConfig = getSharedServerConfig({
    flags: {
      host: flags.host,
      port: flags.port
    },
    workDir,
    cliConfig
  });
  configSpinner.succeed();
  const env = process.env, reactStrictMode = env.SANITY_STUDIO_REACT_STRICT_MODE ? env.SANITY_STUDIO_REACT_STRICT_MODE === "true" : !!cliConfig?.reactStrictMode;
  return env.SANITY_STUDIO_BASEPATH && cliConfig?.project?.basePath && output.warn(`Overriding configured base path (${cliConfig.project.basePath}) with value from environment variable (${env.SANITY_STUDIO_BASEPATH})`), {
    ...baseConfig,
    staticPath: path.join(workDir, "static"),
    reactStrictMode,
    reactCompiler: cliConfig && "reactCompiler" in cliConfig ? cliConfig.reactCompiler : void 0,
    typegen: cliConfig?.typegen,
    schemaExtraction: cliConfig?.schemaExtraction
  };
}
var devAction = /* @__PURE__ */ Object.freeze({
  __proto__: null,
  default: startSanityDevServer,
  getDashboardAppURL,
  getDashboardURL,
  getDevServerConfig
});
export {
  devAction,
  getDashboardAppURL,
  getDevServerConfig,
  startDevServer
};
//# sourceMappingURL=devAction2.js.map
