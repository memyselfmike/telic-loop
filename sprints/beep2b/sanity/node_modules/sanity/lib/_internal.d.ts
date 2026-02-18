import { CliCommandDefinition, CliCommandGroupDefinition } from "@sanity/cli";
/**
 * @deprecated Not actually deprecated, but these are internals and should not be relied upon outside of the Sanity team
 * @internal
 */
declare const cliProjectCommands: {
  requiredCliVersionRange: string;
  commands: (CliCommandDefinition<Record<string, unknown>> | CliCommandGroupDefinition)[];
};
export { cliProjectCommands };