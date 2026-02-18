import fs from "node:fs/promises";
import path from "node:path";
import { PassThrough } from "node:stream";
import { fileURLToPath } from "node:url";
import FormData from "form-data";
import { customAlphabet } from "nanoid";
import readPkgUp from "read-pkg-up";
import { determineIsApp, debug as debug$1 } from "./_internal.js";
import { promiseWithResolvers } from "./promiseWithResolvers.js";
const __dirname$1 = path.dirname(fileURLToPath(import.meta.url)), debug = debug$1.extend("deploy");
async function getUserApplication({
  client,
  appHost,
  appId,
  isSdkApp
}) {
  let query;
  const uri = appId ? `/user-applications/${appId}` : "/user-applications";
  isSdkApp ? query = {
    appType: "coreApp"
  } : appId || (query = appHost ? {
    appHost
  } : {
    default: "true"
  });
  try {
    return await client.request({
      uri,
      query
    });
  } catch (e) {
    if (e?.statusCode === 404)
      return null;
    throw debug("Error getting user application", e), e;
  }
}
async function getUserApplications({
  client,
  organizationId
}) {
  const query = organizationId ? {
    organizationId,
    appType: "coreApp"
  } : {
    appType: "studio"
  };
  try {
    return await client.request({
      uri: "/user-applications",
      query
    });
  } catch (e) {
    if (e?.statusCode === 404)
      return null;
    throw debug("Error getting user applications", e), e;
  }
}
function createUserApplication(client, body, organizationId) {
  const query = organizationId ? {
    organizationId,
    appType: "coreApp"
  } : {
    appType: "studio"
  };
  return client.request({
    uri: "/user-applications",
    method: "POST",
    body,
    query
  });
}
async function createExternalStudio({
  client,
  appHost
}) {
  const validationResult = validateUrl(appHost);
  if (validationResult !== !0)
    throw new Error(validationResult);
  const normalizedUrl = normalizeUrl(appHost);
  try {
    return await createUserApplication(client, {
      appHost: normalizedUrl,
      urlType: "external",
      type: "studio"
    });
  } catch (e) {
    throw debug("Error creating external user application", e), [402, 409].includes(e?.statusCode) ? new Error(e?.response?.body?.message || "Bad request", {
      cause: e
    }) : e;
  }
}
async function selectExistingApplication({
  client,
  prompt,
  message,
  createNewLabel,
  organizationId,
  urlType
}) {
  const allUserApplications = await getUserApplications({
    client,
    organizationId
  }), userApplications = urlType ? allUserApplications?.filter((app) => app.urlType === urlType) : allUserApplications;
  if (!userApplications?.length)
    return null;
  const choices = userApplications.map((app) => ({
    value: app.appHost,
    name: app.title ?? app.appHost
  })), selected = await prompt.single({
    message,
    type: "list",
    choices: [...choices, new prompt.Separator(), {
      value: "new",
      name: createNewLabel
    }]
  });
  return selected === "new" ? null : userApplications.find((app) => app.appHost === selected);
}
function validateUrl(url) {
  try {
    const parsed = new URL(url);
    return ["http:", "https:"].includes(parsed.protocol) ? !0 : "URL must start with http:// or https://";
  } catch {
    return "Please enter a valid URL";
  }
}
function normalizeUrl(url) {
  return url.replace(/\/+$/, "");
}
async function getOrCreateStudio({
  client,
  spinner,
  context,
  urlType = "internal"
}) {
  const {
    output,
    prompt
  } = context;
  if (urlType === "external") {
    spinner.succeed();
    const selectedApp2 = await selectExistingApplication({
      client,
      prompt,
      message: "Select existing external studio or create new",
      createNewLabel: "Create new external studio",
      urlType: "external"
    });
    if (selectedApp2)
      return selectedApp2;
    output.print("Enter the URL to your studio.");
    const {
      promise: promise2,
      resolve: resolve2
    } = promiseWithResolvers();
    return await prompt.single({
      type: "input",
      filter: normalizeUrl,
      message: "Studio URL (https://...):",
      validate: async (externalUrl) => {
        try {
          const response = await createExternalStudio({
            client,
            appHost: externalUrl
          });
          return resolve2(response), !0;
        } catch (e) {
          if (e instanceof Error)
            return e.message;
          throw e;
        }
      }
    }), await promise2;
  }
  const existingUserApplication = await getUserApplication({
    client
  });
  if (spinner.succeed(), existingUserApplication)
    return existingUserApplication;
  const selectedApp = await selectExistingApplication({
    client,
    prompt,
    message: "Select existing studio hostname",
    createNewLabel: "Create new studio hostname",
    urlType: "internal"
  });
  if (selectedApp)
    return selectedApp;
  output.print("Your project has not been assigned a studio hostname."), output.print("To deploy your Sanity Studio to our hosted sanity.studio service,"), output.print("you will need one. Please enter the part you want to use.");
  const {
    promise,
    resolve
  } = promiseWithResolvers();
  return await prompt.single({
    type: "input",
    filter: (inp) => inp.replace(/\.sanity\.studio$/i, ""),
    message: "Studio hostname (<value>.sanity.studio):",
    // if a string is returned here, it is relayed to the user and prompt allows
    // the user to try again until this function returns true
    validate: async (appHost) => {
      try {
        const response = await createUserApplication(client, {
          appHost,
          urlType: "internal",
          type: "studio"
        });
        return resolve(response), !0;
      } catch (e) {
        if ([402, 409].includes(e?.statusCode))
          return e?.response?.body?.message || "Bad request";
        throw debug("Error creating user application", e), e;
      }
    }
  }), await promise;
}
async function getOrCreateApplication({
  client,
  context,
  spinner
}) {
  const {
    prompt,
    cliConfig
  } = context, organizationId = cliConfig && "app" in cliConfig && cliConfig.app?.organizationId;
  spinner.succeed();
  const selectedApp = await selectExistingApplication({
    client,
    prompt,
    message: "Select an existing deployed application",
    createNewLabel: "Create new deployed application",
    organizationId: organizationId || void 0,
    urlType: "internal"
  });
  if (selectedApp)
    return selectedApp;
  const title = await prompt.single({
    type: "input",
    message: "Enter a title for your application:",
    validate: (input) => input.length > 0 || "Title is required"
  }), {
    promise,
    resolve,
    reject
  } = promiseWithResolvers(), tryCreateApp = async () => {
    const appHost = (() => {
      const firstChar = customAlphabet("abcdefghijklmnopqrstuvwxyz", 1)(), rest = customAlphabet("abcdefghijklmnopqrstuvwxyz0123456789", 11)();
      return `${firstChar}${rest}`;
    })();
    try {
      const response2 = await createUserApplication(client, {
        appHost,
        urlType: "internal",
        title,
        type: "coreApp"
      }, organizationId || void 0);
      return resolve(response2), !0;
    } catch (e) {
      if ([402, 409].includes(e?.statusCode))
        return debug("App host taken, retrying with new host"), tryCreateApp();
      throw debug("Error creating core application", e), reject(e), e;
    }
  };
  spinner.start("Creating application"), await tryCreateApp();
  const response = await promise;
  return spinner.succeed(), response;
}
async function getOrCreateStudioFromConfig({
  client,
  context,
  spinner,
  appHost,
  appId
}) {
  const {
    output
  } = context, existingUserApplication = await getUserApplication({
    client,
    appId,
    appHost
  });
  if (spinner.succeed(), existingUserApplication)
    return existingUserApplication;
  if (!appHost)
    throw new Error(`Application not found. Application with id ${appId} does not exist`);
  output.print("Your project has not been assigned a studio hostname."), output.print(`Creating https://${appHost}.sanity.studio`), output.print(""), spinner.start("Creating studio hostname");
  try {
    const response = await createUserApplication(client, {
      appHost,
      urlType: "internal",
      type: "studio"
    });
    return spinner.succeed(), response;
  } catch (e) {
    throw spinner.fail(), [402, 409].includes(e?.statusCode) ? new Error(e?.response?.body?.message || "Bad request", {
      cause: e
    }) : (debug("Error creating user application from config", e), e);
  }
}
async function getOrCreateAppFromConfig({
  client,
  context,
  spinner,
  appHost,
  appId
}) {
  const {
    output,
    cliConfig
  } = context;
  if (appId) {
    const existingUserApplication = await getUserApplication({
      client,
      appId,
      appHost,
      isSdkApp: determineIsApp(cliConfig)
    });
    if (spinner.succeed(), existingUserApplication)
      return existingUserApplication;
  }
  return output.print("The id provided in your configuration is not recognized."), output.print("Checking existing applications..."), getOrCreateApplication({
    client,
    context,
    spinner
  });
}
async function getOrCreateUserApplicationFromConfig(options) {
  const {
    client,
    context,
    spinner,
    appId,
    appHost,
    urlType
  } = options, {
    output
  } = context;
  if (determineIsApp(context.cliConfig))
    return getOrCreateAppFromConfig(options);
  if (urlType === "external") {
    if (appId) {
      const existingUserApplication2 = await getUserApplication({
        client,
        appId
      });
      if (spinner.succeed(), existingUserApplication2)
        return existingUserApplication2;
      throw new Error(`Application not found. Application with id ${appId} does not exist`);
    }
    if (!appHost)
      throw new Error("External deployment requires studioHost to be set in sanity.cli.ts with a full URL, or deployment.appId to reference an existing application");
    const validationResult = validateUrl(appHost);
    if (validationResult !== !0)
      throw new Error(validationResult);
    const normalizedUrl = normalizeUrl(appHost), existingUserApplication = await getUserApplication({
      client,
      appHost: normalizedUrl
    });
    if (spinner.succeed(), existingUserApplication)
      return existingUserApplication;
    output.print(`Registering external studio at ${normalizedUrl}`), output.print(""), spinner.start("Registering external studio URL");
    try {
      const response = await createExternalStudio({
        client,
        appHost: normalizedUrl
      });
      return spinner.succeed(), response;
    } catch (e) {
      throw spinner.fail(), e;
    }
  }
  if (!appId && !appHost)
    throw new Error("Studio was detected, but neither appId or appHost (deprecated) found in CLI config");
  return getOrCreateStudioFromConfig(options);
}
async function createDeployment({
  client,
  tarball,
  applicationId,
  isAutoUpdating,
  version,
  isSdkApp,
  manifest
}) {
  const formData = new FormData();
  return formData.append("isAutoUpdating", isAutoUpdating.toString()), formData.append("version", version), manifest && formData.append("manifest", JSON.stringify(manifest)), tarball && formData.append("tarball", tarball, {
    contentType: "application/gzip",
    filename: "app.tar.gz"
  }), client.request({
    uri: `/user-applications/${applicationId}/deployments`,
    method: "POST",
    headers: formData.getHeaders(),
    body: formData.pipe(new PassThrough()),
    query: isSdkApp ? {
      appType: "coreApp"
    } : {
      appType: "studio"
    }
  });
}
async function deleteUserApplication({
  applicationId,
  client,
  appType
}) {
  await client.request({
    uri: `/user-applications/${applicationId}`,
    query: {
      appType
    },
    method: "DELETE"
  });
}
async function getInstalledSanityVersion() {
  const sanityPkgPath = (await readPkgUp({
    cwd: __dirname$1
  }))?.path;
  if (!sanityPkgPath)
    throw new Error("Unable to resolve `sanity` module root");
  const pkg = JSON.parse(await fs.readFile(sanityPkgPath, "utf-8"));
  if (typeof pkg?.version != "string")
    throw new Error("Unable to find version of `sanity` module");
  return pkg.version;
}
async function dirIsEmptyOrNonExistent(sourceDir) {
  try {
    if (!(await fs.stat(sourceDir)).isDirectory())
      throw new Error(`Directory ${sourceDir} is not a directory`);
  } catch (err) {
    if (err.code === "ENOENT")
      return !0;
    throw err;
  }
  return (await fs.readdir(sourceDir)).length === 0;
}
async function checkDir(sourceDir) {
  try {
    if (!(await fs.stat(sourceDir)).isDirectory())
      throw new Error(`Directory ${sourceDir} is not a directory`);
  } catch (err) {
    throw err.code === "ENOENT" ? new Error(`Directory "${sourceDir}" does not exist`) : err;
  }
  try {
    await fs.stat(path.join(sourceDir, "index.html"));
  } catch (err) {
    throw err.code === "ENOENT" ? new Error([`"${sourceDir}/index.html" does not exist -`, "[SOURCE_DIR] must be a directory containing", 'a Sanity studio built using "sanity build"'].join(" ")) : err;
  }
}
export {
  checkDir,
  createDeployment,
  debug,
  deleteUserApplication,
  dirIsEmptyOrNonExistent,
  getInstalledSanityVersion,
  getOrCreateApplication,
  getOrCreateStudio,
  getOrCreateUserApplicationFromConfig,
  getUserApplication
};
//# sourceMappingURL=helpers.js.map
