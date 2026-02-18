import { SanityClient } from "@sanity/client";
import { TypeGenConfig } from "@sanity/codegen";
import { TelemetryLogger } from "@sanity/telemetry";
import { PluginOptions } from "babel-plugin-react-compiler";
import chalk from "chalk";
import { Answers, ChoiceCollection, DistinctQuestion, Separator } from "inquirer";
import { Options, Ora } from "ora";
import { ConfigEnv, InlineConfig } from "vite";
declare function getInstallCommand(options: {
  workDir: string;
  pkgNames?: string[];
  depType?: 'dev' | 'prod' | 'peer';
}): Promise<string>;
type PackageManager = 'npm' | 'yarn' | 'pnpm' | 'bun' | 'manual';
/**
 * Attempts to resolve the most optimal package manager to use to install/upgrade
 * packages/dependencies at a given path. It does so by looking for package manager
 * specific lockfiles. If it finds a lockfile belonging to a certain package manager,
 * it prioritizes this one. However, if that package manager is not installed, it will
 * prompt the user for which one they want to use and hint at the most optimal one
 * not being installed.
 *
 * Note that this function also takes local npm binary paths into account - for instance,
 * `yarn` can be installed as a dependency of the project instead of globally, and it
 * will use that is available.
 *
 * The user can also select 'manual' to skip the process and run their preferred package
 * manager manually. Commands using this function must take this `manual` choice into
 * account and act accordingly if chosen.
 *
 * @param workDir - The working directory where a lockfile is most likely to be present
 * @param options - Pass `interactive: false` to fall back to npm if most optimal is
 *                  not available, instead of prompting
 * @returns Object of `chosen` and, if a lockfile is found, the `mostOptimal` choice
 */
declare function getPackageManagerChoice(workDir: string, options: {
  interactive: false;
} | {
  interactive?: true;
  prompt: CliPrompter;
}): Promise<{
  chosen: PackageManager;
  mostOptimal?: PackageManager;
}>;
interface InstallOptions {
  packageManager: PackageManager;
  packages: string[];
}
declare function installNewPackages(options: InstallOptions, context: Pick<CliCommandContext, 'output' | 'workDir'>): Promise<void>;
/**
 * @internal
 */
declare const cliPackageManager: {
  getInstallCommand: typeof getInstallCommand;
  getPackageManagerChoice: typeof getPackageManagerChoice;
  installNewPackages: typeof installNewPackages;
};
/**
 * @internal
 */
