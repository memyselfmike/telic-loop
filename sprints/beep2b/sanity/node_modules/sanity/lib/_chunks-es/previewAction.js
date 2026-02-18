import path from "node:path";
import { startPreviewServer } from "./previewServer.js";
import "./runtime.js";
import { gracefulServerDeath, getSharedServerConfig } from "./servers.js";
async function startSanityPreviewServer(args, context) {
  const flags = args.extOptions, {
    workDir,
    cliConfig
  } = context, defaultRootDir = path.resolve(path.join(workDir, "dist")), rootDir = path.resolve(args.argsWithoutOptions[0] || defaultRootDir), config = getPreviewServerConfig({
    flags,
    workDir,
    cliConfig,
    rootDir
  });
  try {
    await startPreviewServer(config);
  } catch (err) {
    gracefulServerDeath("preview", config.httpHost, config.httpPort, err);
  }
}
function getPreviewServerConfig({
  flags,
  workDir,
  cliConfig,
  rootDir
}) {
  return {
    ...getSharedServerConfig({
      flags,
      workDir,
      cliConfig
    }),
    root: rootDir
  };
}
export {
  startSanityPreviewServer as default
};
//# sourceMappingURL=previewAction.js.map
