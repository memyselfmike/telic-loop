import { writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { Worker } from "node:worker_threads";
import logSymbols from "log-symbols";
import readPkgUp from "read-pkg-up";
import { getAggregatedSeverity, formatSchemaValidation } from "./formatSchemaValidation.js";
function generateMetafile(schema) {
  const output = {
    imports: [],
    exports: [],
    inputs: {},
    bytes: 0
  }, inputs = {};
  function processType(path2, entry) {
    let childSize = 0;
    if (entry.fields)
      for (const [name, fieldEntry] of Object.entries(entry.fields))
        processType(`${path2}/${name}`, fieldEntry), childSize += fieldEntry.size;
    if (entry.of)
      for (const [name, fieldEntry] of Object.entries(entry.of))
        processType(`${path2}/${name}`, fieldEntry), childSize += fieldEntry.size;
    const selfSize = entry.size - childSize;
    inputs[path2] = {
      bytes: selfSize,
      imports: [],
      format: "esm"
    }, output.inputs[path2] = {
      bytesInOutput: selfSize
    }, output.bytes += selfSize;
  }
  for (const [name, entry] of Object.entries(schema.types)) {
    const fakePath = `schema/${entry.extends}/${name}`;
    processType(fakePath, entry);
  }
  for (const [name, entry] of Object.entries(schema.hoisted)) {
    const fakePath = `hoisted/${name}`;
    processType(fakePath, entry);
  }
  return {
    outputs: {
      root: output
    },
    inputs
  };
}
const __dirname$1 = path.dirname(fileURLToPath(import.meta.url));
async function validateAction(args, {
  workDir,
  output
}) {
  const flags = args.extOptions, rootPkgPath = readPkgUp.sync({
    cwd: __dirname$1
  })?.path;
  if (!rootPkgPath)
    throw new Error("Could not find root directory for `sanity` package");
  const workerPath = path.join(path.dirname(rootPkgPath), "lib", "_internal", "cli", "threads", "validateSchema.cjs"), level = flags.level || "warning";
  if (level !== "error" && level !== "warning")
    throw new Error("Invalid level. Available levels are 'error' and 'warning'.");
  const format = flags.format || "pretty";
  if (!["pretty", "ndjson", "json"].includes(format))
    throw new Error(`Did not recognize format '${flags.format}'. Available formats are 'pretty', 'ndjson', and 'json'.`);
  let spinner;
  format === "pretty" && (spinner = output.spinner(flags.workspace ? `Validating schema from workspace '${flags.workspace}'\u2026` : "Validating schema\u2026").start());
  const worker = new Worker(workerPath, {
    workerData: {
      workDir,
      level,
      workspace: flags.workspace,
      debugSerialize: !!flags["debug-metafile-path"]
    },
    env: process.env
  }), {
    validation,
    serializedDebug
  } = await new Promise((resolve, reject) => {
    worker.addListener("message", resolve), worker.addListener("error", reject);
  }), problems = validation.flatMap((group) => group.problems), errorCount = problems.filter((problem) => problem.severity === "error").length, warningCount = problems.filter((problem) => problem.severity === "warning").length, didFail = getAggregatedSeverity(validation) === "error";
  if (flags["debug-metafile-path"] && !didFail) {
    if (!serializedDebug) throw new Error("serializedDebug should always be produced");
    const metafile = generateMetafile(serializedDebug);
    writeFileSync(flags["debug-metafile-path"], JSON.stringify(metafile), "utf8");
  }
  switch (format) {
    case "ndjson": {
      for (const group of validation)
        output.print(JSON.stringify(group));
      break;
    }
    case "json": {
      output.print(JSON.stringify(validation));
      break;
    }
    default:
      spinner?.succeed("Validated schema"), output.print(`
Validation results:`), output.print(`${logSymbols.error} Errors:   ${errorCount.toLocaleString("en-US")} error${errorCount === 1 ? "" : "s"}`), level !== "error" && output.print(`${logSymbols.warning} Warnings: ${warningCount.toLocaleString("en-US")} warning${warningCount === 1 ? "" : "s"}`), output.print(), output.print(formatSchemaValidation(validation)), flags["debug-metafile-path"] && (output.print(), didFail ? output.print(`${logSymbols.info} Metafile not written due to validation errors`) : (output.print(`${logSymbols.info} Metafile written to: ${flags["debug-metafile-path"]}`), output.print("  This can be analyzed at https://esbuild.github.io/analyze/")));
  }
  process.exitCode = didFail ? 1 : 0;
}
export {
  validateAction as default
};
//# sourceMappingURL=validateAction.js.map