type CliPackageManager = typeof cliPackageManager;
interface ClientRequirements {
  requireUser?: boolean;
  requireProject?: boolean;
  api?: {
    projectId?: string;
    dataset?: string;
    apiHost?: string;
    apiVersion?: string;
    requestTagPrefix?: string;
  };
}
type CliConfigResult = {
  config: CliConfig;
  path: string;
} | {
  config: null;
  path: string;
};
interface SanityCore {
  requiredCliVersionRange: string;
  commands: (CliCommandDefinition | CliCommandGroupDefinition)[];
}
interface SanityModuleInternal {
  cliProjectCommands: {
    requiredCliVersionRange: string;
    commands: (CliCommandDefinition | CliCommandGroupDefinition)[];
  };
}
interface PackageJson {
  name: string;
  version: string;
  scripts?: Record<string, string>;
  description?: string;
  author?: string;
  license?: string;
  private?: boolean;
  dependencies?: Record<string, string>;
  devDependencies?: Record<string, string>;
  peerDependencies?: Record<string, string>;
  repository?: {
    type: string;
    url: string;
  };
  engines?: Record<string, string>;
}
interface CliCommandGroupDefinition {
  name: string;
  signature: string;
  isGroupRoot: boolean;
  description: string;
  hideFromHelp?: boolean;
}
interface ResolvedCliCommand {
  command: CliCommandDefinition | CliCommandGroupDefinition;
  commandName: string;
  parentName?: string;
  isGroup: boolean;
  isCommand: boolean;
}
type CliCommandAction<F = Record<string, unknown>> = (args: CliCommandArguments<F>, context: CliCommandContext) => Promise<unknown>;
interface CliCommandDefinition<F = Record<string, unknown>> {
  name: string;
  group?: string;
  signature: string;
  description: string;
  helpText: string;
  action: CliCommandAction<F>;
  hideFromHelp?: boolean;
}
interface CliCommandArguments<F = Record<string, unknown>> {
  groupOrCommand: string;
  argv: string[];
  extOptions: F;
  argsWithoutOptions: string[];
  extraArguments: string[];
}
interface TelemetryUserProperties {
  runtime: string;
  runtimeVersion: string;
  cliVersion: string;
  machinePlatform: string;
  cpuArchitecture: string;
  projectId?: string;
  dataset?: string;
}
interface CliCommandContext {
  output: CliOutputter;
  prompt: CliPrompter;
  apiClient: CliApiClient;
  cliConfigPath?: string;
  cliRoot: string;
  workDir: string;
  corePath?: string;
  chalk: typeof chalk;
  commandRunner: CliCommandRunner;
  fromInitCommand?: boolean;
  cliConfig?: CliConfig;
  cliPackageManager: CliPackageManager;
  telemetry: TelemetryLogger<TelemetryUserProperties>;
}
interface CliCommandRunner {
  commands: Readonly<(CliCommandDefinition | CliCommandGroupDefinition)[]>;
  commandGroups: Readonly<Record<string, (CliCommandDefinition | CliCommandGroupDefinition)[]>>;
  runCommand(commandOrGroup: string, args: CliCommandArguments, options: CommandRunnerOptions): Promise<unknown>;
  resolveSubcommand(group: (CliCommandDefinition | CliCommandGroupDefinition)[], subCommandName: string, parentGroupName: string): ResolvedCliCommand | null;
}
interface CliUserConfig {
  cliLastUpdateCheck?: number;
  cliLastUpdateNag?: number;
  authToken?: string;
  authType?: string;
}
interface CommandRunnerOptions {
  cliConfig: CliConfigResult | null;
  cliRoot: string;
  workDir: string;
  corePath: string | undefined;
  telemetry: TelemetryLogger<TelemetryUserProperties>;
}
interface CliOutputter {
  print: (...args: unknown[]) => void;
  success: (...args: unknown[]) => void;
  warn: (...args: unknown[]) => void;
  error: (...args: unknown[]) => void;
  clear: () => void;
  spinner(options: Options | string): Ora;
}
type SinglePrompt = (Omit<DistinctQuestion, 'name'> & {
  type: 'list';
  choices: ChoiceCollection;
}) | (Omit<DistinctQuestion, 'name'> & {
  type: 'confirm';
}) | (Omit<DistinctQuestion, 'name'> & {
  type: 'input';
});
type CliPrompter = (<T extends Answers = Answers>(questions: DistinctQuestion<T>[]) => Promise<T>) & {
  Separator: typeof Separator;
  single: <T = string>(question: SinglePrompt) => Promise<T>;
};
type CliApiClient = (options?: ClientRequirements) => SanityClient;
interface CliYarnOptions {
  print?: CliOutputter['print'];
  error?: CliOutputter['error'];
  rootDir?: string;
}
type CliStubbedYarn = (args: string[], options?: CliYarnOptions) => Promise<void>;
interface CliApiConfig {
  projectId?: string;
  dataset?: string;
}
interface SanityJson {
  root?: boolean;
  project?: {
    name?: string;
    basePath?: string;
  };
  api?: CliApiConfig;
  __experimental_spaces?: {
    name: string;
    title: string;
    default?: true;
    api: {
      projectId?: string;
      dataset?: string;
    };
  }[];
  plugins?: string[];
  parts?: {
    name?: string;
    path?: string;
    implements?: string;
    description?: string;
  }[];
  env?: {
    production?: SanityJson;
    staging?: SanityJson;
    development?: SanityJson;
  };
}
interface GraphQLAPIConfig {
  /**
   * ID of GraphQL API. Only (currently) required when using the `--api` flag
   * for `sanity graphql deploy`, in order to only deploy a specific API.
   */
  id?: string;
  /**
   * Name of workspace containing the schema to deploy
   *
   * Optional, defaults to `default` (eg the one used if no `name` is defined)
   */
  workspace?: string;
  /**
   * Name of source containing the schema to deploy, within the configured workspace
   *
   * Optional, defaults to `default` (eg the one used if no `name` is defined)
   */
  source?: string;
  /**
   * API tag for this API - allows deploying multiple different APIs to a single dataset
   *
   * Optional, defaults to `default`
   */
  tag?: string;
  /**
   * Whether or not to deploy a "GraphQL Playground" to the API url - an HTML interface that allows
   * running queries and introspecting the schema from the browser. Note that this interface is not
   * secured in any way, but as the schema definition and API route is generally open, this does not
   * expose any more information than is otherwise available - it only makes it more discoverable.
   *
   * Optional, defaults to `true`
   */
  playground?: boolean;
  /**
   * Generation of API to auto-generate from schema. New APIs should use the latest (`gen3`).
   *
   * Optional, defaults to `gen3`
   */
  generation?: 'gen3' | 'gen2' | 'gen1';
  /**
   * Define document interface fields (`_id`, `_type` etc) as non-nullable.
   * If you never use a document type as an object (within other documents) in your schema types,
   * you can (and probably should) set this to `true`. Because a document type _could_ be used
   * inside other documents, it is by default set to `false`, as in these cases these fields
   * _can_ be null.
   *
   * Optional, defaults to `false`
   */
  nonNullDocumentFields?: boolean;
  /**
   * Suffix to use for generated filter types.
   *
   * Optional, Defaults to `Filter`.
   *
   */
  filterSuffix?: string;
}
/**
 * @beta
 */
