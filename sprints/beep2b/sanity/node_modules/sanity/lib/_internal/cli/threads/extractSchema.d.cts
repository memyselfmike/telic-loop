import { Schema, SchemaValidationProblem, SchemaValidationProblemGroup } from "@sanity/types";
import { SchemaType } from "groq-js";
interface ExtractSchemaOptions {
  enforceRequiredFields?: boolean;
}
/**
 * Extracts a GROQ-compatible schema from a Sanity schema definition. The extraction happens in three passes:
 *
 * 1. **Dependency analysis & hoisting detection** (`sortByDependencies`): Walks the entire schema to sort
 *    types topologically and identifies inline object fields that are used multiple times (candidates
 *    for "hoisting").
 *
 * 2. **Hoisted type creation**: For any repeated inline fields, we create top-level named type definitions
 *    first, so they exist before being referenced.
 *
 * 3. **Main type conversion**: Processes each schema type in dependency order. When a field was marked for
 *    hoisting, we emit an `inline` reference to the hoisted type instead of duplicating the structure.
 */
declare function extractSchema(schemaDef: Schema, extractOptions?: ExtractSchemaOptions): SchemaType;
/**
 * @internal
 */
/** @internal */
interface ExtractSchemaWorkerData {
  workDir: string;
  workspaceName?: string;
  enforceRequiredFields?: boolean;
  format: 'groq-type-nodes' | string;
}
/** @internal */
interface ExtractSchemaWorkerResult {
  type: 'success';
  schema: ReturnType<typeof extractSchema>;
}
/** @internal */
interface ExtractSchemaWorkerError {
  type: 'error';
  error: string;
  validation?: SchemaValidationProblemGroup[];
}
/** @internal */
type ExtractSchemaWorkerMessage = ExtractSchemaWorkerResult | ExtractSchemaWorkerError;
export { ExtractSchemaWorkerData, ExtractSchemaWorkerError, ExtractSchemaWorkerMessage, ExtractSchemaWorkerResult };