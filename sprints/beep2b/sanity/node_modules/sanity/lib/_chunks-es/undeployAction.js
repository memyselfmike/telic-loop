import { debug as debug$1 } from "./_internal.js";
import { getAppId } from "./getAppId.js";
import { getUserApplication, deleteUserApplication } from "./helpers.js";
const debug = debug$1.extend("undeploy");
async function undeployAppAction(_, context) {
  const {
    apiClient,
    chalk,
    output,
    prompt,
    cliConfig
  } = context, client = apiClient({
    requireUser: !0,
    requireProject: !1
  }).withConfig({
    apiVersion: "v2024-08-01"
  });
  let spinner = output.spinner("Checking application info").start();
  const appId = getAppId({
    cliConfig,
    output
  });
  if (!appId) {
    spinner.fail(), output.print("No application ID provided."), output.print("Please set id in `app` in sanity.cli.js or sanity.cli.ts."), output.print("Nothing to undeploy.");
    return;
  }
  const userApplication = await getUserApplication({
    client,
    appId,
    isSdkApp: !0
  });
  if (spinner.succeed(), !userApplication) {
    spinner.fail(), output.print("Application with the given ID does not exist."), output.print("Nothing to undeploy.");
    return;
  }
  if (output.print(""), !!await prompt.single({
    type: "confirm",
    default: !1,
    message: `This will undeploy the following application:

    Title: ${chalk.yellow(userApplication.title)}
    ID:    ${chalk.yellow(userApplication.id)}

  The application will no longer be available for any of your users if you proceed.

  Are you ${chalk.red("sure")} you want to undeploy?`.trim()
  })) {
    spinner = output.spinner("Undeploying application").start();
    try {
      await deleteUserApplication({
        client,
        applicationId: userApplication.id,
        appType: "coreApp"
      }), spinner.succeed();
    } catch (err) {
      throw spinner.fail(), debug("Error undeploying application", err), err;
    }
    output.print(`Application undeploy scheduled. It might take a few minutes before ${chalk.yellow(userApplication.title)} is unavailable.`);
  }
}
export {
  undeployAppAction as default
};
//# sourceMappingURL=undeployAction.js.map
