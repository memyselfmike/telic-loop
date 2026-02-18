import path from "node:path";
import resolveFrom from "resolve-from";
import semver from "semver";
import { readPackageManifest } from "./timing.js";
import chalk from "chalk";
const MODULES_HOST = process.env.SANITY_MODULES_HOST || (process.env.SANITY_INTERNAL_ENV === "staging" ? "https://sanity-cdn.work" : "https://sanity-cdn.com");
function currentUnixTime() {
  return Math.floor(Date.now() / 1e3);
}
function getAutoUpdatesImportMap(packages, options = {}) {
  return Object.fromEntries(packages.flatMap((pkg) => getAppAutoUpdateImportMapForPackage(pkg, options)));
}
function getAppAutoUpdateImportMapForPackage(pkg, options = {}) {
  const moduleUrl = getModuleUrl(pkg, options);
  return [[pkg.name, moduleUrl], [`${pkg.name}/`, `${moduleUrl}/`]];
}
function getModuleUrl(pkg, options = {}) {
  const {
    timestamp = currentUnixTime()
  } = options;
  return options.appId ? getByAppModuleUrl(pkg, {
    appId: options.appId,
    baseUrl: options.baseUrl,
    timestamp
  }) : getLegacyModuleUrl(pkg, {
    timestamp,
    baseUrl: options.baseUrl
  });
}
function getLegacyModuleUrl(pkg, options) {
  const encodedMinVer = encodeURIComponent(`^${pkg.version}`);
  return `${options.baseUrl || MODULES_HOST}/v1/modules/${rewriteScopedPackage(pkg.name)}/default/${encodedMinVer}/t${options.timestamp}`;
}
function getByAppModuleUrl(pkg, options) {
  const encodedMinVer = encodeURIComponent(`^${pkg.version}`);
  return `${options.baseUrl || MODULES_HOST}/v1/modules/by-app/${options.appId}/t${options.timestamp}/${encodedMinVer}/${rewriteScopedPackage(pkg.name)}`;
}
function rewriteScopedPackage(pkgName) {
  if (!pkgName.includes("@"))
    return pkgName;
  const [scope, ...pkg] = pkgName.split("/");
  return `${scope}__${pkg.join("")}`;
}
function getRemoteResolvedVersion(fetchFn, url) {
  return fetchFn(url, {
    method: "HEAD",
    redirect: "manual"
  }).then((res) => {
    if (res.ok || res.status < 400) {
      const resolved = res.headers.get("x-resolved-version");
      if (!resolved)
        throw new Error(`Missing 'x-resolved-version' header on response from HEAD ${url}`);
      return resolved;
    }
    throw new Error(`Unexpected HTTP response: ${res.status} ${res.statusText}`);
  }, (err) => {
    throw new Error(`Failed to fetch remote version for ${url}: ${err.message}`, {
      cause: err
    });
  });
}
async function compareDependencyVersions(packages, workDir, {
  fetchFn = globalThis.fetch
} = {}) {
  const manifest = await readPackageManifest(path.join(workDir, "package.json")), dependencies = {
    ...manifest.dependencies,
    ...manifest.devDependencies
  }, failedDependencies = [];
  for (const pkg of packages) {
    const resolvedVersion = await getRemoteResolvedVersion(fetchFn, getModuleUrl(pkg)), manifestPath = resolveFrom.silent(workDir, path.join(pkg.name, "package.json")), manifestVersion = dependencies[pkg.name], installed = semver.coerce(manifestPath ? semver.parse((await readPackageManifest(manifestPath)).version) : semver.coerce(manifestVersion));
    if (!installed)
      throw new Error(`Failed to parse installed version for ${pkg}`);
    semver.eq(resolvedVersion, installed.version) || failedDependencies.push({
      pkg: pkg.name,
      installed: installed.version,
      remote: resolvedVersion
    });
  }
  return failedDependencies;
}
function shouldAutoUpdate({
  flags,
  cliConfig,
  output
}) {
  if ("auto-updates" in flags) {
    if (output) {
      const flagUsed = flags["auto-updates"] ? "--auto-updates" : "--no-auto-updates";
      output.warn(chalk.yellow(`The ${flagUsed} flag is deprecated for \`deploy\` and \`build\` commands. Set the \`autoUpdates\` option in \`sanity.cli.ts\` or \`sanity.cli.js\` instead.`));
    }
    return !!flags["auto-updates"];
  }
  const hasOldCliConfigFlag = cliConfig && "autoUpdates" in cliConfig, hasNewCliConfigFlag = cliConfig && "deployment" in cliConfig && cliConfig.deployment && "autoUpdates" in cliConfig.deployment;
  if (hasOldCliConfigFlag && hasNewCliConfigFlag)
    throw new Error("Found both `autoUpdates` (deprecated) and `deployment.autoUpdates` in sanity.cli.js. Please remove the deprecated top level `autoUpdates` config.");
  return hasOldCliConfigFlag && output?.warn(chalk.yellow(`The \`autoUpdates\` config has moved to \`deployment.autoUpdates\`.
Please update \`sanity.cli.ts\` or \`sanity.cli.js\` and make the following change:
${chalk.red(`-  autoUpdates: ${cliConfig.autoUpdates},`)}
${chalk.green(`+  deployment: {autoUpdates: ${cliConfig.autoUpdates}},`)}
`)), !!(hasOldCliConfigFlag ? cliConfig.autoUpdates : cliConfig?.deployment?.autoUpdates);
}
export {
  compareDependencyVersions,
  getAutoUpdatesImportMap,
  shouldAutoUpdate
};
//# sourceMappingURL=shouldAutoUpdate.js.map
