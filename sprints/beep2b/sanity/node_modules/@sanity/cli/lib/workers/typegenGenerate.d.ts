import { TypegenWorkerChannel as TypegenWorkerChannel$1 } from "@sanity/codegen";
import { WorkerChannel } from "@sanity/worker-channels";
interface TypegenGenerateTypesWorkerData {
  workDir: string;
  schemaPath: string;
  searchPath: string | string[];
  overloadClientMethods?: boolean;
}
type TypegenWorkerChannel = WorkerChannel.Definition<{
  loadedSchema: WorkerChannel.Event;
  typegenStarted: WorkerChannel.Event<{
    expectedFileCount: number;
  }>;
  typegenComplete: WorkerChannel.Event<{
    code: string;
  }>;
} & TypegenWorkerChannel$1['__definition']>;
export { TypegenGenerateTypesWorkerData, TypegenWorkerChannel };