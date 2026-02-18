import { C as SanityUser, E as UserViteConfig, S as SanityModuleInternal, T as TelemetryUserProperties, _ as PackageJson, a as CliCommandContext, b as SanityCore, c as CliCommandRunner, d as CliPrompter, f as CliStubbedYarn, g as GraphQLAPIConfig, h as CommandRunnerOptions, i as CliCommandArguments, l as CliConfig, m as CliYarnOptions, n as CliApiConfig, o as CliCommandDefinition, p as CliUserConfig, r as CliCommandAction, s as CliCommandGroupDefinition, t as CliApiClient, u as CliOutputter, v as ReactCompilerConfig, w as SinglePrompt, x as SanityJson, y as ResolvedCliCommand } from "./_chunks-dts/types.js";
import { ClientConfig, SanityClient, SanityClient as SanityClient$1 } from "@sanity/client";
/**
 * `getCliClient` accepts all options the `ClientConfig` does but provides
 * `projectId` and `dataset` from the `sanity.cli.ts` configuration file along
 * with a token in certain scenarios (e.g. `sanity exec SCRIPT --with-user-token`)
 */
interface CliClientOptions extends ClientConfig {
  /**
   * If no `projectId` or `dataset` is provided, `getCliClient` will try to
   * resolve these from the `sanity.cli.ts` configuration file. Use this option
   * to specify the directory to look for this file.
   */
  cwd?: string;
}
interface GetCliClient {
  (options?: CliClientOptions): SanityClient$1;
  /**
   * @internal
   * @deprecated This is only for INTERNAL use, and should not be relied upon outside of official Sanity modules
   * @returns A token to use when constructing a client without a `token` explicitly defined, or undefined
   */
  __internal__getToken: () => string | undefined;
}
/** @internal */
declare const getCliClient: GetCliClient;
/** @beta */
declare function defineCliConfig(config: CliConfig): CliConfig;
/**
 * @deprecated Use `defineCliConfig` instead
 * @beta
 */
declare function createCliConfig(config: CliConfig): CliConfig;
/**
 * This is an "inlined" version of Vite's `loadEnv` function,
 * simplified somewhat to only support our use case.
 *
 * Ideally we'd just use `loadEnv` from Vite, but importing it
 * causes bundling issues due to node APIs and downstream dependencies.
 *
 * Vite is MIT licensed, copyright (c) Yuxi (Evan) You and Vite contributors.
 */
declare function loadEnv(mode: string, envDir: string, prefixes?: string[]): Record<string, string>;
export { CliApiClient, CliApiConfig, type CliClientOptions, CliCommandAction, CliCommandArguments, CliCommandContext, CliCommandDefinition, CliCommandGroupDefinition, CliCommandRunner, CliConfig, CliOutputter, CliPrompter, CliStubbedYarn, CliUserConfig, CliYarnOptions, CommandRunnerOptions, GraphQLAPIConfig, PackageJson, ReactCompilerConfig, ResolvedCliCommand, type SanityClient, SanityCore, SanityJson, SanityModuleInternal, SanityUser, SinglePrompt, TelemetryUserProperties, UserViteConfig, createCliConfig, defineCliConfig, getCliClient, loadEnv };