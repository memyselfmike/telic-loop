import chalk from "chalk";
import { uniq } from "lodash-es";
import { parseDeleteSchemasConfig, ensureManifestExtractSatisfied, createSchemaApiClient, createManifestReader, projectIdDatasetPair, getProjectIdDatasetsOutString, getStringList, isDefined, createManifestExtractor } from "./schemaStoreOutStrings.js";
import { uniqueProjectIdDataset } from "./uniqueProjectIdDataset.js";
class DeleteIdError extends Error {
  constructor(args) {
    super(args.options?.cause?.message, args.options), this.name = "DeleteIdError", this.schemaId = args.schemaId, this.projectId = args.projectId, this.dataset = args.dataset;
  }
}
function deleteSchemasActionForCommand(flags, context) {
  return deleteSchemaAction(flags, {
    ...context,
    manifestExtractor: createManifestExtractor(context)
  });
}
async function deleteSchemaAction(flags, context) {
  const {
    ids,
    dataset,
    extractManifest,
    manifestDir,
    verbose
  } = parseDeleteSchemasConfig(flags, context), {
    output,
    apiClient,
    jsonReader,
    manifestExtractor
  } = context;
  if (!await ensureManifestExtractSatisfied({
    schemaRequired: !0,
    extractManifest,
    manifestDir,
    manifestExtractor,
    output,
    telemetry: context.telemetry
  }))
    return "failure";
  const {
    client
  } = createSchemaApiClient(apiClient), workspaces = (await createManifestReader({
    manifestDir,
    output,
    jsonReader
  }).getManifest()).workspaces.filter((workspace) => !dataset || workspace.dataset === dataset), projectDatasets = uniqueProjectIdDataset(workspaces), results = await Promise.allSettled(projectDatasets.flatMap(({
    projectId: targetProjectId,
    dataset: targetDataset
  }) => ids.map(async ({
    schemaId
  }) => {
    const targetClient = client.withConfig({
      projectId: targetProjectId,
      dataset: targetDataset
    });
    try {
      if (!await targetClient.getDocument(schemaId))
        return {
          projectId: targetProjectId,
          dataset: targetDataset,
          schemaId,
          deleted: !1
        };
      const deletedSchema = await targetClient.request({
        method: "DELETE",
        url: `/projects/${targetProjectId}/datasets/${targetDataset}/schemas/${schemaId}`
      });
      return {
        projectId: targetProjectId,
        dataset: targetDataset,
        schemaId,
        deleted: !!deletedSchema?.deleted
      };
    } catch (err) {
      throw new DeleteIdError({
        schemaId,
        projectId: targetProjectId,
        dataset: targetDataset,
        options: {
          cause: err
        }
      });
    }
  }))), deletedIds = results.filter((r) => r.status === "fulfilled").filter((r) => r.value.deleted).map((r) => r.value), deleteFailureIds = uniq(results.filter((r) => r.status === "rejected").map((result) => {
    const error = result.reason;
    if (error instanceof DeleteIdError)
      return output.error(chalk.red(`Failed to delete schema "${error.schemaId}" in "${projectIdDatasetPair(error)}":
${error.message}`)), verbose && output.error(error), error.schemaId;
    throw error;
  })), notFound = uniq(results.filter((r) => r.status === "fulfilled").filter((r) => !r.value.deleted).filter((r) => !deletedIds.map(({
    schemaId
  }) => schemaId).includes(r.value.schemaId) && !deleteFailureIds.includes(r.value.schemaId)).map((r) => r.value.schemaId)), success = deletedIds.length === ids.length;
  return success ? output.success(`Successfully deleted ${deletedIds.length}/${ids.length} schemas`) : output.error([`Deleted ${deletedIds.length}/${ids.length} schemas.`, deletedIds.length ? `Successfully deleted ids:
${deletedIds.map((result) => `- ${result.schemaId} (in ${projectIdDatasetPair(result)})`).join(`
`)}` : void 0, notFound.length ? `Ids not found in ${getProjectIdDatasetsOutString(projectDatasets)}:
${getStringList(notFound)}` : void 0, ...deleteFailureIds.length ? [`Failed to delete ids:
${getStringList(deleteFailureIds)}`, "Check logs for errors."] : []].filter(isDefined).join(`
`)), success ? "success" : "failure";
}
export {
  deleteSchemasActionForCommand as default,
  deleteSchemaAction
};
//# sourceMappingURL=deleteSchemaAction.js.map
