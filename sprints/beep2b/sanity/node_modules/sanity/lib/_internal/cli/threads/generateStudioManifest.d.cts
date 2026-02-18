import { ClientConfig } from "@sanity/client";
import { StudioManifest } from "sanity";
/** @internal */
interface DeployedCreateSchema {
  name: string;
  projectId: string;
  dataset: string;
}
/** @internal */
interface DeployStudioWorkerData {
  workDir: string;
  clientConfig: Partial<ClientConfig>;
  sanityVersion: string;
}
/** @internal */
interface DeployStudioWorkerSuccess {
  type: 'success';
  /** The final studio manifest for deployment registration */
  studioManifest: StudioManifest | null;
}
/** @internal */
interface DeployStudioWorkerError {
  type: 'error';
  message: string;
  workspaceName?: string;
}
/** @internal */
type DeployStudioWorkerResult = DeployStudioWorkerSuccess | DeployStudioWorkerError;
export { DeployStudioWorkerData, DeployStudioWorkerError, DeployStudioWorkerResult, DeployStudioWorkerSuccess, DeployedCreateSchema };