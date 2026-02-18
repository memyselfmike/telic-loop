import { isatty } from "node:tty";
import { generateHelpUrl } from "./index.js";
import chalk from "chalk";
import logSymbols from "log-symbols";
const isTty = isatty(1), headers = {
  error: isTty ? chalk.bold(chalk.bgRed(chalk.black(" ERROR "))) : chalk.red("[ERROR]"),
  warning: isTty ? chalk.bold(chalk.bgYellow(chalk.black(" WARN "))) : chalk.yellow("[WARN]")
}, severityValues = {
  error: 0,
  warning: 1
};
function formatPath(pathSegments) {
  const format = ([curr, ...next], mode = "object") => {
    if (!curr) return "";
    if (curr.kind === "property") return format(next, curr.name === "of" ? "array" : "object");
    const name = curr.name ? curr.name : `<anonymous_${curr.type}>`;
    return `${mode === "array" ? `[${name}]` : `.${name}`}${format(next)}`;
  };
  return format(pathSegments.slice(1)).slice(1);
}
function getAggregatedSeverity(groupOrGroups) {
  return (Array.isArray(groupOrGroups) ? groupOrGroups : [groupOrGroups]).flatMap((group) => group.problems.map((problem) => problem.severity)).find((severity) => severity === "error") ? "error" : "warning";
}
function formatSchemaValidation(validation) {
  let unnamedTopLevelTypeCount = 0;
  return Object.entries(validation.reduce((acc, next) => {
    const [firstSegment] = next.path;
    if (!firstSegment || firstSegment.kind !== "type") return acc;
    const topLevelType = firstSegment.name || `<unnamed_${firstSegment.type}_type_${unnamedTopLevelTypeCount++}>`, problems = acc[topLevelType] ?? [];
    return problems.push(next), acc[topLevelType] = problems, acc;
  }, {})).sort((a, b) => {
    const [aType, aGroups] = a, [bType, bGroups] = b, aValue = severityValues[getAggregatedSeverity(aGroups)], bValue = severityValues[getAggregatedSeverity(bGroups)];
    return aValue === bValue ? aType.localeCompare(bType, "en-US") : aValue - bValue;
  }).map(([topLevelType, groups]) => {
    const formattedTopLevelType = isTty ? chalk.bgWhite(chalk.black(` ${topLevelType} `)) : `[${topLevelType}]`, header = `${headers[getAggregatedSeverity(groups)]} ${formattedTopLevelType}`, body = groups.sort((a, b) => severityValues[getAggregatedSeverity(a)] - severityValues[getAggregatedSeverity(b)]).map((group) => {
      const formattedPath = `  ${chalk.bold(formatPath(group.path) || "(root)")}`, formattedMessages = group.problems.sort((a, b) => severityValues[a.severity] - severityValues[b.severity]).map(({
        severity,
        message,
        helpId
      }) => {
        const help = helpId ? `
      See ${generateHelpUrl(helpId)}` : "";
        return `    ${logSymbols[severity]} ${message}${help}`;
      }).join(`
`);
      return `${formattedPath}
${formattedMessages}`;
    }).join(`
`);
    return `${header}
${body}`;
  }).join(`

`);
}
export {
  formatSchemaValidation,
  getAggregatedSeverity
};
//# sourceMappingURL=formatSchemaValidation.js.map
