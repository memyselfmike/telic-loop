import path from "node:path";
function withMediaLibraryConfig(context) {
  const {
    cliConfig,
    cliConfigPath
  } = context, mediaLibrary = typeof cliConfig == "object" && "mediaLibrary" in cliConfig ? cliConfig.mediaLibrary : void 0, relativeConfigPath = path.relative(process.cwd(), cliConfigPath ?? "");
  if (typeof mediaLibrary?.aspectsPath > "u")
    throw new Error(`${relativeConfigPath} does not contain a media library aspects path ("mediaLibrary.aspectsPath"), which is required for the Sanity CLI to manage aspects.`);
  return {
    ...context,
    mediaLibrary
  };
}
export {
  withMediaLibraryConfig
};
//# sourceMappingURL=withMediaLibraryConfig.js.map
