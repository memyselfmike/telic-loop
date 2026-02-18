import path from "node:path";
import { fileURLToPath } from "node:url";
import { isMainThread, Worker } from "node:worker_threads";
import readPkgUp from "read-pkg-up";
import { createSchema } from "sanity";
const __dirname$1 = path.dirname(fileURLToPath(import.meta.url));
async function getGraphQLAPIs(cliContext) {
  if (!isMainThread)
    throw new Error("getGraphQLAPIs() must be called from the main thread");
  const defaultTypes = createSchema({
    name: "default",
    types: []
  }).getTypeNames(), isCustomType = (type) => !defaultTypes.includes(type.name);
  return (await getApisWithSchemaTypes(cliContext)).map(({
    schemaTypes,
    ...api
  }) => ({
    schema: createSchema({
      name: "default",
      types: schemaTypes.filter(isCustomType)
    }),
    ...api
  }));
}
function getApisWithSchemaTypes(cliContext) {
  return new Promise((resolve, reject) => {
    const {
      cliConfig,
      cliConfigPath,
      workDir
    } = cliContext, rootPkgPath = readPkgUp.sync({
      cwd: __dirname$1
    })?.path;
    if (!rootPkgPath)
      throw new Error("Could not find root directory for `sanity` package");
    const rootDir = path.dirname(rootPkgPath), workerPath = path.join(rootDir, "lib", "_internal", "cli", "threads", "getGraphQLAPIs.cjs"), worker = new Worker(workerPath, {
      workerData: {
        cliConfig: serialize(cliConfig || {}),
        cliConfigPath,
        workDir
      },
      env: process.env
    });
    worker.on("message", resolve), worker.on("error", reject), worker.on("exit", (code) => {
      code !== 0 && reject(new Error(`Worker stopped with exit code ${code}`));
    });
  });
}
function serialize(obj) {
  try {
    return JSON.parse(JSON.stringify(obj));
  } catch (cause) {
    throw new Error("Failed to serialize CLI configuration", {
      cause
    });
  }
}
export {
  getGraphQLAPIs
};
//# sourceMappingURL=getGraphQLAPIs.js.map
