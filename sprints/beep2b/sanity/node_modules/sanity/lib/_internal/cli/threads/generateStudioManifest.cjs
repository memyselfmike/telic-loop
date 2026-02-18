"use strict";
var node_worker_threads = require("node:worker_threads"), client = require("@sanity/client"), debugit = require("debug"), sanity = require("sanity"), extractWorkspaceManifest = require("../../../_chunks-cjs/extractWorkspaceManifest.cjs"), getStudioWorkspaces = require("../../../_chunks-cjs/getStudioWorkspaces.cjs"), mockBrowserEnvironment = require("../../../_chunks-cjs/mockBrowserEnvironment.cjs");
function _interopDefaultCompat(e) {
  return e && typeof e == "object" && "default" in e ? e : { default: e };
}
var debugit__default = /* @__PURE__ */ _interopDefaultCompat(debugit);
const debug = debugit__default.default("sanity:cli:generate-studio-manifest");
async function main() {
  if (node_worker_threads.isMainThread || !node_worker_threads.parentPort)
    throw new Error("This module must be run as a worker thread");
  const opts = node_worker_threads.workerData, cleanup = mockBrowserEnvironment.mockBrowserEnvironment(opts.workDir);
  try {
    const workspaces = await getStudioWorkspaces.getStudioWorkspaces({
      basePath: opts.workDir
    });
    if (!workspaces.length) {
      node_worker_threads.parentPort.postMessage({
        type: "error",
        message: "No workspaces found in studio configuration"
      });
      return;
    }
    const client$1 = client.createClient({
      ...opts.clientConfig,
      requestTagPrefix: "sanity.cli.deploy"
    }), schemaDescriptorsResult = await uploadSchemasToLexicon(workspaces, client$1);
    if (schemaDescriptorsResult.type === "error") {
      node_worker_threads.parentPort.postMessage(schemaDescriptorsResult);
      return;
    }
    const schemaDescriptors = schemaDescriptorsResult.descriptors, manifest = await sanity.generateStudioManifest({
      workspaces,
      resolveSchemaDescriptorId: (workspace) => schemaDescriptors.get(workspace.name),
      resolveIcon: (workspace) => extractWorkspaceManifest.resolveIcon({
        icon: workspace.icon,
        title: workspace.title,
        subtitle: workspace.subtitle
      }) ?? void 0,
      bundleVersion: opts.sanityVersion,
      buildId: JSON.stringify(Date.now())
    }), result = {
      type: "success",
      // Return null if no workspaces have schema descriptors
      studioManifest: manifest.workspaces.length === 0 ? null : manifest
    };
    node_worker_threads.parentPort.postMessage(result);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error occurred";
    node_worker_threads.parentPort.postMessage({
      type: "error",
      message
    });
  } finally {
    cleanup();
  }
}
async function uploadSchemasToLexicon(workspaces, client2) {
  const schemaDescriptors = /* @__PURE__ */ new Map();
  for (const workspace of workspaces) {
    const workspaceClient = client2.withConfig({
      projectId: workspace.projectId,
      dataset: workspace.dataset
    });
    try {
      const descriptorId = await sanity.uploadSchema(workspace.schema, workspaceClient);
      if (!descriptorId)
        return {
          type: "error",
          message: `Failed to get schema descriptor ID for workspace "${workspace.name}": upload returned empty result`,
          workspaceName: workspace.name
        };
      schemaDescriptors.set(workspace.name, descriptorId), debug(`Uploaded schema for workspace "${workspace.name}" to Lexicon with descriptor ID: ${descriptorId}`);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : "Unknown error";
      return {
        type: "error",
        message: `Failed to upload schema for workspace "${workspace.name}": ${errorMessage}`,
        workspaceName: workspace.name
      };
    }
  }
  return {
    type: "success",
    descriptors: schemaDescriptors
  };
}
main();
//# sourceMappingURL=generateStudioManifest.cjs.map
