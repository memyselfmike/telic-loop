import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import fs, { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { text } from "node:stream/consumers";
import { pipeline } from "node:stream/promises";
import gunzipMaybe from "gunzip-maybe";
import isTar from "is-tar";
import peek from "peek-stream";
import { mergeMap, from, switchMap, zip, of, mergeWith, map, tap, pipe, scan, catchError, EMPTY, filter } from "rxjs";
import tar from "tar-fs";
import { glob } from "tinyglobby";
import { debug as debug$1 } from "./_internal.js";
import { determineTargetMediaLibrary, MINIMUM_API_VERSION } from "./determineTargetMediaLibrary.js";
import readline from "node:readline";
async function readNdjsonFile(ndjson) {
  const lines = readline.createInterface({
    input: ndjson
  }), entries = [];
  try {
    for await (const line of lines) {
      const trimmed = line.trim();
      trimmed && entries.push(JSON.parse(trimmed));
    }
  } finally {
    lines.close(), ndjson.destroy();
  }
  return entries;
}
const debug = debug$1.extend("importMedia"), DEFAULT_CONCURRENCY = 6, importAssetsAction = async (args, context) => {
  const {
    output,
    apiClient,
    chalk
  } = context, [importSourcePath] = args.argsWithoutOptions, replaceAspects = args.extOptions["replace-aspects"] ?? !1, mediaLibraryId = args.extOptions["media-library-id"] ?? await determineTargetMediaLibrary(context), client = apiClient().withConfig({
    apiVersion: MINIMUM_API_VERSION,
    requestTagPrefix: "sanity.mediaLibraryCli.import",
    resource: {
      type: "media-library",
      id: mediaLibraryId
    },
    perspective: "drafts"
  });
  output.print(), output.print(`Importing to media library: ${chalk.bold(mediaLibraryId)}`), output.print(`Importing from path: ${chalk.bold(importSourcePath)}`), output.print();
  const spinner = output.spinner("Beginning import\u2026").start();
  importer({
    client,
    sourcePath: importSourcePath,
    replaceAspects,
    chalk,
    spinner,
    output
  }).pipe(reportResult({
    chalk,
    spinner
  })).subscribe({
    error: (error) => {
      spinner.stop(), output.error(error);
    }
  });
};
function importer(options) {
  return resolveSource(options).pipe(mergeMap(({
    files,
    images,
    aspectsNdjsonPath,
    workingPath
  }) => {
    const fileCount = files.length + images.length;
    if (fileCount === 0)
      throw new Error("No assets to import");
    const aspectsDataPromise = aspectsNdjsonPath ? readNdjsonFile(createReadStream(aspectsNdjsonPath)) : Promise.resolve([]);
    return from(aspectsDataPromise).pipe(mergeMap((aspectsData) => {
      const context = {
        ...options,
        workingPath,
        aspectsData
      };
      return from(files).pipe(switchMap((file) => zip(of("file"), of(file))), mergeWith(from(images).pipe(switchMap((file) => zip(of("image"), of(file))))), fetchExistingAssets(context), uploadAsset(context), resolveAspectData(context), setAspects(context), map((asset) => ({
        asset,
        fileCount
      })));
    }));
  }));
}
function resolveSource({
  sourcePath,
  chalk
}) {
  return from(fs.stat(sourcePath)).pipe(switchMap((stats) => stats.isDirectory() ? of(sourcePath) : from(mkdtemp(path.join(tmpdir(), "sanity-media-library-import"))).pipe(switchMap((tempPath) => from(pipeline(createReadStream(sourcePath), gunzipMaybe(), untarMaybe(tempPath))).pipe(map(() => tempPath))))), switchMap((importSourcePath) => from(glob(["**/data.ndjson"], {
    cwd: importSourcePath,
    deep: 2,
    absolute: !0
  })).pipe(map(([aspectsNdjsonPath]) => ({
    aspectsNdjsonPath,
    importSourcePath,
    workingPath: typeof aspectsNdjsonPath > "u" ? importSourcePath : path.dirname(aspectsNdjsonPath)
  })))), tap(({
    aspectsNdjsonPath,
    importSourcePath
  }) => {
    debug(typeof aspectsNdjsonPath > "u" ? `[No data.ndjson file] No predefined aspect data will be imported from ${importSourcePath}` : `[Found NDJSON file] ${aspectsNdjsonPath}`);
  }), switchMap(({
    aspectsNdjsonPath,
    workingPath
  }) => from(Promise.all([glob(["files/*"], {
    cwd: workingPath
  }), glob(["images/*"], {
    cwd: workingPath
  })])).pipe(map(([files, images]) => ({
    files,
    images,
    aspectsNdjsonPath,
    workingPath
  })))));
}
function untarMaybe(outputPath) {
  return peek({
    newline: !1,
    maxBuffer: 300
  }, (data, swap) => isTar(data) ? swap(null, tar.extract(outputPath)) : swap(null));
}
function fetchAssetsByHash({
  client,
  type
}) {
  return switchMap((hash) => client.observable.fetch(`*[
          _type == "sanity.asset" &&
          currentVersion._ref == *[
            _type == $type &&
            sha1hash == $hash
          ][0]._id
        ]._id`, {
    type: ["sanity", `${type}Asset`].join("."),
    hash
  }, {
    tag: "asset.getId"
  }).pipe(switchMap((assetIds) => zip(of(hash), of(assetIds)))));
}
function fetchExistingAssets({
  client,
  workingPath
}) {
  return mergeMap(([type, asset]) => {
    const createSha1Hash = createHash("sha1"), sha1hash = text(createReadStream(path.join(workingPath, asset)).pipe(createSha1Hash).setEncoding("hex"));
    return from(sha1hash).pipe(tap((hash) => debug(`[Asset ${asset}] Checking for ${type} asset with hash ${hash}`)), fetchAssetsByHash({
      client,
      type
    }), map(([hash, assetIds]) => assetIds.length === 0 ? [type, asset, hash] : {
      originalFilename: asset,
      sha1Hash: hash,
      assetIds,
      isExistingAsset: !0
    }));
  });
}
function resolveAspectData({
  aspectsData
}) {
  return map((resolvedAsset) => {
    if (!aspectsData || aspectsData.length === 0)
      return {
        ...resolvedAsset,
        aspects: void 0
      };
    const aspectsFromImport = aspectsData.find((entry) => entry.filename === resolvedAsset.originalFilename);
    return {
      ...resolvedAsset,
      aspects: aspectsFromImport?.aspects
    };
  });
}
function setAspects({
  client,
  replaceAspects
}) {
  return mergeMap((asset) => {
    const {
      assetIds,
      isExistingAsset,
      aspects
    } = asset;
    if (isExistingAsset && !replaceAspects)
      return debug(`[Asset ${asset.originalFilename}] Skipping replacement of existing aspects`), of(asset);
    if (typeof aspects > "u")
      return debug(`[Asset ${asset.originalFilename}] No aspects to import`), of(asset);
    const transaction = assetIds.reduce((previous, assetId) => previous.patch(assetId, {
      set: {
        aspects
      }
    }), client.observable.transaction());
    return debug(`[Asset ${asset.originalFilename}] Setting aspects on asset documents ${JSON.stringify(assetIds)}`), transaction.commit({
      visibility: "async",
      tag: "asset.setAspects"
    }).pipe(map(() => asset));
  }, DEFAULT_CONCURRENCY);
}
function uploadAsset({
  workingPath,
  client
}) {
  return mergeMap((maybeResolvedAsset) => {
    if ("assetIds" in maybeResolvedAsset)
      return debug(`[Asset ${maybeResolvedAsset.originalFilename}] Skipping upload of existing asset with hash ${maybeResolvedAsset.sha1Hash}`), of(maybeResolvedAsset);
    const [type, asset, hash] = maybeResolvedAsset;
    return debug(`[Asset ${asset}] Uploading new asset`), client.observable.assets.upload(type, createReadStream(path.join(workingPath, asset)), {
      tag: "asset.upload"
    }).pipe(
      catchError((error) => error.statusCode === 409 ? (debug(`[Asset ${asset}] Cannot overwrite existing ${type} asset with hash ${hash}`), EMPTY) : EMPTY),
      filter((response) => response.type === "response"),
      tap(() => debug(`[Asset ${asset}] Finished uploading new asset`)),
      // TODO: The `client.assets.upload` method should return `MediaLibraryUploadResponse` when operating on Media Library resources. When that occurs, this type assertion can be removed.
      map((response) => response.body),
      map((result) => ({
        assetIds: [result.asset._id],
        originalFilename: asset,
        sha1Hash: hash,
        isExistingAsset: !1
      }))
    );
  }, DEFAULT_CONCURRENCY);
}
function reportResult({
  chalk,
  spinner
}) {
  let previousState;
  return pipe(scan((processedAssetsCount, state) => [processedAssetsCount[0] + 1, state], [0, void 0]), tap({
    next: ([processedAssetsCount, state]) => {
      previousState = state, spinner.text = `${processedAssetsCount} of ${state?.fileCount} assets imported ${chalk.dim(state?.asset.originalFilename)}`;
    },
    complete: () => spinner.succeed(`Imported ${previousState?.fileCount} assets`)
  }));
}
export {
  importAssetsAction as default,
  importer,
  resolveSource,
  setAspects
};
//# sourceMappingURL=importAssetsAction.js.map
