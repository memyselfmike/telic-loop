"use strict";
var node_worker_threads = require("node:worker_threads"), extractWorkspaceManifest = require("../../../_chunks-cjs/extractWorkspaceManifest.cjs"), getStudioWorkspaces = require("../../../_chunks-cjs/getStudioWorkspaces.cjs"), mockBrowserEnvironment = require("../../../_chunks-cjs/mockBrowserEnvironment.cjs");
async function main() {
  if (node_worker_threads.isMainThread || !node_worker_threads.parentPort)
    throw new Error("This module must be run as a worker thread");
  const opts = node_worker_threads.workerData, cleanup = mockBrowserEnvironment.mockBrowserEnvironment(opts.workDir);
  try {
    const workspaces = await getStudioWorkspaces.getStudioWorkspaces({
      basePath: opts.workDir
    });
    for (const workspace of workspaces)
      node_worker_threads.parentPort?.postMessage(extractWorkspaceManifest.extractCreateWorkspaceManifest(workspace));
  } finally {
    node_worker_threads.parentPort?.close(), cleanup();
  }
}
main().then(() => process.exit());
//# sourceMappingURL=extractManifest.cjs.map
