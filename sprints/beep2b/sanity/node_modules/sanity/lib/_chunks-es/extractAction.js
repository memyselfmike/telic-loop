import { join } from "node:path";
import { once, mean } from "lodash-es";
import { promiseWithResolvers } from "./promiseWithResolvers.js";
import { SchemaExtractionWatchModeTrace, DEFAULT_WATCH_PATTERNS, startSchemaWatcher, SchemaExtractedTrace, extractSchemaToFile, SchemaExtractionError } from "./schemaExtractorApi.js";
import { formatSchemaValidation } from "./formatSchemaValidation.js";
async function extractAction(args, context) {
  return args.extOptions.watch ? runWatchMode(args, context) : runSingleExtraction(args, context);
}
function getExtractOptions(flags, config, workDir) {
  const schemaExtraction = config?.schemaExtraction;
  return {
    workspace: flags.workspace ?? schemaExtraction?.workspace,
    format: flags.format ?? "groq-type-nodes",
    enforceRequiredFields: flags["enforce-required-fields"] ?? schemaExtraction?.enforceRequiredFields ?? !1,
    outputPath: flags.path ?? schemaExtraction?.path ?? join(workDir, "schema.json"),
    watchPatterns: flags["watch-patterns"] ? Array.isArray(flags["watch-patterns"]) ? flags["watch-patterns"] : [flags["watch-patterns"]] : schemaExtraction?.watchPatterns ?? []
  };
}
async function runSingleExtraction(args, context) {
  const flags = args.extOptions, {
    workDir,
    output,
    telemetry,
    cliConfig
  } = context, {
    format,
    enforceRequiredFields,
    outputPath,
    workspace: workspaceName
  } = getExtractOptions(flags, cliConfig, workDir), spinner = output.spinner({}).start(enforceRequiredFields ? "Extracting schema, with enforced required fields" : "Extracting schema"), trace = telemetry.trace(SchemaExtractedTrace);
  trace.start();
  try {
    const schema = await extractSchemaToFile({
      workDir,
      outputPath,
      workspaceName,
      enforceRequiredFields,
      format
    });
    trace.log({
      schemaAllTypesCount: schema.length,
      schemaDocumentTypesCount: schema.filter((type) => type.type === "document").length,
      schemaTypesCount: schema.filter((type) => type.type === "type").length,
      enforceRequiredFields,
      schemaFormat: format
    }), trace.complete(), spinner.succeed(enforceRequiredFields ? `Extracted schema to ${outputPath} with enforced required fields` : `Extracted schema to ${outputPath}`);
  } catch (err) {
    throw trace.error(err), spinner.fail(enforceRequiredFields ? "Failed to extract schema, with enforced required fields" : "Failed to extract schema"), err instanceof SchemaExtractionError && err.validation && err.validation.length > 0 && (output.print(""), output.print(formatSchemaValidation(err.validation))), err;
  }
}
async function runWatchMode(args, context) {
  const flags = args.extOptions, startTime = Date.now(), stats = {
    successfulDurations: [],
    failedCount: 0
  }, {
    workDir,
    output,
    telemetry,
    cliConfig
  } = context, options = getExtractOptions(flags, cliConfig, workDir), {
    format,
    enforceRequiredFields,
    outputPath,
    watchPatterns: additionalPatterns,
    workspace: workspaceName
  } = options, watchPatterns = [...DEFAULT_WATCH_PATTERNS, ...additionalPatterns], trace = telemetry.trace(SchemaExtractionWatchModeTrace);
  trace.start(), output.print("Schema extraction watch mode"), output.print(""), output.print("Watching for changes in:");
  for (const pattern of watchPatterns)
    output.print(`  - ${pattern}`);
  output.print(""), output.print("Running initial extraction...");
  const {
    stop
  } = await startSchemaWatcher({
    workDir,
    outputPath,
    output,
    workspaceName,
    enforceRequiredFields,
    format,
    patterns: watchPatterns,
    onExtraction: ({
      success,
      duration
    }) => {
      success ? stats.successfulDurations.push(duration) : stats.failedCount++;
    }
  });
  trace.log({
    step: "started",
    enforceRequiredFields,
    schemaFormat: format
  }), output.print(""), output.print("Watching for changes... (Ctrl+C to stop)");
  const {
    resolve,
    promise
  } = promiseWithResolvers(), cleanup = once(() => {
    trace.log({
      step: "stopped",
      watcherDuration: Date.now() - startTime,
      averageExtractionDuration: mean(stats.successfulDurations),
      extractionSuccessfulCount: stats.successfulDurations.length,
      extractionFailedCount: stats.failedCount
    }), trace.complete(), output.print(""), output.print("Stopping watch mode..."), stop(), resolve();
  });
  process.on("SIGINT", cleanup), process.on("SIGTERM", cleanup), await promise;
}
export {
  extractAction as default,
  getExtractOptions
};
//# sourceMappingURL=extractAction.js.map
