import path from "node:path";
import resolveFrom from "resolve-from";
import { readFile } from "node:fs/promises";
import { performance } from "node:perf_hooks";
function isPackageManifest(item) {
  return typeof item == "object" && item !== null && "name" in item && "version" in item;
}
async function readPackageJson(filePath) {
  try {
    return JSON.parse(await readFile(filePath, "utf8"));
  } catch (err) {
    throw new Error(`Failed to read "${filePath}": ${err.message}`, {
      cause: err
    });
  }
}
async function readPackageManifest(packageJsonPath, defaults = {}) {
  let manifest;
  try {
    manifest = {
      ...defaults,
      ...await readPackageJson(packageJsonPath)
    };
  } catch (err) {
    throw new Error(`Failed to read "${packageJsonPath}": ${err.message}`, {
      cause: err
    });
  }
  if (!isPackageManifest(manifest))
    throw new Error(`Failed to read "${packageJsonPath}": Invalid package manifest`);
  const {
    name,
    version,
    dependencies = {},
    devDependencies = {}
  } = manifest;
  return {
    name,
    version,
    dependencies,
    devDependencies
  };
}
async function readModuleVersion(dir, moduleName) {
  const manifestPath = resolveFrom.silent(dir, path.join(moduleName, "package.json"));
  return manifestPath ? (await readPackageManifest(manifestPath)).version : null;
}
function getTimer() {
  const timings = {}, startTimes = {};
  function start(name) {
    if (typeof startTimes[name] < "u")
      throw new Error(`Timer "${name}" already started, cannot overwrite`);
    startTimes[name] = performance.now();
  }
  function end(name) {
    if (typeof startTimes[name] > "u")
      throw new Error(`Timer "${name}" never started, cannot end`);
    return timings[name] = performance.now() - startTimes[name], timings[name];
  }
  return {
    start,
    end,
    getTimings: () => timings
  };
}
export {
  getTimer,
  readModuleVersion,
  readPackageJson,
  readPackageManifest
};
//# sourceMappingURL=timing.js.map
