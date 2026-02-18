import path from "node:path";
import { exportDataset } from "@sanity/export";
import { determineTargetMediaLibrary, MINIMUM_API_VERSION } from "./determineTargetMediaLibrary.js";
const DEFAULT_CONCURRENCY = 6, exportAssetsAction = async (args, context) => {
  const {
    apiClient,
    output,
    chalk
  } = context, mediaLibraryId = args.extOptions["media-library-id"] ?? await determineTargetMediaLibrary(context), client = apiClient().withConfig({
    apiVersion: MINIMUM_API_VERSION,
    requestTagPrefix: "sanity.mediaLibraryCli.export"
  }), outputPath = path.join(process.cwd(), `media-library-${mediaLibraryId}-${Date.now()}.tar.gz`);
  output.print(), output.print(`Exporting from media library: ${chalk.bold(mediaLibraryId)}`), output.print(`Exporting to path: ${chalk.bold(outputPath)}`), output.print();
  let currentStep = "Beginning export\u2026", spinner = output.spinner(currentStep).start();
  try {
    await exportDataset({
      client,
      mediaLibraryId,
      outputPath,
      drafts: !1,
      types: ["sanity.asset"],
      assetConcurrency: DEFAULT_CONCURRENCY,
      mode: "stream",
      onProgress: (progress) => {
        progress.step !== currentStep ? (spinner.succeed(), spinner = output.spinner(progress.step).start()) : progress.step === currentStep && progress.update && (spinner.text = `${progress.step} (${progress.current}/${progress.total})`), currentStep = progress.step;
      },
      // The `assets.json` assets map is not required for Media Library archives, because the
      // import process reads asset files directly from the archive.
      assetsMap: !1,
      // The documents listed in `data.ndjson` are only used for recording aspect data. If there
      // is no aspect data, the document can safely be omitted.
      filterDocument: (doc) => typeof doc != "object" || doc === null || !("aspects" in doc) || "assetType" in doc && doc.assetType === "sanity.videoAsset" ? !1 : typeof doc.aspects == "object" && doc.aspects !== null && Object.keys(doc.aspects).length !== 0,
      // Media Library archives only record asset aspect data. All other data can be safely
      // ommitted.
      transformDocument: (doc) => typeof doc != "object" || doc === null || !("currentVersion" in doc) || !("aspects" in doc) || typeof doc.currentVersion != "object" || doc.currentVersion === null || !("_ref" in doc.currentVersion) || typeof doc.currentVersion._ref != "string" ? doc : {
        filename: [[doc.currentVersion._ref.split("-")[0], "s"].join(""), generateFilename(doc.currentVersion._ref)].join("/"),
        aspects: doc.aspects
      }
    });
  } catch (error) {
    throw spinner.fail("Failed to export media library"), error;
  }
  spinner.succeed(`Exported media library to ${chalk.bold(outputPath)}`);
};
function generateFilename(assetId) {
  const [, , asset, ext] = assetId.match(/^(image|file)-(.*?)(-[a-z]+)?$/) || [], extension = (ext || "bin").replace(/^-/, "");
  return asset ? `${asset}.${extension}` : `${assetId}.bin`;
}
export {
  exportAssetsAction as default
};
//# sourceMappingURL=exportAssetsAction.js.map
