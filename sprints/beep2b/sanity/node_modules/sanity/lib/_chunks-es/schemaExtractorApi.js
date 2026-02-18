import { defineTrace } from "@sanity/telemetry";
import { writeFile } from "node:fs/promises";
import path, { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { Worker } from "node:worker_threads";
import readPkgUp from "read-pkg-up";
import { formatSchemaValidation } from "./formatSchemaValidation.js";
import chokidar from "chokidar";
import { debounce } from "lodash-es";
const SchemaExtractedTrace = defineTrace({
  name: "Schema Extracted",
  version: 0,
  description: "Trace emitted when extracting schema"
}), SchemaExtractionWatchModeTrace = defineTrace({
  name: "Schema Extraction Watch Mode Started",
  version: 0,
  description: "Trace emitted when schema extraction watch mode is run"
}), DEFAULT_WATCH_PATTERNS = ["sanity.config.{js,jsx,ts,tsx,mjs}", "schema*/**/*.{js,jsx,ts,tsx,mjs}"], IGNORED_PATTERNS = ["**/node_modules/**", "**/.git/**", "**/dist/**", "**/lib/**", "**/.sanity/**"];
function createExtractionRunner(onExtract) {
  const state = {
    isExtracting: !1,
    pendingExtraction: !1
  };
  async function runExtraction() {
    if (state.isExtracting) {
      state.pendingExtraction = !0;
      return;
    }
    state.isExtracting = !0, state.pendingExtraction = !1;
    try {
      await onExtract();
    } finally {
      state.isExtracting = !1, state.pendingExtraction && (state.pendingExtraction = !1, await runExtraction());
    }
  }
  return {
    state,
    runExtraction
  };
}
async function createSchemaWatcher(options) {
  const {
    workDir,
    patterns,
    debounceMs = 1e3,
    onExtract,
    output
  } = options, {
    runExtraction
  } = createExtractionRunner(onExtract), debouncedExtract = debounce(() => {
    runExtraction();
  }, debounceMs), absolutePatterns = patterns.map((pattern) => path.isAbsolute(pattern) ? pattern : path.join(workDir, pattern)), watcher = chokidar.watch(absolutePatterns, {
    ignoreInitial: !0,
    ignored: IGNORED_PATTERNS,
    cwd: workDir
  });
  return watcher.on("all", (event, filePath) => {
    const timestamp = (/* @__PURE__ */ new Date()).toLocaleTimeString(), relativePath = path.isAbsolute(filePath) ? path.relative(workDir, filePath) : filePath;
    output.print(`[${timestamp}] ${event}: ${relativePath}`), debouncedExtract();
  }), watcher.on("error", (err) => {
    output.error(`Watcher error: ${err instanceof Error ? err.message : String(err)}`);
  }), watcher;
}
const __dirname$1 = dirname(fileURLToPath(import.meta.url));
class SchemaExtractionError extends Error {
  constructor(message, validation) {
    super(message), this.name = "SchemaExtractionError", this.validation = validation;
  }
}
async function extractSchemaToFile(options) {
  const {
    workDir,
    outputPath,
    workspaceName,
    enforceRequiredFields = !1,
    format = "groq-type-nodes"
  } = options, rootPkgPath = readPkgUp.sync({
    cwd: __dirname$1
  })?.path;
  if (!rootPkgPath)
    throw new Error("Could not find root directory for `sanity` package");
  const workerPath = join(dirname(rootPkgPath), "lib", "_internal", "cli", "threads", "extractSchema.cjs"), worker = new Worker(workerPath, {
    workerData: {
      workDir,
      workspaceName,
      enforceRequiredFields,
      format
    },
    env: process.env
  }), message = await new Promise((resolve, reject) => {
    worker.addListener("message", resolve), worker.addListener("error", reject);
  });
  if (message.type === "error")
    throw new SchemaExtractionError(message.error, message.validation);
  return await writeFile(outputPath, `${JSON.stringify(message.schema, null, 2)}
`), message.schema;
}
async function startSchemaWatcher(options) {
  const {
    workDir,
    outputPath,
    output,
    workspaceName,
    enforceRequiredFields = !1,
    format = "groq-type-nodes",
    patterns = DEFAULT_WATCH_PATTERNS,
    onExtraction
  } = options, runExtraction = async (spinnerText, successText) => {
    const spinner = output.spinner({}).start(spinnerText), startTime = Date.now();
    try {
      const schema = await extractSchemaToFile({
        workDir,
        outputPath,
        workspaceName,
        enforceRequiredFields,
        format
      });
      return onExtraction?.({
        success: !0,
        schema,
        duration: Date.now() - startTime
      }), spinner.succeed(successText), !0;
    } catch (err) {
      return onExtraction?.({
        success: !1,
        duration: Date.now() - startTime
      }), spinner.fail(`Extraction failed: ${err instanceof Error ? err.message : String(err)}`), err instanceof SchemaExtractionError && err.validation && err.validation.length > 0 && (output.print(""), output.print(formatSchemaValidation(err.validation))), !1;
    }
  };
  await runExtraction("Extracting schema...", `Extracted schema to ${outputPath}`);
  const watcher = await createSchemaWatcher({
    workDir,
    patterns,
    onExtract: async () => {
      await runExtraction("Extracting schema...", `Extracted schema to ${outputPath}`);
    },
    output
  });
  return {
    stop: async () => {
      await watcher.close();
    },
    watcher
  };
}
export {
  DEFAULT_WATCH_PATTERNS,
  SchemaExtractedTrace,
  SchemaExtractionError,
  SchemaExtractionWatchModeTrace,
  extractSchemaToFile,
  startSchemaWatcher
};
//# sourceMappingURL=schemaExtractorApi.js.map
