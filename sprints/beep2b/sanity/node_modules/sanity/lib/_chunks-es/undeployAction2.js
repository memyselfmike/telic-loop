import { debug as debug$1 } from "./_internal.js";
import { getUserApplication, deleteUserApplication } from "./helpers.js";
const debug = debug$1.extend("undeploy");
async function undeployStudioAction(args, context) {
  const {
    apiClient,
    chalk,
    output,
    prompt,
    cliConfig
  } = context, flags = args.extOptions, client = apiClient({
    requireUser: !0,
    requireProject: !0
  }).withConfig({
    apiVersion: "v2024-08-01"
  });
  let spinner = output.spinner("Checking project info").start();
  const appId = cliConfig?.deployment?.appId || void 0, appHost = cliConfig?.studioHost || void 0, userApplication = await getUserApplication({
    client,
    ...appId ? {
      appId
    } : {
      appHost
    }
  });
  if (spinner.succeed(), !userApplication) {
    output.print("Your project has not been assigned a studio hostname"), output.print("or the `studioHost` provided does not exist."), output.print("Nothing to undeploy.");
    return;
  }
  output.print("");
  const isExternal = userApplication.urlType === "external", url = isExternal ? chalk.yellow(userApplication.appHost) : `https://${chalk.yellow(userApplication.appHost)}.sanity.studio`;
  if (!(flags.yes || flags.y)) {
    const confirmMessage = isExternal ? `This will unregister the external studio at ${url}.
  Are you ${chalk.red("sure")} you want to unregister?` : `This will undeploy ${url} and make it unavailable for your users.
  The hostname will be available for anyone to claim.
  Are you ${chalk.red("sure")} you want to undeploy?`;
    if (!await prompt.single({
      type: "confirm",
      default: !1,
      message: confirmMessage.trim()
    }))
      return;
  }
  spinner = output.spinner(isExternal ? "Unregistering studio" : "Undeploying studio").start();
  try {
    await deleteUserApplication({
      client,
      applicationId: userApplication.id,
      appType: "studio"
    }), spinner.succeed();
  } catch (err) {
    throw spinner.fail(), debug("Error undeploying studio", err), err;
  }
  output.print(isExternal ? "External studio unregistered." : `Studio undeploy scheduled. It might take a few minutes before ${url} is unavailable.`);
}
export {
  undeployStudioAction as default
};
//# sourceMappingURL=undeployAction2.js.map
