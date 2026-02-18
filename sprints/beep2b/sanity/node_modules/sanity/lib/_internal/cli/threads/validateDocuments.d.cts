import { ValidationMarker } from "@sanity/types";
import { ClientConfig } from "@sanity/client";
/**
 * Represents the definition of a "worker channel" to report progress from the
 * worker to the parent. Worker channels can define named events or streams and
 * the worker will report events and streams while the parent will await them.
 * This allows the control flow of the parent to follow the control flow of the
 * worker 1-to-1.
 */
type WorkerChannel<TWorkerChannel extends Record<string, WorkerChannelEvent<unknown> | WorkerChannelStream<unknown>> = Record<string, WorkerChannelEvent<unknown> | WorkerChannelStream<unknown>>> = TWorkerChannel;
type WorkerChannelEvent<TPayload = void> = {
  type: 'event';
  payload: TPayload;
};
type WorkerChannelStream<TPayload = void> = {
  type: 'stream';
  payload: TPayload;
};
/** @internal */
interface ValidateDocumentsWorkerData {
  workDir: string;
  configPath?: string;
  workspace?: string;
  clientConfig?: Partial<ClientConfig>;
  projectId?: string;
  dataset?: string;
  ndjsonFilePath?: string;
  level?: ValidationMarker['level'];
  maxCustomValidationConcurrency?: number;
  maxFetchConcurrency?: number;
  studioHost?: string;
}
/** @internal */
type ValidationWorkerChannel = WorkerChannel<{
  loadedWorkspace: WorkerChannelEvent<{
    name: string;
    projectId: string;
    dataset: string;
    basePath: string;
  }>;
  loadedDocumentCount: WorkerChannelEvent<{
    documentCount: number;
  }>;
  exportProgress: WorkerChannelStream<{
    downloadedCount: number;
    documentCount: number;
  }>;
  exportFinished: WorkerChannelEvent<{
    totalDocumentsToValidate: number;
  }>;
  loadedReferenceIntegrity: WorkerChannelEvent;
  validation: WorkerChannelStream<{
    validatedCount: number;
    documentId: string;
    documentType: string;
    intentUrl?: string;
    revision: string;
    level: ValidationMarker['level'];
    markers: ValidationMarker[];
  }>;
}>;
export { ValidateDocumentsWorkerData, ValidationWorkerChannel };