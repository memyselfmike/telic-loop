import { firstValueFrom, mergeMap, filter, groupBy, zip, of, toArray } from "rxjs";
import { debug } from "./_internal.js";
const MINIMUM_API_VERSION = "v2025-02-19", ASPECT_FILE_EXTENSIONS = [".ts", ".js"];
async function determineTargetMediaLibrary({
  apiClient,
  output,
  prompt
}) {
  const client = apiClient().withConfig({
    apiVersion: "vX"
  }), {
    projectId
  } = client.config();
  if (typeof projectId > "u")
    throw new Error("Project id is required");
  debug("Fetching available media libraries");
  const spinner = output.spinner("Fetching available media libraries").start(), mediaLibrariesByOrganization = await firstValueFrom(client.observable.request({
    uri: "/media-libraries",
    query: {
      projectId
    }
  }).pipe(mergeMap((response) => response.data), filter(({
    status
  }) => status === "active"), groupBy(({
    organizationId
  }) => organizationId), mergeMap((group) => zip(of(group.key), group.pipe(toArray()))), toArray()));
  return spinner.succeed("[100%] Fetching available media libraries"), prompt.single({
    message: "Select media library",
    type: "list",
    choices: mediaLibrariesByOrganization.flatMap(([organizationId, mediaLibraries]) => [new prompt.Separator(`Organization: ${organizationId}`), ...mediaLibraries.map(({
      id
    }) => ({
      value: id,
      name: id
    }))])
  });
}
export {
  ASPECT_FILE_EXTENSIONS,
  MINIMUM_API_VERSION,
  determineTargetMediaLibrary
};
//# sourceMappingURL=determineTargetMediaLibrary.js.map
