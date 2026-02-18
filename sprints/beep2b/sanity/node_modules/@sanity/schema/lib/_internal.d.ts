import { a as SchemaValidationResult, i as ProblemPathTypeSegment, l as Schema$1, n as ProblemPathPropertySegment, o as TypeWithProblems, r as ProblemPathSegment, s as _FIXME_, t as ProblemPath } from "./_chunks-dts/typedefs.js";
import { SetSynchronization, SynchronizationRequest, SynchronizationResult } from "@sanity/descriptors";
import * as _sanity_types2 from "@sanity/types";
import { Schema, SchemaType, SchemaTypeDefinition, SchemaValidationProblem, SchemaValidationProblemGroup } from "@sanity/types";
import { SchemaType as SchemaType$1 } from "groq-js";
/** The scheduler is capable of executing work in different ways. */
type Scheduler = {
  map<T, U>(arr: T[], fn: (val: T) => U): Promise<U[]>;
  forEach<T>(arr: T[], fn: (val: T) => void): Promise<void>;
  forEachIter<T>(iter: Iterable<T>, fn: (val: T) => void): Promise<void>;
};
type RegistryType = 'sanity.schema.registry';
declare class DescriptorConverter {
  cache: WeakMap<Schema, SetSynchronization<RegistryType>>;
  /**
   * Returns a synchronization object for a schema.
   *
   * This is automatically cached in a weak map.
   */
  get(schema: Schema, opts?: {
    /**
     * If present, this will use an idle scheduler which records duration into this array.
     * This option will be ignored if the `scheduler` option is passed in.
     **/
    pauseDurations?: number[]; /** An explicit scheduler to do the work. */
    scheduler?: Scheduler;
  }): Promise<SetSynchronization<RegistryType>>;
}
type SchemaSynchronizationRequest = SynchronizationRequest;
type SchemaSynchronizationResult = SynchronizationResult;
/**
 * Returns the next request that should be generated for synchronizing the
 * schema, based on the previous response from the /synchronize endpoint.
 *
 * @param response - The previous response, or `null` if it's the first request.
 * @returns The next request, or `null` if it's been fully synchronized.
 */
declare function processSchemaSynchronization(sync: SetSynchronization<RegistryType>, response: SchemaSynchronizationResult | null): SchemaSynchronizationRequest | null;
declare const isActionEnabled: (schemaType: SchemaType, action: string) => boolean;
declare const DEFAULT_MAX_FIELD_DEPTH = 5;
declare function resolveSearchConfigForBaseFieldPaths(type: any, maxDepth?: number): any;
/**
 * @internal
 */
declare function resolveSearchConfig(type: any, maxDepth?: number): any;
declare const ALL_FIELDS_GROUP_NAME = "all-fields";
declare const builtinTypes: ({
  name: string;
  title: string;
  type: string;
  fieldsets: {
    name: string;
    title: string;
    description: string;
  }[];
  fields: ({
    name: string;
    type: string;
    title: string;
    readOnly: boolean;
    hidden?: undefined;
    fieldset?: undefined;
  } | {
    name: string;
    type: string;
    title: string;
    readOnly?: undefined;
    hidden?: undefined;
    fieldset?: undefined;
  } | {
    name: string;
    type: string;
    title: string;
    readOnly: boolean;
    fieldset: string;
    hidden?: undefined;
  } | {
    name: string;
    type: string;
    readOnly: boolean;
    hidden: boolean;
    fieldset: string;
    title?: undefined;
  })[];
  preview: {
    select: {
      title: string;
      path: string;
      mimeType: string;
      size: string;
    };
    prepare(doc: Record<string, any>): {
      title: any;
      subtitle: string;
    };
  };
  orderings: {
    title: string;
    name: string;
    by: {
      field: string;
      direction: string;
    }[];
  }[];
} | {
  title: string;
  name: string;
  type: string;
  fields: {
    name: string;
    type: string;
    title: string;
  }[];
} | {
  name: string;
  title: string;
  type: string;
  fieldsets: {
    name: string;
    title: string;
    description: string;
  }[];
  fields: ({
    name: string;
    type: string;
    title: string;
    readOnly: boolean;
    hidden?: undefined;
    fieldset?: undefined;
  } | {
    name: string;
    type: string;
    title: string;
    readOnly?: undefined;
    hidden?: undefined;
    fieldset?: undefined;
  } | {
    name: string;
    type: string;
    title: string;
    readOnly: boolean;
    fieldset: string;
    hidden?: undefined;
  } | {
    title?: undefined;
    name: string;
    type: string;
    readOnly: boolean;
    hidden: boolean;
    fieldset: string;
  })[];
  preview: {
    select: {
      id: string;
      title: string;
      mimeType: string;
      size: string;
      media: string;
    };
    prepare(doc: Partial<_sanity_types2.SanityDocument>): {
      title: {};
      media: {
        asset: {
          _ref: unknown;
        };
        media?: {} | undefined;
      };
      subtitle: string;
    };
  };
  orderings: {
    title: string;
    name: string;
    by: {
      field: string;
      direction: string;
    }[];
  }[];
} | {
  name: string;
  title: string;
  type: string;
  fields: {
    name: string;
    type: string;
    validation: (Rule: _sanity_types2.Rule) => _sanity_types2.Rule;
  }[];
} | {
  name: string;
  title: string;
  type: string;
  fieldsets: {
    name: string;
    title: string;
    options: {
      collapsable: boolean;
    };
  }[];
  fields: ({
    title?: undefined;
    readOnly?: undefined;
    fieldset?: undefined;
    name: string;
    type: string;
  } | {
    readOnly?: undefined;
    name: string;
    title: string;
    type: string;
    fieldset: string;
  } | {
    fieldset?: undefined;
    name: string;
    title: string;
    type: string;
    readOnly: boolean;
  })[];
})[];
declare function createSchemaFromManifestTypes(schemaDef: {
  name: string;
  types: unknown[];
}): Schema$1;
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
declare function extractSchema(schemaDef: Schema, extractOptions?: ExtractSchemaOptions): SchemaType$1;
/**
 * @internal
 */
