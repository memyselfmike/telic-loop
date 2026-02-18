"use strict";
var node_worker_threads = require("node:worker_threads"), _internal = require("@sanity/schema/_internal"), getStudioWorkspaces = require("../../../_chunks-cjs/getStudioWorkspaces.cjs"), mockBrowserEnvironment = require("../../../_chunks-cjs/mockBrowserEnvironment.cjs");
const {
  workDir,
  workspace: workspaceName,
  level = "warning",
  debugSerialize
} = node_worker_threads.workerData;
async function main() {
  if (node_worker_threads.isMainThread || !node_worker_threads.parentPort)
    throw new Error("This module must be run as a worker thread");
  const cleanup = mockBrowserEnvironment.mockBrowserEnvironment(workDir);
  try {
    const workspaces = await getStudioWorkspaces.getStudioWorkspaces({
      basePath: workDir
    });
    if (!workspaces.length)
      throw new Error("Configuration did not return any workspaces.");
    let workspace;
    if (workspaceName) {
      if (workspace = workspaces.find((w) => w.name === workspaceName), !workspace)
        throw new Error(`Could not find any workspaces with name \`${workspaceName}\``);
    } else {
      if (workspaces.length !== 1)
        throw new Error("Multiple workspaces found. Please specify which workspace to use with '--workspace'.");
      workspace = workspaces[0];
    }
    const schema = workspace.schema, validation = schema._validation;
    let serializedDebug;
    if (debugSerialize) {
      const set = await new _internal.DescriptorConverter().get(schema);
      serializedDebug = getSeralizedSchemaDebug(set);
    }
    const result = {
      validation: validation.map((group) => ({
        ...group,
        problems: group.problems.filter((problem) => level === "error" ? problem.severity === "error" : !0)
      })).filter((group) => group.problems.length),
      serializedDebug
    };
    node_worker_threads.parentPort?.postMessage(result);
  } catch (err) {
    throw console.error(err), console.error(err.stack), err;
  } finally {
    cleanup();
  }
}
function getSeralizedSchemaDebug(set) {
  let size = 0;
  const types = {}, hoisted = {};
  for (const [id, value] of Object.entries(set.objectValues)) {
    switch (typeof value.type == "string" ? value.type : "<unknown>") {
      case "sanity.schema.namedType": {
        const typeName = typeof value.name == "string" ? value.name : id;
        if (isEncodableObject(value.typeDef)) {
          const debug = getSerializedTypeDebug(value.typeDef);
          types[typeName] = debug, size += debug.size;
        }
        break;
      }
      case "sanity.schema.hoisted": {
        const key = typeof value.key == "string" ? value.key : id;
        if (isEncodableObject(value.value) && isEncodableObject(value.value.typeDef)) {
          const debug = getSerializedTypeDebug(value.value.typeDef);
          hoisted[key] = debug, size += debug.size;
        }
        break;
      }
    }
    size += JSON.stringify(value).length;
  }
  return {
    size,
    types,
    hoisted
  };
}
function isEncodableObject(val) {
  return typeof val == "object" && val !== null && !Array.isArray(val);
}
function getSerializedTypeDebug(typeDef) {
  const ext = typeof typeDef.extends == "string" ? typeDef.extends : "<unknown>";
  let fields, of;
  if (Array.isArray(typeDef.fields)) {
    fields = {};
    for (const field of typeDef.fields) {
      if (!isEncodableObject(field)) continue;
      const name = field.name, fieldTypeDef = field.typeDef;
      typeof name != "string" || !isEncodableObject(fieldTypeDef) || (fields[name] = getSerializedTypeDebug(fieldTypeDef));
    }
  }
  if (Array.isArray(typeDef.of)) {
    of = {};
    for (const field of typeDef.of) {
      if (!isEncodableObject(field)) continue;
      const name = field.name, arrayTypeDef = field.typeDef;
      typeof name != "string" || !isEncodableObject(arrayTypeDef) || (of[name] = getSerializedTypeDebug(arrayTypeDef));
    }
  }
  return {
    size: JSON.stringify(typeDef).length,
    extends: ext,
    fields,
    of
  };
}
main().then(() => process.exit());
//# sourceMappingURL=validateSchema.cjs.map
