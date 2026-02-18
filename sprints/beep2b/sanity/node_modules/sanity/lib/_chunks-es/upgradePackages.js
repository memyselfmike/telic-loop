import path from "node:path";
import execa from "execa";
import oneline from "oneline";
import semver from "semver";
import { peerDependencies } from "./package.js";
import { determineIsApp, isInteractive } from "./_internal.js";
import { readPackageManifest, readModuleVersion, readPackageJson } from "./timing.js";
import { generateHelpUrl } from "./index.js";
import resolveFrom from "resolve-from";
import preferredPM from "preferred-pm";
import which from "which";
const defaultStudioManifestProps = {
  name: "studio",
  version: "1.0.0"
};
async function checkRequiredDependencies(context) {
  if (determineIsApp(context.cliConfig))
    return {
      didInstall: !1,
      installedSanityVersion: ""
    };
  const {
    workDir: studioPath,
    output
  } = context, [studioPackageManifest, installedStyledComponentsVersion, installedSanityVersion] = await Promise.all([await readPackageManifest(path.join(studioPath, "package.json"), defaultStudioManifestProps), await readModuleVersion(studioPath, "styled-components"), await readModuleVersion(studioPath, "sanity")]), wantedStyledComponentsVersionRange = peerDependencies["styled-components"];
  if (!installedSanityVersion)
    throw new Error("Failed to read the installed sanity version.");
  const declaredStyledComponentsVersion = studioPackageManifest.dependencies["styled-components"] || studioPackageManifest.devDependencies["styled-components"];
  if (!declaredStyledComponentsVersion) {
    const [file, ...args] = process.argv;
    return await installDependencies({
      "styled-components": wantedStyledComponentsVersionRange
    }, context), await execa(file, args, {
      cwd: studioPath,
      stdio: "inherit"
    }), {
      didInstall: !0,
      installedSanityVersion
    };
  }
  const isStyledComponentsVersionRangeInCatalog = declaredStyledComponentsVersion.startsWith("catalog:");
  let minDeclaredStyledComponentsVersion = null;
  try {
    minDeclaredStyledComponentsVersion = semver.minVersion(declaredStyledComponentsVersion);
  } catch {
  }
  if (!minDeclaredStyledComponentsVersion && !isStyledComponentsVersionRangeInCatalog)
    throw new Error(oneline`
      Declared dependency \`styled-components\` has an invalid version range:
      \`${declaredStyledComponentsVersion}\`.
    `);
  if (!isStyledComponentsVersionRangeInCatalog && isComparableRange(declaredStyledComponentsVersion) && !semver.satisfies(minDeclaredStyledComponentsVersion, wantedStyledComponentsVersionRange) && output.warn(oneline`
      Declared version of styled-components (${declaredStyledComponentsVersion})
      is not compatible with the version required by sanity (${wantedStyledComponentsVersionRange}).
      This might cause problems!
    `), !installedStyledComponentsVersion)
    throw new Error(oneline`
      Declared dependency \`styled-components\` is not installed - run
      \`npm install\`, \`yarn install\` or \`pnpm install\` to install it before re-running this command.
    `);
  return semver.satisfies(installedStyledComponentsVersion, wantedStyledComponentsVersionRange) || output.warn(oneline`
      Installed version of styled-components (${installedStyledComponentsVersion})
      is not compatible with the version required by sanity (${wantedStyledComponentsVersionRange}).
      This might cause problems!
    `), {
    didInstall: !1,
    installedSanityVersion
  };
}
async function installDependencies(dependencies, context) {
  const {
    output,
    prompt,
    workDir,
    cliPackageManager
  } = context, packages = [];
  output.print("The Sanity studio needs to install missing dependencies:");
  for (const [pkgName, version] of Object.entries(dependencies)) {
    const declaration = `${pkgName}@${version}`;
    output.print(`- ${declaration}`), packages.push(declaration);
  }
  if (!cliPackageManager) {
    output.error("ERROR: Could not determine package manager choice - run `npm install` or equivalent");
    return;
  }
  const {
    getPackageManagerChoice: getPackageManagerChoice2,
    installNewPackages
  } = cliPackageManager, {
    mostOptimal,
    chosen: pkgManager
  } = await getPackageManagerChoice2(workDir, {
    prompt
  });
  mostOptimal && pkgManager !== mostOptimal && output.warn(`WARN: This project appears to be installed with or using ${mostOptimal} - using a different package manager _may_ result in errors.`), await installNewPackages({
    packages,
    packageManager: pkgManager
  }, context);
}
function isComparableRange(range) {
  return /^[\^~]?\d+(\.\d+)?(\.\d+)?$/.test(range);
}
const PACKAGES = [{
  name: "react",
  supported: ["^19.2.2"],
  deprecatedBelow: null
}, {
  name: "react-dom",
  supported: ["^19.2.2"],
  deprecatedBelow: null
}, {
  name: "styled-components",
  supported: ["^6"],
  deprecatedBelow: null
}, {
  name: "@sanity/ui",
  supported: ["^2", "^3"],
  deprecatedBelow: "^3"
}];
async function checkStudioDependencyVersions(workDir) {
  const manifest = await readPackageJson(path.join(workDir, "package.json")), dependencies = {
    ...manifest.dependencies,
    ...manifest.devDependencies
  }, packageInfo = PACKAGES.map(async (pkg) => {
    const dependency = dependencies[pkg.name];
    if (!dependency)
      return !1;
    const manifestPath = resolveFrom.silent(workDir, path.join(pkg.name, "package.json")), installed = semver.coerce(manifestPath ? (await readPackageManifest(manifestPath)).version : dependency.replace(/[\D.]/g, ""));
    if (!installed)
      return !1;
    const supported = pkg.supported.join(" || "), isUntested = !semver.satisfies(installed, supported) && semver.gtr(installed, supported), isUnsupported = !semver.satisfies(installed, supported) && !isUntested, isDeprecated = pkg.deprecatedBelow ? semver.ltr(installed, pkg.deprecatedBelow) : !1;
    return {
      ...pkg,
      installed,
      isUnsupported,
      isDeprecated,
      isUntested
    };
  }), installedPackages = (await Promise.all(packageInfo)).filter((inp) => inp !== !1), unsupported = installedPackages.filter((pkg) => pkg.isUnsupported), deprecated = installedPackages.filter((pkg) => !pkg.isUnsupported && pkg.isDeprecated), untested = installedPackages.filter((pkg) => pkg.isUntested);
  deprecated.length > 0 && console.warn(`
[WARN] The following package versions have been deprecated and should be upgraded:

  ${listPackages(deprecated)}

Support for these will be removed in a future release!

  ${getUpgradeInstructions(deprecated)}
`), untested.length > 0 && console.warn(`
[WARN] The following package versions have not yet been marked as supported:

  ${listPackages(untested)}

You _may_ encounter bugs while using these versions.

  ${getDowngradeInstructions(untested)}
`), unsupported.length > 0 && (console.error(`
[ERROR] The following package versions are no longer supported and needs to be upgraded:

  ${listPackages(unsupported)}

  ${getUpgradeInstructions(unsupported)}
`), process.exit(1));
}
function listPackages(pkgs) {
  return pkgs.map((pkg) => `${pkg.name} (installed: ${pkg.installed}, want: ${pkg.deprecatedBelow || pkg.supported.join(" || ")})`).join(`
  `);
}
function getUpgradeInstructions(pkgs) {
  const inst = pkgs.map((pkg) => {
    const [recommendedVersion] = pkg.supported.concat(pkg.deprecatedBelow || []).map((version) => (semver.coerce(version) || {
      version: ""
    }).version).sort(semver.rcompare);
    return `"${pkg.name}@^${recommendedVersion}"`;
  }).join(" ");
  return `To upgrade, run either:

  npm install ${inst}

  or

  yarn add ${inst}

  or

  pnpm add ${inst}


Read more at ${generateHelpUrl("upgrade-packages")}`;
}
function getDowngradeInstructions(pkgs) {
  const inst = pkgs.map((pkg) => {
    const [highestSupported] = pkg.supported.map((version) => (semver.coerce(version) || {
      version: ""
    }).version).sort(semver.rcompare);
    return `"${pkg.name}@^${highestSupported}"`;
  }).join(" ");
  return `To downgrade, run either:

  yarn add ${inst}

  or

  npm install ${inst}

  or

  pnpm install ${inst}`;
}
const EXPERIMENTAL = ["bun"];
async function getPackageManagerChoice(workDir, options) {
  const rootDir = workDir || process.cwd(), preferred = (await preferredPM(rootDir))?.name;
  if (preferred && await hasCommand(preferred, rootDir))
    return {
      chosen: preferred,
      mostOptimal: preferred
    };
  const mostLikelyPM = await getMostLikelyInstalledPackageManager(rootDir);
  if (!(typeof options.interactive == "boolean" ? options.interactive : isInteractive))
    return {
      chosen: mostLikelyPM || await getFallback(rootDir),
      mostOptimal: preferred
    };
  if (!("prompt" in options))
    throw new Error("Must pass `prompt` when in interactive mode");
  const messageSuffix = preferred ? ` (preferred is ${preferred}, but is not installed)` : "", installed = await getAvailablePackageManagers(rootDir);
  return {
    chosen: await options.prompt.single({
      type: "list",
      choices: installed.map((pm) => ({
        value: pm,
        name: EXPERIMENTAL.includes(pm) ? `${pm} (experimental)` : pm
      })),
      default: preferred || mostLikelyPM,
      message: `Package manager to use for installing dependencies?${messageSuffix}`
    }),
    mostOptimal: preferred
  };
}
async function getFallback(cwd) {
  return await hasNpmInstalled(cwd) ? "npm" : await hasYarnInstalled(cwd) ? "yarn" : await hasPnpmInstalled(cwd) ? "pnpm" : await hasBunInstalled(cwd) ? "bun" : "manual";
}
async function getAvailablePackageManagers(cwd) {
  const [npm, yarn, pnpm, bun] = await Promise.all([hasNpmInstalled(cwd), hasYarnInstalled(cwd), hasPnpmInstalled(cwd), hasBunInstalled(cwd)]);
  return [npm && "npm", yarn && "yarn", pnpm && "pnpm", bun && "bun", "manual"].filter((pm) => pm !== !1);
}
function hasNpmInstalled(cwd) {
  return hasCommand("npm", cwd);
}
function hasYarnInstalled(cwd) {
  return hasCommand("yarn", cwd);
}
function hasPnpmInstalled(cwd) {
  return hasCommand("pnpm", cwd);
}
function hasBunInstalled(cwd) {
  return hasCommand("bun", cwd);
}
function getNpmRunPath(cwd) {
  let previous, cwdPath = path.resolve(cwd);
  const result = [];
  for (; previous !== cwdPath; )
    result.push(path.join(cwdPath, "node_modules", ".bin")), previous = cwdPath, cwdPath = path.resolve(cwdPath, "..");
  result.push(path.resolve(cwd, process.execPath, ".."));
  const pathEnv = process.env[getPathEnvVarKey()];
  return [...result, pathEnv].join(path.delimiter);
}
function getPartialEnvWithNpmPath(cwd) {
  return {
    [getPathEnvVarKey()]: getNpmRunPath(cwd)
  };
}
function getPathEnvVarKey() {
  return process.platform !== "win32" ? "PATH" : Object.keys(process.env).reverse().find((key) => key.toUpperCase() === "PATH") || "Path";
}
function getCommandPath(cmd, cwd) {
  const options = {
    path: cwd ? getNpmRunPath(cwd) : void 0
  };
  return which(cmd, options).catch(() => null);
}
function hasCommand(cmd, cwd) {
  return getCommandPath(cmd, cwd).then((cmdPath) => cmdPath !== null);
}
async function getMostLikelyInstalledPackageManager(rootDir) {
  const installed = await getAvailablePackageManagers(rootDir), running = getRunningPackageManager();
  return running && installed.includes(running) ? running : void 0;
}
function getRunningPackageManager() {
  const agent = process.env.npm_config_user_agent || "";
  if (agent.includes("yarn"))
    return "yarn";
  if (agent.includes("pnpm"))
    return "pnpm";
  if (agent.includes("bun"))
    return "bun";
  if (/^npm\/\d/.test(agent))
    return "npm";
}
async function upgradePackages(options, context) {
  const {
    packageManager,
    packages
  } = options, {
    output,
    workDir
  } = context, execOptions = {
    encoding: "utf8",
    env: getPartialEnvWithNpmPath(workDir),
    cwd: workDir,
    stdio: "inherit"
  }, upgradePackageArgs = packages.map((pkg) => pkg.join("@"));
  let result;
  if (packageManager === "npm") {
    const npmArgs = ["install", "--legacy-peer-deps", ...upgradePackageArgs];
    output.print(`Running 'npm ${npmArgs.join(" ")}'`), result = await execa("npm", npmArgs, execOptions);
  } else if (packageManager === "yarn") {
    const yarnArgs = ["upgrade ", ...upgradePackageArgs];
    output.print(`Running 'yarn ${yarnArgs.join(" ")}'`), result = await execa("yarn", yarnArgs, execOptions);
  } else if (packageManager === "pnpm") {
    const pnpmArgs = ["upgrade", ...upgradePackageArgs];
    output.print(`Running 'pnpm ${pnpmArgs.join(" ")}'`), result = await execa("pnpm", pnpmArgs, execOptions);
  } else if (packageManager === "bun") {
    const bunArgs = ["update", ...upgradePackageArgs];
    output.print(`Running 'bun ${bunArgs.join(" ")}'`), result = await execa("bun", bunArgs, execOptions);
  } else packageManager === "manual" && output.print(`Manual installation selected - run 'npm upgrade ${upgradePackageArgs.join(" ")}' or equivalent`);
  if (result?.exitCode || result?.failed)
    throw new Error("Package upgrade failed");
}
export {
  checkRequiredDependencies,
  checkStudioDependencyVersions,
  getPackageManagerChoice,
  upgradePackages
};
//# sourceMappingURL=upgradePackages.js.map
