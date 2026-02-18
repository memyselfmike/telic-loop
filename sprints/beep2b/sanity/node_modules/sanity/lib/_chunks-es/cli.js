import { loadEnv } from "@sanity/cli";
const envPrefix = "SANITY_STUDIO_", appEnvPrefix = "SANITY_APP_";
function getStudioEnvironmentVariables(options = {}) {
  const {
    prefix = "",
    envFile = !1,
    jsonEncode = !1
  } = options, fullEnv = envFile ? {
    ...process.env,
    ...loadEnv(envFile.mode, envFile.envDir || process.cwd(), [envPrefix])
  } : process.env, studioEnv = {};
  for (const key in fullEnv)
    key.startsWith(envPrefix) && (studioEnv[`${prefix}${key}`] = jsonEncode ? JSON.stringify(fullEnv[key] || "") : fullEnv[key] || "");
  return studioEnv;
}
function getAppEnvironmentVariables(options = {}) {
  const {
    prefix = "",
    envFile = !1,
    jsonEncode = !1
  } = options, fullEnv = envFile ? {
    ...process.env,
    ...loadEnv(envFile.mode, envFile.envDir || process.cwd(), [envPrefix])
  } : process.env, appEnv = {};
  for (const key in fullEnv)
    key.startsWith(appEnvPrefix) && (appEnv[`${prefix}${key}`] = jsonEncode ? JSON.stringify(fullEnv[key] || "") : fullEnv[key] || "");
  return appEnv;
}
export {
  getAppEnvironmentVariables,
  getStudioEnvironmentVariables
};
//# sourceMappingURL=cli.js.map