declare function groupProblems(types: SchemaTypeDefinition[]): SchemaValidationProblemGroup[];
/**
 * Ensure that the provided value is a valid Media Library asset aspect that can be safely deployed.
 *
 * @internal
 */
declare function validateMediaLibraryAssetAspect(maybeAspect: unknown): [isValidMediaLibraryAspect: boolean, validationErrors: SchemaValidationProblem[][]];
declare function validateBlockType(typeDef: any, visitorContext: any): {
  marks: any;
  styles: any;
  name: any;
  of: any;
  _problems: SchemaValidationResult[];
};
declare const typeVisitors: {
  array: (typeDef: any, visitorContext: any) => any;
  object: (typeDef: any, visitorContext: any) => any;
  slug: (typeDef: any, visitorContext: any) => any;
  file: (typeDef: any, visitorContext: any) => any;
  image: (typeDef: any, visitorContext: any) => any;
  block: typeof validateBlockType;
  document: (typeDefinition: any, visitorContext: any) => any;
  reference: (typeDef: any, visitorContext: any) => any;
  crossDatasetReference: (typeDef: any, visitorContext: any) => any;
  globalDocumentReference: (typeDef: any, visitorContext: any) => any;
};
interface Options {
  transformTypeVisitors?: (visitors: typeof typeVisitors) => Partial<typeof typeVisitors>;
  transformCommonVisitors?: (visitors: any[]) => any[];
}
/**
 * @internal
 */
declare function validateSchema(schemaTypes: _FIXME_, {
  transformTypeVisitors,
  transformCommonVisitors
}?: Options): {
  get(typeName: string): any;
  has(typeName: string): boolean;
  getTypeNames(): string[];
  getTypes(): any[];
  toJSON(): any[];
};
declare class ValidationError extends Error {
  problems: SchemaValidationProblemGroup[];
  constructor(problems: SchemaValidationProblemGroup[]);
}
export { ALL_FIELDS_GROUP_NAME, DEFAULT_MAX_FIELD_DEPTH, DescriptorConverter, type _FIXME_ as FIXME, type SchemaValidationResult as Problem, type SchemaValidationResult as ValidationResult, type ProblemPath, type ProblemPathPropertySegment, type ProblemPathSegment, type ProblemPathTypeSegment, SchemaSynchronizationRequest, SchemaSynchronizationResult, type TypeWithProblems, ValidationError, builtinTypes, createSchemaFromManifestTypes, extractSchema, groupProblems, isActionEnabled, processSchemaSynchronization, resolveSearchConfig, resolveSearchConfigForBaseFieldPaths, validateMediaLibraryAssetAspect, validateSchema };