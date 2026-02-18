"use strict";
var fs = require("node:fs/promises"), path = require("node:path"), node_worker_threads = require("node:worker_threads"), codegen = require("@sanity/codegen"), workerChannels = require("@sanity/worker-channels");
function _interopDefaultCompat(e) {
  return e && typeof e == "object" && "default" in e ? e : { default: e };
}
var path__default = /* @__PURE__ */ _interopDefaultCompat(path);
if (node_worker_threads.isMainThread || !node_worker_threads.parentPort)
  throw new Error("This module must be run as a worker thread");
codegen.registerBabel();
async function main({
  schemaPath,
  searchPath,
  workDir,
  overloadClientMethods
}) {
  const report = workerChannels.WorkerChannelReporter.from(node_worker_threads.parentPort), fullPath = path__default.default.isAbsolute(schemaPath) ? schemaPath : path__default.default.join(workDir, schemaPath);
  try {
    if (!(await fs.stat(fullPath)).isFile())
      throw new Error(`Schema path is not a file: ${schemaPath}`);
  } catch (err) {
    if (err.code === "ENOENT") {
      const hint = schemaPath === "./schema.json" ? ' - did you run "sanity schema extract"?' : "";
      throw new Error(`Schema file not found: ${fullPath}${hint}`, { cause: err });
    }
    throw err;
  }
  const schema = await codegen.readSchema(fullPath);
  report.event.loadedSchema();
  const typeGenerator = new codegen.TypeGenerator(), { files, queries } = codegen.findQueriesInPath({
    path: searchPath,
    resolver: codegen.getResolver(workDir)
  });
  report.event.typegenStarted({ expectedFileCount: files.length });
  const result = await typeGenerator.generateTypes({
    queries,
    schema,
    reporter: report,
    schemaPath,
    root: workDir,
    overloadClientMethods
  });
  report.event.typegenComplete(result);
}
main(node_worker_threads.workerData).catch((err) => {
  throw err;
});
//# sourceMappingURL=typegenGenerate.js.map
