"use strict";
var fs = require("node:fs"), Module = require("node:module"), path = require("node:path"), rxjs = require("rxjs"), sanity = require("sanity"), mockBrowserEnvironment = require("./mockBrowserEnvironment.cjs"), _documentCurrentScript = typeof document < "u" ? document.currentScript : null;
function _interopDefaultCompat(e) {
  return e && typeof e == "object" && "default" in e ? e : { default: e };
}
var fs__default = /* @__PURE__ */ _interopDefaultCompat(fs), path__default = /* @__PURE__ */ _interopDefaultCompat(path);
const require$1 = Module.createRequire(typeof document > "u" ? require("url").pathToFileURL(__filename).href : _documentCurrentScript && _documentCurrentScript.tagName.toUpperCase() === "SCRIPT" && _documentCurrentScript.src || new URL("_chunks-cjs/getStudioWorkspaces.cjs", document.baseURI).href), candidates = ["sanity.config.js", "sanity.config.jsx", "sanity.config.ts", "sanity.config.tsx"];
function getStudioConfig({
  basePath,
  configPath: cfgPath
}) {
  let cleanup;
  try {
    cleanup = mockBrowserEnvironment.mockBrowserEnvironment(basePath);
    let configPath = cfgPath;
    if (configPath && !fs__default.default.existsSync(configPath))
      throw new Error(`Failed to find config at "${cfgPath}"`);
    if (configPath || (configPath = candidates.map((candidate) => path__default.default.join(basePath, candidate)).find((candidate) => fs__default.default.existsSync(candidate))), !configPath)
      throw new Error(`Failed to resolve sanity.config.(js|ts) for base path "${basePath}"`);
    let config;
    try {
      const mod = require$1(configPath);
      config = mod.__esModule && mod.default ? mod.default : mod;
    } catch (err) {
      throw new Error(`Failed to load configuration file "${configPath}"`, {
        cause: err
      });
    }
    if (!config) throw new Error("Configuration did not export expected config shape");
    return Array.isArray(config) ? config : [{
      ...config,
      name: config.name || "default",
      basePath: config.basePath || "/"
    }];
  } finally {
    cleanup?.();
  }
}
async function getStudioWorkspaces(options) {
  let cleanup;
  try {
    cleanup = mockBrowserEnvironment.mockBrowserEnvironment(options.basePath);
    const config = getStudioConfig(options), workspaces = await rxjs.firstValueFrom(sanity.resolveConfig(config));
    if (!workspaces) throw new Error("Failed to resolve configuration");
    return workspaces;
  } finally {
    cleanup?.();
  }
}
exports.getStudioWorkspaces = getStudioWorkspaces;
//# sourceMappingURL=getStudioWorkspaces.cjs.map
