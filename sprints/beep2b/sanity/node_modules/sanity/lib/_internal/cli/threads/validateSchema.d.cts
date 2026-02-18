import { SchemaValidationProblem, SchemaValidationProblemGroup } from "@sanity/types";
/** @internal */
interface ValidateSchemaWorkerData {
  workDir: string;
  workspace?: string;
  level?: SchemaValidationProblem['severity'];
  debugSerialize?: boolean;
}
/** @internal */
interface ValidateSchemaWorkerResult {
  validation: SchemaValidationProblemGroup[];
  serializedDebug?: SeralizedSchemaDebug;
}
/**
 * Contains debug information about the serialized schema.
 *
 * @internal
 **/
type SeralizedSchemaDebug = {
  size: number;
  parent?: SeralizedSchemaDebug;
  types: Record<string, SerializedTypeDebug>;
  hoisted: Record<string, SerializedTypeDebug>;
};
/**
 * Contains debug information about a serialized type.
 *
 * @internal
 **/
type SerializedTypeDebug = {
  size: number;
  extends: string;
  fields?: Record<string, SerializedTypeDebug>;
  of?: Record<string, SerializedTypeDebug>;
};
export { SeralizedSchemaDebug, SerializedTypeDebug, ValidateSchemaWorkerData, ValidateSchemaWorkerResult };