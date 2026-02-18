import { uniqBy } from "lodash-es";
function uniqueProjectIdDataset(workspaces) {
  return uniqBy(workspaces.map((w) => ({
    key: `${w.projectId}-${w.dataset}`,
    projectId: w.projectId,
    dataset: w.dataset
  })), "key");
}
export {
  uniqueProjectIdDataset
};
//# sourceMappingURL=uniqueProjectIdDataset.js.map
