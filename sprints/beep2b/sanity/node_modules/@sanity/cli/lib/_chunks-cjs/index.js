"use strict";
var process = require("node:process"), fs = require("node:fs/promises"), node_url = require("node:url"), path = require("node:path");
function _interopDefaultCompat(e) {
  return e && typeof e == "object" && "default" in e ? e : { default: e };
}
var process__default = /* @__PURE__ */ _interopDefaultCompat(process), fs__default = /* @__PURE__ */ _interopDefaultCompat(fs), path__default = /* @__PURE__ */ _interopDefaultCompat(path);
const toPath = (urlOrPath) => urlOrPath instanceof URL ? node_url.fileURLToPath(urlOrPath) : urlOrPath;
async function findUp(name, {
  cwd = process__default.default.cwd(),
  type = "file",
  stopAt
} = {}) {
  let directory = path__default.default.resolve(toPath(cwd) ?? "");
  const { root } = path__default.default.parse(directory);
  stopAt = path__default.default.resolve(directory, toPath(stopAt ?? root));
  const isAbsoluteName = path__default.default.isAbsolute(name);
  for (; directory; ) {
    const filePath = isAbsoluteName ? name : path__default.default.join(directory, name);
    try {
      const stats = await fs__default.default.stat(filePath);
      if (type === "file" && stats.isFile() || type === "directory" && stats.isDirectory())
        return filePath;
    } catch {
    }
    if (directory === stopAt || directory === root)
      break;
    directory = path__default.default.dirname(directory);
  }
}
exports.findUp = findUp;
//# sourceMappingURL=index.js.map
