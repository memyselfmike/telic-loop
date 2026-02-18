import chalk from "chalk";
function getAppId({
  cliConfig,
  output
}) {
  const hasOldCliConfigFlag = cliConfig && "app" in cliConfig && cliConfig.app && "id" in cliConfig.app, hasNewCliConfigFlag = cliConfig && "deployment" in cliConfig && cliConfig.deployment && "appId" in cliConfig.deployment;
  if (hasOldCliConfigFlag && hasNewCliConfigFlag)
    throw new Error("Found both `app.id` (deprecated) and `deployment.appId` in sanity.cli.js. Please remove the deprecated `app.id`.");
  const appId = hasOldCliConfigFlag ? cliConfig.app?.id : cliConfig?.deployment?.appId;
  return hasOldCliConfigFlag && output?.warn(chalk.yellow(`The \`app.id\` config has moved to \`deployment.appId\`.
Please update \`sanity.cli.ts\` or \`sanity.cli.js\` and move:
${chalk.red(`app: {id: "${appId}", ... }`)}
to
${chalk.green(`deployment: {appId: "${appId}", ... }`)})
`)), appId;
}
export {
  getAppId
};
//# sourceMappingURL=getAppId.js.map
