import { _ as PackageJson } from "./_chunks-dts/types.js";
declare function runCli(cliRoot: string, {
  cliPkg
}: {
  cliPkg: PackageJson;
}): Promise<void>;
export { runCli };