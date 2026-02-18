"use strict";
var fs = require("node:fs/promises"), codegen = require("@sanity/codegen"), chalk = require("chalk"), getCliConfig = require("./getCliConfig.js"), cli = require("./cli.js");
function _interopDefaultCompat(e) {
  return e && typeof e == "object" && "default" in e ? e : { default: e };
}
var chalk__default = /* @__PURE__ */ _interopDefaultCompat(chalk), FUNC_ERROR_TEXT = "Expected a function";
function before(n, func) {
  var result;
  if (typeof func != "function")
    throw new TypeError(FUNC_ERROR_TEXT);
  return n = cli.toInteger(n), function() {
    return --n > 0 && (result = func.apply(this, arguments)), n <= 1 && (func = void 0), result;
  };
}
function once(func) {
  return before(2, func);
}
const promiseWithResolvers = Promise.withResolvers?.bind(Promise) || function() {
  let resolve, reject;
  return { promise: new Promise((res, rej) => {
    resolve = res, reject = rej;
  }), resolve, reject };
};
async function getConfig(workDir, configPath) {
  const config = await getCliConfig.getCliConfig(workDir);
  if (!config?.config)
    throw new Error("Unable to load config");
  const legacyConfigPath = configPath || "sanity-typegen.json";
  let hasLegacyConfig = !1;
  try {
    hasLegacyConfig = (await fs.stat(legacyConfigPath)).isFile();
  } catch (err) {
    if (err.code === "ENOENT" && configPath)
      throw new Error(`Typegen config file not found: ${configPath}`, { cause: err });
    if (err.code !== "ENOENT")
      throw new Error(`Error when checking if typegen config file exists: ${legacyConfigPath}`, {
        cause: err
      });
  }
  return config?.config?.typegen && hasLegacyConfig ? (console.warn(
    chalk__default.default.yellow(
      `You've specified typegen in your Sanity CLI config, but also have a typegen config.

The config from the Sanity CLI config is used.
`
    )
  ), {
    config: codegen.configDefinition.parse(config.config.typegen || {}),
    path: config.path,
    type: "cli"
  }) : hasLegacyConfig ? (console.warn(
    chalk__default.default.yellow(
      "The separate typegen config has been deprecated. Use `typegen` in the sanity CLI config instead.\n\nSee: https://www.sanity.io/docs/help/configuring-typegen-in-sanity-cli-config"
    )
  ), {
    config: await codegen.readConfig(legacyConfigPath),
    path: legacyConfigPath,
    type: "legacy"
  }) : {
    config: codegen.configDefinition.parse(config?.config?.typegen || {}),
    path: config?.path,
    type: "cli"
  };
}
async function runSingle({ extOptions: flags }, context) {
  const { output, workDir, telemetry } = context, trace = telemetry.trace(codegen.TypesGeneratedTrace);
  trace.start();
  const spinner = output.spinner({}).start("Loading config\u2026");
  try {
    let config;
    try {
      config = await getConfig(workDir, flags["config-path"]), spinner.succeed(`Config loaded from ${config.path?.replace(workDir, ".")}`);
    } catch (err) {
      throw spinner.fail(), err;
    }
    const { config: typegenConfig, type: typegenConfigMethod } = config, result = await codegen.runTypegenGenerate({
      config: typegenConfig,
      workDir: context.workDir
    }), traceStats = cli.omit(result, "code", "duration");
    trace.log({
      ...traceStats,
      configMethod: typegenConfigMethod,
      configOverloadClientMethods: typegenConfig.overloadClientMethods
    });
  } catch (error) {
    console.error(` ${chalk__default.default.red("\u203A")}   ${error.message}`), trace.error(error), process.exitCode = 1;
  } finally {
    trace.complete();
  }
}
async function runWatcher({ extOptions: flags }, context) {
  const { output, workDir, telemetry } = context, trace = telemetry.trace(codegen.TypegenWatchModeTrace);
  trace.start();
  const spinner = output.spinner({}).start("Loading config\u2026");
  try {
    let config;
    try {
      config = await getConfig(workDir, flags["config-path"]), spinner.succeed(`Config loaded from ${config.path?.replace(workDir, ".")}`);
    } catch (err) {
      throw spinner.fail(), err;
    }
    const typegenConfig = config.config, { promise, resolve } = promiseWithResolvers(), typegenWatcher = codegen.runTypegenWatcher({
      config: typegenConfig,
      workDir,
      spin: spinner
    }), stop = once(async () => {
      process.off("SIGINT", stop), process.off("SIGTERM", stop), trace.log({
        step: "stopped",
        ...typegenWatcher.getStats()
      }), await typegenWatcher.stop(), resolve();
    });
    process.on("SIGINT", stop), process.on("SIGTERM", stop), await promise;
  } catch (error) {
    console.error(` ${chalk__default.default.red("\u203A")}   ${error.message}`), trace.error(error), process.exitCode = 1;
  } finally {
    trace.complete();
  }
}
async function typegenGenerateAction(args, context) {
  const { extOptions: flags } = args;
  if (flags.watch) {
    await runWatcher(args, context);
    return;
  }
  await runSingle(args, context);
}
exports.default = typegenGenerateAction;
//# sourceMappingURL=generateAction.js.map
