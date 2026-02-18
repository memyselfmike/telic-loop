import fs from "node:fs/promises";
import path from "node:path";
import { createPublishedId } from "@sanity/id-utils";
import { camelCase } from "lodash-es";
import { withMediaLibraryConfig } from "./withMediaLibraryConfig.js";
const createAspectAction = async (args, context) => {
  const {
    output,
    chalk,
    prompt,
    mediaLibrary
  } = withMediaLibraryConfig(context), title = await prompt.single({
    message: "Title",
    type: "input"
  }), name = await prompt.single({
    message: "Name",
    type: "input",
    default: createPublishedId(camelCase(title))
  }), safeName = createPublishedId(camelCase(name)), destinationPath = path.resolve(mediaLibrary.aspectsPath, `${safeName}.ts`), relativeDestinationPath = path.relative(process.cwd(), destinationPath);
  if (await fs.mkdir(path.resolve(mediaLibrary.aspectsPath), {
    recursive: !0
  }), await fs.stat(destinationPath).then(() => !0).catch(() => !1)) {
    output.error(`A file already exists at ${chalk.bold(relativeDestinationPath)}`);
    return;
  }
  await fs.writeFile(destinationPath, template({
    name: safeName,
    title
  })), output.success(`Aspect created! ${chalk.bold(relativeDestinationPath)}`), output.print(), output.print("Next steps:"), output.print(`Open ${chalk.bold(relativeDestinationPath)} in your code editor and customize the aspect.`), output.print(), output.print("Deploy this aspect by running:"), output.print(chalk.bold(`sanity media deploy-aspect ${safeName}`)), output.print(), output.print("Deploy all aspects by running:"), output.print(chalk.bold("sanity media deploy-aspect --all"));
};
function template({
  name,
  title
}) {
  return `import {defineAssetAspect, defineField} from 'sanity'

export default defineAssetAspect({
  name: '${name}',
  title: '${title}',
  type: 'object',
  fields: [
    defineField({
      name: 'string',
      title: 'Plain String',
      type: 'string',
    }),
  ],
})
`;
}
export {
  createAspectAction as default
};
//# sourceMappingURL=createAspectAction.js.map
