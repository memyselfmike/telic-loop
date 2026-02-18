"use strict";
var node = require("esbuild-register/dist/node");
node.register({
  target: `node${process.version.slice(1)}`,
  supported: {
    "dynamic-import": !0
  },
  format: "cjs"
});
//# sourceMappingURL=esbuild.cjs.map
