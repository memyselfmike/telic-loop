import fs from "node:fs/promises";
import { createRequire } from "node:module";
import { EOL } from "node:os";
import path from "node:path";
import { validateMediaLibraryAssetAspect } from "@sanity/schema/_internal";
import { isAssetAspect } from "@sanity/types";
import { register } from "esbuild-register/dist/node";
import pluralize from "pluralize-esm";
import { mergeMap, of, from, tap, filter, switchMap, map, groupBy, zip, toArray, finalize, pipe, catchError, scan, takeLast } from "rxjs";
import { determineTargetMediaLibrary, MINIMUM_API_VERSION, ASPECT_FILE_EXTENSIONS } from "./determineTargetMediaLibrary.js";
import { withMediaLibraryConfig } from "./withMediaLibraryConfig.js";
const require$1 = createRequire(import.meta.url), deployAspectAction = async (args, context) => {
  const {
    output,
    apiClient,
    mediaLibrary
  } = withMediaLibraryConfig(context), [aspectId] = args.argsWithoutOptions, all = args.extOptions.all ?? !1;
  if (!all && typeof aspectId > "u") {
    output.error("Specify an aspect name, or use the `--all` option to deploy all aspect definitions.");
    return;
  }
  if (all && typeof aspectId < "u") {
    output.error("Specified both an aspect name and `--all`.");
    return;
  }
  const mediaLibraryId = args.extOptions["media-library-id"] ?? await determineTargetMediaLibrary(context), client = apiClient().withConfig({
    apiVersion: MINIMUM_API_VERSION,
    requestTagPrefix: "sanity.mediaLibraryCli"
  });
  importAspects({
    aspectsPath: mediaLibrary.aspectsPath,
    filterAspects: (entry) => all ? !0 : typeof entry == "object" && entry !== null && "_id" in entry ? entry._id === aspectId : !1
  }).pipe(mergeMap(([status, aspects]) => status === "invalid" ? of({
    status: "failure",
    reason: "invalidAspect",
    aspects
  }) : of(aspects).pipe(deployAspects({
    client,
    mediaLibraryId,
    dryRun: !1
  }))), reportResult({
    context
  }), reportUnfoundAspect({
    aspectId,
    context
  })).subscribe();
};
function importAspects({
  aspectsPath,
  filterAspects = () => !0
}) {
  let unregister;
  const entries = fs.readdir(aspectsPath, {
    withFileTypes: !0
  });
  return from(entries).pipe(tap({
    subscribe() {
      unregister = register({
        target: `node${process.version.slice(1)}`,
        supported: {
          "dynamic-import": !0
        },
        format: "cjs"
      }).unregister;
    }
  }), mergeMap((entry) => from(entry)), filter((file) => file.isFile()), filter((file) => ASPECT_FILE_EXTENSIONS.includes(path.extname(file.name))), switchMap((file) => importAspect({
    aspectsPath,
    filename: file.name
  })), map(([filename, maybeAspect]) => {
    if (!isAssetAspect(maybeAspect))
      return {
        status: "invalid",
        aspect: maybeAspect,
        validationErrors: [],
        filename
      };
    const [valid, errors] = validateMediaLibraryAssetAspect(maybeAspect.definition);
    return valid ? {
      status: "valid",
      aspect: maybeAspect,
      validationErrors: [],
      filename
    } : {
      status: "invalid",
      aspect: maybeAspect,
      validationErrors: errors,
      filename
    };
  }), groupBy((maybeAspect) => maybeAspect.status), mergeMap((group) => zip(of(group.key), group.pipe(filter(({
    aspect
  }) => filterAspects(aspect)), toArray()))), finalize(() => unregister?.()));
}
function importAspect({
  aspectsPath,
  filename
}) {
  return of([filename, require$1(path.resolve(aspectsPath, filename)).default]);
}
function deployAspects({
  client,
  dryRun,
  mediaLibraryId
}) {
  return pipe(filter((aspects) => aspects.length !== 0), switchMap((aspects) => client.observable.request({
    method: "POST",
    uri: `/media-libraries/${mediaLibraryId}/mutate`,
    tag: "deployAspects",
    query: {
      dryRun: String(dryRun)
    },
    body: {
      mutations: aspects.map(({
        aspect
      }) => ({
        createOrReplace: aspect
      }))
    }
  }).pipe(mergeMap(() => of({
    status: "success",
    aspects
  })), catchError((error) => of({
    status: "failure",
    reason: "failedMutation",
    error: error.message,
    aspects
  })))));
}
function reportResult({
  context
}) {
  return tap((result) => {
    const {
      output,
      chalk
    } = context, list = formatAspectList({
      aspects: result.aspects,
      chalk
    });
    result.status === "success" && result.aspects.length !== 0 && (output.print(), output.success(chalk.bold(`Deployed ${result.aspects.length} ${pluralize("aspect", result.aspects.length)}`)), output.print(list)), result.status === "failure" && result.aspects.length !== 0 && result.reason === "invalidAspect" && (output.print(), output.warn(chalk.bold(`Skipped ${result.aspects.length} invalid ${pluralize("aspect", result.aspects.length)}`)), output.print(list)), result.status === "failure" && result.aspects.length !== 0 && result.reason === "failedMutation" && (output.print(), output.error(chalk.bold(`Failed to deploy ${result.aspects.length} ${pluralize("aspect", result.aspects.length)}`)), output.print(list), output.print(), output.print(chalk.red(result.error)));
  });
}
function reportUnfoundAspect({
  aspectId,
  context
}) {
  const {
    output,
    chalk
  } = context;
  return pipe(scan((aspects, result) => aspects.concat(result.aspects), []), takeLast(1), tap((aspects) => {
    aspects.length === 0 && aspectId && (output.print(), output.error(`Could not find aspect: ${chalk.bold(aspectId)}`));
  }));
}
function formatAspectList({
  aspects,
  chalk
}) {
  return aspects.map(({
    aspect,
    filename,
    validationErrors
  }) => {
    const label = typeof aspect == "object" && aspect !== null && "_id" in aspect && typeof aspect._id < "u" ? aspect._id : "Unnamed aspect", simplifiedErrors = validationErrors.flatMap((group) => group.map(({
      message
    }) => message)), errorLabel = simplifiedErrors.length === 0 ? "" : ` ${chalk.bgRed(simplifiedErrors[0])}`, remainingErrorsCount = simplifiedErrors.length - 1, remainingErrorsLabel = remainingErrorsCount > 0 ? chalk.italic(` and ${simplifiedErrors.length - 1} other ${pluralize("error", remainingErrorsCount)}`) : "";
    return `  - ${label} ${chalk.dim(filename)}${errorLabel}${remainingErrorsLabel}`;
  }).join(EOL);
}
export {
  deployAspectAction as default
};
//# sourceMappingURL=deployAspectAction.js.map
