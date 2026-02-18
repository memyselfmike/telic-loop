import { MEDIA_LIBRARY_ASSET_ASPECT_TYPE_NAME } from "@sanity/types";
import { tap } from "rxjs";
import { determineTargetMediaLibrary, MINIMUM_API_VERSION } from "./determineTargetMediaLibrary.js";
const deleteAspectAction = async (args, context) => {
  const {
    output,
    chalk,
    apiClient,
    prompt
  } = context, [aspectName] = args.argsWithoutOptions;
  if (typeof aspectName > "u") {
    output.error("Specify an aspect name.");
    return;
  }
  const mediaLibraryId = args.extOptions["media-library-id"] ?? await determineTargetMediaLibrary(context);
  await prompt.single({
    type: "confirm",
    message: `Are you absolutely sure you want to undeploy the ${aspectName} aspect from the "${mediaLibraryId}" media library?`,
    default: !1
  }) && apiClient().withConfig({
    apiVersion: MINIMUM_API_VERSION
  }).observable.request({
    method: "POST",
    uri: `/media-libraries/${mediaLibraryId}/mutate`,
    body: {
      mutations: [{
        delete: {
          query: "*[_type == $type && _id == $id]",
          params: {
            id: aspectName,
            type: MEDIA_LIBRARY_ASSET_ASPECT_TYPE_NAME
          }
        }
      }]
    }
  }).pipe(tap({
    error(error) {
      output.print(), output.error(chalk.bold("Failed to delete aspect")), output.print(`  - ${aspectName}`), output.print(), output.print(chalk.red(error.message));
    },
    next(response) {
      if (response.results.length === 0) {
        output.print(), output.warn(chalk.bold("There's no deployed aspect with that name")), output.print(`  - ${aspectName}`);
        return;
      }
      output.print(), output.success(chalk.bold("Deleted aspect")), output.print(`  - ${aspectName}`);
    }
  })).subscribe();
};
export {
  deleteAspectAction as default
};
//# sourceMappingURL=deleteAspectAction.js.map
