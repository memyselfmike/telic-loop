import fs from "node:fs";
import path from "node:path";
import resolveFrom from "resolve-from";
import semver from "semver";
import { createExternalFromImportMap } from "./runtime.js";
import chalk from "chalk";
import logSymbols from "log-symbols";
const VENDOR_DIR = "vendor", VENDOR_IMPORTS = {
  react: {
    "^19.2.0": {
      ".": "./cjs/react.production.js",
      "./jsx-runtime": "./cjs/react-jsx-runtime.production.js",
      "./jsx-dev-runtime": "./cjs/react-jsx-dev-runtime.production.js",
      "./compiler-runtime": "./cjs/react-compiler-runtime.production.js",
      "./package.json": "./package.json"
    }
  },
  "react-dom": {
    "^19.2.0": {
      ".": "./cjs/react-dom.production.js",
      "./client": "./cjs/react-dom-client.production.js",
      "./server": "./cjs/react-dom-server-legacy.browser.production.js",
      "./server.browser": "./cjs/react-dom-server-legacy.browser.production.js",
      "./static": "./cjs/react-dom-server.browser.production.js",
      "./static.browser": "./cjs/react-dom-server.browser.production.js",
      "./package.json": "./package.json"
    }
  },
  "styled-components": {
    "^6.1.0": {
      ".": "./dist/styled-components.browser.esm.js",
      "./package.json": "./package.json"
    }
  }
};
async function buildVendorDependencies({
  cwd,
  outputDir,
  basePath
}) {
  const dir = path.relative(process.cwd(), path.resolve(cwd)), entry = {}, imports = {};
  for (const [packageName, ranges] of Object.entries(VENDOR_IMPORTS)) {
    const packageJsonPath = resolveFrom.silent(cwd, path.join(packageName, "package.json"));
    if (!packageJsonPath)
      throw new Error(`Could not find package.json for package '${packageName}' from directory '${dir}'. Is it installed?`);
    let packageJson;
    try {
      packageJson = JSON.parse(await fs.promises.readFile(packageJsonPath, "utf-8"));
    } catch (e) {
      const message = `Could not read package.json for package '${packageName}' from directory '${dir}'`;
      throw typeof e?.message == "string" ? (e.message = `${message}: ${e.message}`, e) : new Error(message, {
        cause: e
      });
    }
    const version = semver.coerce(packageJson.version)?.version;
    if (!version)
      throw new Error(`Could not parse version '${packageJson.version}' from '${packageName}'`);
    const sortedRanges = Object.keys(ranges).sort((range1, range2) => {
      const min1 = semver.minVersion(range1), min2 = semver.minVersion(range2);
      if (!min1) throw new Error(`Could not parse range '${range1}'`);
      if (!min2) throw new Error(`Could not parse range '${range2}'`);
      return semver.rcompare(min1.version, min2.version);
    }), matchedRange = sortedRanges.find((range) => semver.satisfies(version, range));
    if (!matchedRange) {
      const min = semver.minVersion(sortedRanges[sortedRanges.length - 1]);
      throw min ? semver.gt(min.version, version) ? new Error(`Package '${packageName}' requires at least ${min.version}.`) : new Error(`Version '${version}' of package '${packageName}' is not supported yet.`) : new Error(`Could not find a minimum version for package '${packageName}'`);
    }
    const subpaths = ranges[matchedRange];
    for (const [subpath, relativeEntryPoint] of Object.entries(subpaths)) {
      const packagePath = path.dirname(packageJsonPath), entryPoint = resolveFrom.silent(packagePath, relativeEntryPoint);
      if (!entryPoint)
        throw new Error(`Failed to resolve entry point '${path.join(packageName, relativeEntryPoint)}'. `);
      const specifier = path.posix.join(packageName, subpath), chunkName = path.posix.join(packageName, path.relative(packageName, specifier) || "index");
      entry[chunkName] = entryPoint, imports[specifier] = path.posix.join("/", basePath, VENDOR_DIR, `${chunkName}.mjs`);
    }
  }
  const {
    build
  } = await import("vite");
  let buildResult = await build({
    // Define a custom cache directory so that sanity's vite cache
    // does not conflict with any potential local vite projects
    cacheDir: "node_modules/.sanity/vite-vendor",
    root: cwd,
    configFile: !1,
    logLevel: "silent",
    appType: "custom",
    mode: "production",
    define: {
      "process.env.NODE_ENV": JSON.stringify("production")
    },
    build: {
      commonjsOptions: {
        strictRequires: "auto"
      },
      minify: !0,
      emptyOutDir: !1,
      // Rely on CLI to do this
      outDir: path.join(outputDir, VENDOR_DIR),
      lib: {
        entry,
        formats: ["es"]
      },
      rollupOptions: {
        external: createExternalFromImportMap({
          imports
        }),
        output: {
          entryFileNames: "[name]-[hash].mjs",
          chunkFileNames: "[name]-[hash].mjs",
          exports: "named",
          format: "es"
        },
        treeshake: {
          preset: "recommended"
        }
      }
    }
  });
  buildResult = Array.isArray(buildResult) ? buildResult : [buildResult];
  const hashedImports = {}, output = buildResult.flatMap((i) => i.output);
  for (const chunk of output)
    if (chunk.type !== "asset")
      for (const [specifier, originalPath] of Object.entries(imports))
        originalPath.endsWith(`${chunk.name}.mjs`) && (hashedImports[specifier] = path.posix.join("/", basePath, VENDOR_DIR, chunk.fileName));
  return hashedImports;
}
function formatSize(bytes) {
  return chalk.cyan(`${(bytes / 1024).toFixed()} kB`);
}
function formatModuleSizes(modules) {
  const lines = [];
  for (const mod of modules)
    lines.push(` - ${formatModuleName(mod.name)} (${formatSize(mod.renderedLength)})`);
  return lines.join(`
`);
}
function formatModuleName(modName) {
  const delimiter = "/node_modules/", nodeIndex = modName.lastIndexOf(delimiter);
  return nodeIndex === -1 ? modName : modName.slice(nodeIndex + delimiter.length);
}
function sortModulesBySize(chunks) {
  return chunks.flatMap((chunk) => chunk.modules).sort((modA, modB) => modB.renderedLength - modA.renderedLength);
}
const baseUrl = process.env.SANITY_INTERNAL_ENV === "staging" ? "https://www.sanity.work" : "https://www.sanity.io";
function warnAboutMissingAppId({
  appType,
  projectId,
  output,
  cliConfigPath
}) {
  const manageUrl = `${baseUrl}/manage${projectId ? `/project/${projectId}/studios` : ""}`, cliConfigFile = cliConfigPath ? path.basename(cliConfigPath) : "sanity.cli.js";
  output.print(`${logSymbols.warning} No ${chalk.bold("appId")} configured. This ${appType} will auto-update to the ${chalk.green.bold("latest")} channel. To enable fine grained version selection, head over to ${chalk.cyan(manageUrl)} and add the appId to the ${chalk.bold("deployment")} section in ${chalk.bold(cliConfigFile)}.
        `);
}
export {
  buildVendorDependencies,
  formatModuleSizes,
  sortModulesBySize,
  warnAboutMissingAppId
};
//# sourceMappingURL=warnAboutMissingAppId.js.map