type ReactCompilerConfig = Partial<PluginOptions>;
interface AppConfig {
  /**
   * The ID of your Sanity organization
   */
  organizationId: string;
  /**
   * The entrypoint for your Sanity app. Defaults to './src/App'.
   */
  entry?: string;
  /**
   * @deprecated - Moved to `deployment.appId`
   */
  id?: string;
}
interface CliConfig {
  api?: CliApiConfig;
  project?: {
    basePath?: string;
  };
  /**
   * Wraps the Studio in `<React.StrictMode>` root to aid flagging potential problems related to concurrent features (`startTransition`, `useTransition`, `useDeferredValue`, `Suspense`)
   * Can also be enabled by setting `SANITY_STUDIO_REACT_STRICT_MODE="true"|"false"`.
   * It only applies to `sanity dev` in dev mode, it's ignored in `sanity build` and in production.
   * Defaults to `false`
   */
  reactStrictMode?: boolean;
  /**
   * The React Compiler is currently in beta, and is disabled by default.
   * @see https://react.dev/learn/react-compiler
   * @beta
   */
  reactCompiler?: ReactCompilerConfig;
  server?: {
    hostname?: string;
    port?: number;
  };
  graphql?: GraphQLAPIConfig[];
  vite?: UserViteConfig;
  /**
   * @deprecated - Moved to deployment.autoUpdates
   */
  autoUpdates?: boolean;
  /**
   * @deprecated - Replaced by deployment.appId
   */
  studioHost?: string;
  /**
   * Parameter used to configure other kinds of applications.
   * Signals to `sanity` commands that this is not a studio.
   */
  app?: AppConfig;
  /**
   * Deployment configuration
   */
  deployment?: {
    /**
     * The ID of your Sanity studio or app. Generated when deploying your studio or app for the first time.
     * Get the appId either by
     * - Checking the output of `sanity deploy`.
     * - Get it from your project's Studio tab in https://www.sanity.io/manage
     */
    appId?: string;
    /**
     * Enable auto-updates for studios.
     * {@link https://www.sanity.io/docs/studio/latest-version-of-sanity#k47faf43faf56}
     */
    autoUpdates?: boolean;
  };
  /**
   * Configuration for Sanity media libraries.
   */
  mediaLibrary?: {
    /**
     * The path to the Media Library aspects directory. When using the CLI to manage aspects, this
     * is the directory they will be read from and written to.
     */
    aspectsPath: string;
  };
  /**
   * Configuration for Sanity typegen
   */
  typegen?: Partial<TypeGenConfig> & {
    /**
     * Enable typegen as part of sanity dev and sanity build.
     * When enabled, types are generated on startup and when files change.
     * Defaults to `false`
     */
    enabled?: boolean;
  };
  /**
   * Configuration for schema extraction
   */
  schemaExtraction?: {
    /**
     * Enable schema extraction as part of sanity dev and sanity build
     */
    enabled?: boolean;
    /**
     * Output path for the extracted schema file.
     * Defaults to `schema.json` in the working directory.
     */
    path?: string;
    /**
     * When true, schema fields marked as required will be non-optional in the output.
     * Defaults to `false`
     */
    enforceRequiredFields?: boolean;
    /**
     * Additional glob patterns to watch for schema changes in watch mode.
     * These extend the default patterns:
     * - `sanity.config.{js,jsx,ts,tsx,mjs}`
     * - `schema*\/**\/*.{js,jsx,ts,tsx,mjs}`
     */
    watchPatterns?: string[];
    /**
     * The name of the workspace to generate a schema for. Required if your Sanity project has more than one
     * workspace.
     */
    workspace?: string;
  };
}
type UserViteConfig = InlineConfig | ((config: InlineConfig, env: ConfigEnv) => InlineConfig | Promise<InlineConfig>);
type SanityUser = {
  id: string;
  name: string;
  email: string;
  profileImage?: string;
  tosAcceptedAt?: string;
  provider: 'google' | 'github' | 'sanity' | `saml-${string}`;
};
export { SanityUser as C, UserViteConfig as E, SanityModuleInternal as S, TelemetryUserProperties as T, PackageJson as _, CliCommandContext as a, SanityCore as b, CliCommandRunner as c, CliPrompter as d, CliStubbedYarn as f, GraphQLAPIConfig as g, CommandRunnerOptions as h, CliCommandArguments as i, CliConfig as l, CliYarnOptions as m, CliApiConfig as n, CliCommandDefinition as o, CliUserConfig as p, CliCommandAction as r, CliCommandGroupDefinition as s, CliApiClient as t, CliOutputter as u, ReactCompilerConfig as v, SinglePrompt as w, SanityJson as x, ResolvedCliCommand as y };