import chalk from "chalk";
import { hideBin } from "yargs/helpers";
import yargs from "yargs/yargs";
import { getDevServerConfig, startDevServer, getDashboardAppURL } from "./devAction2.js";
import { gracefulServerDeath } from "./servers.js";
function parseCliFlags(args) {
  return yargs(hideBin(args.argv || process.argv).slice(1)).options("host", {
    type: "string"
  }).options("port", {
    type: "number"
  }).options("load-in-dashboard", {
    type: "boolean",
    default: !0
  }).argv;
}
async function startAppDevServer(args, context) {
  const flags = await parseCliFlags(args), {
    output,
    workDir,
    cliConfig
  } = context;
  flags.loadInDashboard || (output.warn("Apps cannot run without the Sanity dashboard"), output.warn("Starting dev server with the --load-in-dashboard flag set to true"));
  let organizationId;
  cliConfig && "app" in cliConfig && cliConfig.app?.organizationId && (organizationId = cliConfig.app.organizationId), organizationId || (output.error("Apps require an organization ID (orgId) specified in your sanity.cli.ts file"), process.exit(1));
  const config = getDevServerConfig({
    flags,
    workDir,
    cliConfig,
    output
  });
  try {
    output.print("Starting dev server");
    const {
      server
    } = await startDevServer({
      ...config,
      isApp: !0
    }), {
      port
    } = server.config.server, httpHost = config.httpHost || "localhost", dashboardAppUrl = await getDashboardAppURL({
      organizationId,
      httpHost,
      httpPort: port
    });
    output.print(`Dev server started on port ${port}`), output.print("View your app in the Sanity dashboard here:"), output.print(chalk.blue(chalk.underline(dashboardAppUrl)));
  } catch (err) {
    gracefulServerDeath("dev", config.httpHost, config.httpPort, err);
  }
}
export {
  startAppDevServer as default
};
//# sourceMappingURL=devAction.js.map
