import path, { isAbsolute } from "node:path";
import { fileURLToPath } from "node:url";
import debug$4 from "debug";
import readPkgUp from "read-pkg-up";
import { escapeRegExp, debounce, once, mean } from "lodash-es";
import { getAppEnvironmentVariables, getStudioEnvironmentVariables } from "./cli.js";
import fs$1 from "node:fs/promises";
import logSymbols from "log-symbols";
import picomatch from "picomatch";
import { SchemaExtractedTrace, SchemaExtractionWatchModeTrace, SchemaExtractionError, extractSchemaToFile } from "./schemaExtractorApi.js";
import { formatSchemaValidation } from "./formatSchemaValidation.js";
import fs, { existsSync } from "node:fs";
import { TypesGeneratedTrace, TypegenWatchModeTrace, runTypegenGenerate } from "@sanity/codegen";
import chokidar from "chokidar";
import { jsxs, Fragment, jsx } from "react/jsx-runtime";
import { Worker, parentPort, isMainThread, workerData } from "node:worker_threads";
import chalk from "chalk";
import importFresh from "import-fresh";
import { parse } from "node-html-parser";
import { renderToStaticMarkup } from "react-dom/server";
import { c } from "react/compiler-runtime";
const debug$3 = debug$4("sanity:server");
function createExternalFromImportMap({
  imports = {}
} = {}) {
  return Object.keys(imports).map((specifier) => specifier.endsWith("/") ? new RegExp(`^${escapeRegExp(specifier)}.+`) : specifier);
}
function normalizeBasePath(pathName) {
  return `/${pathName}/`.replace(/^\/+/, "/").replace(/\/+$/, "/");
}
function Favicons() {
  const $ = c(1);
  let t0;
  return $[0] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t0 = /* @__PURE__ */ jsxs(Fragment, { children: [
    /* @__PURE__ */ jsx("link", { rel: "icon", href: "/static/favicon.ico", sizes: "any" }),
    /* @__PURE__ */ jsx("link", { rel: "icon", href: "/static/favicon.svg", type: "image/svg+xml" }),
    /* @__PURE__ */ jsx("link", { rel: "apple-touch-icon", href: "/static/apple-touch-icon.png" }),
    /* @__PURE__ */ jsx("link", { rel: "manifest", href: "/static/manifest.webmanifest" })
  ] }), $[0] = t0) : t0 = $[0], t0;
}
const errorHandlerScript = `
;(function () {
  // The error channel is provided so that error handling can be delegated to a view component.
  // If there is a subscriber to the error channel at the time the error happens, the error will be pushed to the subscriber instead of handled here.
  var errorChannel = (function () {
    var subscribers = Object.create(null)
    var nextId = 0
    function subscribe(subscriber) {
      var id = nextId++
      subscribers[id] = subscriber
      return function unsubscribe() {
        delete subscribers[id]
      }
    }

    function publish(event) {
      for (var id in subscribers) {
        if (Object.hasOwn(subscribers, id)) {
          subscribers[id](event)
        }
      }
    }
    return {
      subscribers,
      publish,
      subscribe
    }
  })()

  // NOTE: Store the error channel instance in the global scope so that the Studio application can
  // access it and subscribe to errors.
  window.__sanityErrorChannel = {
    subscribe: errorChannel.subscribe
  }

  function _handleError(event) {
    // If there are error channel subscribers, then we assume they will own error rendering,
    // and we defer to them (no console error).
    if (Object.keys(errorChannel.subscribers).length > 0) {
      errorChannel.publish(event)
    } else {
      _renderErrorOverlay(event)
    }
  }

  var ERROR_BOX_STYLE = [
    'background: #fff',
    'border-radius: 6px',
    'box-sizing: border-box',
    'color: #121923',
    'flex: 1',
    "font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'Helvetica Neue','Liberation Sans',Helvetica,Arial,system-ui,sans-serif",
    'font-size: 16px',
    'line-height: 21px',
    'margin: 0 auto',
    'max-width: 960px',
    'max-height: 90dvh',
    'overflow: auto',
    'padding: 20px',
    'width: 100%',
  ].join(';')

  var ERROR_CODE_STYLE = [
    'color: #972E2A',
    "font-family: -apple-system-ui-monospace, 'SF Mono', Menlo, Monaco, Consolas, monospace",
    'font-size: 13px',
    'line-height: 17px',
    'margin: 0',
  ].join(';')

  function _renderErrorOverlay(event) {
    var errorElement = document.querySelector('#__sanityError') || document.createElement('div')
    var error = event.error
    var colno = event.colno
    var lineno = event.lineno
    var filename = event.filename

    errorElement.id = '__sanityError'
    errorElement.innerHTML = [
      '<div style="' + ERROR_BOX_STYLE + '">',
      '<div style="font-weight: 700;">Uncaught error: ' + error.message + '</div>',
      '<div style="color: #515E72; font-size: 13px; line-height: 17px; margin: 10px 0;">' +
        filename +
        ':' +
        lineno +
        ':' +
        colno +
        '</div>',
      '<pre style="' + ERROR_CODE_STYLE + '">' + error.stack + '</pre>',
      '</div>',
    ].join('')

    errorElement.style.position = 'fixed'
    errorElement.style.zIndex = 1000000
    errorElement.style.top = 0
    errorElement.style.left = 0
    errorElement.style.right = 0
    errorElement.style.bottom = 0
    errorElement.style.padding = '20px'
    errorElement.style.background = 'rgba(16,17,18,0.66)'
    errorElement.style.display = 'flex'
    errorElement.style.alignItems = 'center'
    errorElement.style.justifyContent = 'center'

    document.body.appendChild(errorElement)
  }

  // Error listener
  window.addEventListener('error', (event) => {
    _handleError({
      type: 'error',
      error: event.error,
      lineno: event.lineno,
      colno: event.colno,
      filename: event.filename
    })
  })

  // Error listener
  window.addEventListener('unhandledrejection', (event) => {
    _handleError({
      type: 'rejection',
      error: event.reason
    })
  })
})()
`;
function GlobalErrorHandler() {
  const $ = c(1);
  let t0;
  return $[0] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t0 = /* @__PURE__ */ jsx("script", { dangerouslySetInnerHTML: {
    __html: errorHandlerScript
  } }), $[0] = t0) : t0 = $[0], t0;
}
const NoJsStyles = `
.sanity-app-no-js__root {
  position: absolute;
  top: 0;
  right: 0;
  left: 0;
  bottom: 0;
  background: #fff;
}

.sanity-app-no-js__content {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  font-family: helvetica, arial, sans-serif;
}
`;
function NoJavascript() {
  const $ = c(3);
  let t0, t1;
  $[0] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t0 = /* @__PURE__ */ jsx("style", { type: "text/css", children: NoJsStyles }), t1 = /* @__PURE__ */ jsx("h1", { children: "JavaScript disabled" }), $[0] = t0, $[1] = t1) : (t0 = $[0], t1 = $[1]);
  let t2;
  return $[2] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t2 = /* @__PURE__ */ jsx("noscript", { children: /* @__PURE__ */ jsx("div", { className: "sanity-app-no-js__root", children: /* @__PURE__ */ jsxs("div", { className: "sanity-app-no-js__content", children: [
    t0,
    t1,
    /* @__PURE__ */ jsxs("p", { children: [
      "Please ",
      /* @__PURE__ */ jsx("a", { href: "https://www.enable-javascript.com/", children: "enable JavaScript" }),
      " in your browser and reload the page to proceed."
    ] })
  ] }) }) }), $[2] = t2) : t2 = $[2], t2;
}
const EMPTY_ARRAY$1 = [];
function BasicDocument(props) {
  const $ = c(20), {
    entryPath,
    css: t0
  } = props, css = t0 === void 0 ? EMPTY_ARRAY$1 : t0;
  let t1, t2, t3, t4, t5, t6, t7;
  $[0] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t1 = /* @__PURE__ */ jsx("meta", { charSet: "utf-8" }), t2 = /* @__PURE__ */ jsx("meta", { name: "viewport", content: "width=device-width, initial-scale=1, viewport-fit=cover" }), t3 = /* @__PURE__ */ jsx("meta", { name: "robots", content: "noindex" }), t4 = /* @__PURE__ */ jsx("meta", { name: "referrer", content: "same-origin" }), t5 = /* @__PURE__ */ jsx(Favicons, {}), t6 = /* @__PURE__ */ jsx("title", { children: "Sanity Custom App" }), t7 = /* @__PURE__ */ jsx(GlobalErrorHandler, {}), $[0] = t1, $[1] = t2, $[2] = t3, $[3] = t4, $[4] = t5, $[5] = t6, $[6] = t7) : (t1 = $[0], t2 = $[1], t3 = $[2], t4 = $[3], t5 = $[4], t6 = $[5], t7 = $[6]);
  let t8;
  $[7] !== css ? (t8 = css.map(_temp$1), $[7] = css, $[8] = t8) : t8 = $[8];
  let t9;
  $[9] !== t8 ? (t9 = /* @__PURE__ */ jsxs("head", { children: [
    t1,
    t2,
    t3,
    t4,
    t5,
    t6,
    t7,
    t8
  ] }), $[9] = t8, $[10] = t9) : t9 = $[10];
  let t10;
  $[11] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t10 = /* @__PURE__ */ jsx("div", { id: "root" }), $[11] = t10) : t10 = $[11];
  let t11;
  $[12] !== entryPath ? (t11 = /* @__PURE__ */ jsx("script", { type: "module", src: entryPath }), $[12] = entryPath, $[13] = t11) : t11 = $[13];
  let t12;
  $[14] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t12 = /* @__PURE__ */ jsx(NoJavascript, {}), $[14] = t12) : t12 = $[14];
  let t13;
  $[15] !== t11 ? (t13 = /* @__PURE__ */ jsxs("body", { children: [
    t10,
    t11,
    t12
  ] }), $[15] = t11, $[16] = t13) : t13 = $[16];
  let t14;
  return $[17] !== t13 || $[18] !== t9 ? (t14 = /* @__PURE__ */ jsxs("html", { lang: "en", children: [
    t9,
    t13
  ] }), $[17] = t13, $[18] = t9, $[19] = t14) : t14 = $[19], t14;
}
function _temp$1(href) {
  return /* @__PURE__ */ jsx("link", { rel: "stylesheet", href }, href);
}
const globalStyles = `
  @font-face {
    font-family: Inter;
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-Regular.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: italic;
    font-weight: 400;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-Italic.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: normal;
    font-weight: 500;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-Medium.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: italic;
    font-weight: 500;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-MediumItalic.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: normal;
    font-weight: 600;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-SemiBold.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: italic;
    font-weight: 600;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-SemiBoldItalic.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: normal;
    font-weight: 700;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-Bold.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: italic;
    font-weight: 700;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-BoldItalic.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: normal;
    font-weight: 800;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-ExtraBold.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: italic;
    font-weight: 800;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-ExtraBoldItalic.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: normal;
    font-weight: 900;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-Black.woff2") format("woff2");
  }
  @font-face {
    font-family: Inter;
    font-style: italic;
    font-weight: 900;
    font-display: swap;
    src: url("https://studio-static.sanity.io/Inter-BlackItalic.woff2") format("woff2");
  }
  html {
    @media (prefers-color-scheme: dark) {
      background-color: #13141b;
    }
    @media (prefers-color-scheme: light) {
      background-color: #ffffff;
    }
  }
  html,
  body,
  #sanity {
    height: 100%;
  }
  body {
    margin: 0;
    -webkit-font-smoothing: antialiased;
  }
`, EMPTY_ARRAY = [];
function DefaultDocument(props) {
  const $ = c(21), {
    entryPath,
    css: t0
  } = props, css = t0 === void 0 ? EMPTY_ARRAY : t0;
  let t1, t2, t3, t4, t5, t6, t7;
  $[0] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t1 = /* @__PURE__ */ jsx("meta", { charSet: "utf-8" }), t2 = /* @__PURE__ */ jsx("meta", { name: "viewport", content: "width=device-width, initial-scale=1, maximum-scale=1, viewport-fit=cover" }), t3 = /* @__PURE__ */ jsx("meta", { name: "robots", content: "noindex" }), t4 = /* @__PURE__ */ jsx("meta", { name: "referrer", content: "same-origin" }), t5 = /* @__PURE__ */ jsx(Favicons, {}), t6 = /* @__PURE__ */ jsx("title", { children: "Sanity Studio" }), t7 = /* @__PURE__ */ jsx(GlobalErrorHandler, {}), $[0] = t1, $[1] = t2, $[2] = t3, $[3] = t4, $[4] = t5, $[5] = t6, $[6] = t7) : (t1 = $[0], t2 = $[1], t3 = $[2], t4 = $[3], t5 = $[4], t6 = $[5], t7 = $[6]);
  let t8;
  $[7] !== css ? (t8 = css.map(_temp), $[7] = css, $[8] = t8) : t8 = $[8];
  let t9;
  $[9] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t9 = /* @__PURE__ */ jsx("style", { dangerouslySetInnerHTML: {
    __html: globalStyles
  } }), $[9] = t9) : t9 = $[9];
  let t10;
  $[10] !== t8 ? (t10 = /* @__PURE__ */ jsxs("head", { children: [
    t1,
    t2,
    t3,
    t4,
    t5,
    t6,
    t7,
    t8,
    t9
  ] }), $[10] = t8, $[11] = t10) : t10 = $[11];
  let t11;
  $[12] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t11 = /* @__PURE__ */ jsx("div", { id: "sanity" }), $[12] = t11) : t11 = $[12];
  let t12;
  $[13] !== entryPath ? (t12 = /* @__PURE__ */ jsx("script", { type: "module", src: entryPath }), $[13] = entryPath, $[14] = t12) : t12 = $[14];
  let t13;
  $[15] === /* @__PURE__ */ Symbol.for("react.memo_cache_sentinel") ? (t13 = /* @__PURE__ */ jsx(NoJavascript, {}), $[15] = t13) : t13 = $[15];
  let t14;
  $[16] !== t12 ? (t14 = /* @__PURE__ */ jsxs("body", { children: [
    t11,
    t12,
    t13
  ] }), $[16] = t12, $[17] = t14) : t14 = $[17];
  let t15;
  return $[18] !== t10 || $[19] !== t14 ? (t15 = /* @__PURE__ */ jsxs("html", { lang: "en", children: [
    t10,
    t14
  ] }), $[18] = t10, $[19] = t14, $[20] = t15) : t15 = $[20], t15;
}
function _temp(href) {
  return /* @__PURE__ */ jsx("link", { rel: "stylesheet", href }, href);
}
const TIMESTAMPED_IMPORTMAP_INJECTOR_SCRIPT = `<script>
  // auto-generated script to add import map with timestamp
  const importsJson = document.getElementById('__imports')?.textContent;
  const { imports = {}, ...rest } = importsJson ? JSON.parse(importsJson) : {};
  const importMapEl = document.createElement('script');
  importMapEl.type = 'importmap';
  const newTimestamp = \`/t\${Math.floor(Date.now() / 1000)}\`;
  importMapEl.textContent = JSON.stringify({
    imports: Object.fromEntries(
      Object.entries(imports).map(([specifier, path]) => {
        try {
          const url = new URL(path);
          if (/^sanity-cdn\\.[a-zA-Z]+$/.test(url.hostname)) {
            url.pathname = url.pathname.replace(/\\/t\\d+/, newTimestamp);
          }
          return [specifier, url.toString()];
        } catch {
          return [specifier, path];
        }
      })
    ),
    ...rest,
  });
  document.head.appendChild(importMapEl);
<\/script>`, __filename$1 = fileURLToPath(import.meta.url);
path.dirname(__filename$1);
const debug$2 = debug$3.extend("renderDocument"), useThreads = typeof process.env.JEST_WORKER_ID > "u", hasWarnedAbout = /* @__PURE__ */ new Set(), defaultProps = {
  entryPath: "./.sanity/runtime/app.js"
}, autoGeneratedWarning = `
This file is auto-generated from "sanity dev".
Modifications to this file are automatically discarded.
`.trim();
function renderDocument(options) {
  return new Promise((resolve, reject) => {
    if (!useThreads) {
      resolve(getDocumentHtml(options.studioRootPath, options.props, options.importMap, options.isApp));
      return;
    }
    debug$2("Starting worker thread for %s", __filename$1);
    const worker = new Worker(__filename$1, {
      execArgv: void 0,
      workerData: {
        ...options,
        dev: !1,
        shouldWarn: !0
      },
      env: process.env
    });
    worker.on("message", (msg) => {
      if (msg.type === "warning") {
        if (hasWarnedAbout.has(msg.warnKey))
          return;
        Array.isArray(msg.message) ? msg.message.forEach((warning) => console.warn(`${chalk.yellow("[warn]")} ${warning}`)) : console.warn(`${chalk.yellow("[warn]")} ${msg.message}`), hasWarnedAbout.add(msg.warnKey);
        return;
      }
      if (msg.type === "error") {
        debug$2("Error from worker: %s", msg.error || "Unknown error"), reject(new Error(msg.error || "Document rendering worker stopped with an unknown error"));
        return;
      }
      msg.type === "result" && (debug$2("Document HTML rendered, %d bytes", msg.html.length), resolve(msg.html));
    }), worker.on("error", (err) => {
      debug$2("Worker errored: %s", err.message), reject(err);
    }), worker.on("exit", (code) => {
      code !== 0 && (debug$2("Worker stopped with code %d", code), reject(new Error(`Document rendering worker stopped with exit code ${code}`)));
    });
  });
}
function decorateIndexWithAutoGeneratedWarning(template) {
  return template.replace(/<head/, `
<!--
${autoGeneratedWarning}
-->
<head`);
}
function decorateIndexWithBridgeScript(template) {
  const scriptURL = (process.env.SANITY_INTERNAL_ENV || "production") === "production" ? "https://core.sanity-cdn.com/bridge.js" : "https://core.sanity-cdn.work/bridge.js";
  return template.replace("</head>", `<script src="${scriptURL}" async type="module" data-sanity-core><\/script>
</head>`);
}
function getPossibleDocumentComponentLocations(studioRootPath) {
  return [path.join(studioRootPath, "_document.js"), path.join(studioRootPath, "_document.tsx")];
}
function _prefixUrlWithBasePath(url, basePath) {
  const normalizedBasePath = basePath.startsWith("/") ? basePath : `/${basePath}`;
  return url.startsWith("/") ? normalizedBasePath.endsWith("/") ? `${normalizedBasePath.slice(0, -1)}${url}` : `${normalizedBasePath}${url}` : normalizedBasePath.endsWith("/") ? `${normalizedBasePath}${url}` : `${normalizedBasePath}/${url}`;
}
!isMainThread && parentPort && renderDocumentFromWorkerData();
async function renderDocumentFromWorkerData() {
  if (!parentPort || !workerData)
    throw new Error("Must be used as a Worker with a valid options object in worker data");
  const {
    studioRootPath,
    props,
    importMap,
    isApp
  } = workerData || {};
  if (workerData?.dev && (global.__DEV__ = !0), typeof studioRootPath != "string") {
    parentPort.postMessage({
      type: "error",
      message: "Missing/invalid `studioRootPath` option"
    });
    return;
  }
  if (props && typeof props != "object") {
    parentPort.postMessage({
      type: "error",
      message: "`props` must be an object if provided"
    });
    return;
  }
  debug$2("Registering esbuild for node %s", process.version);
  const {
    register
  } = await import("esbuild-register/dist/node"), {
    unregister
  } = register({
    target: `node${process.version.slice(1)}`,
    supported: {
      "dynamic-import": !0
    },
    jsx: "automatic",
    extensions: [".jsx", ".ts", ".tsx", ".mjs"],
    format: "cjs"
  });
  debug$2("Registering esbuild for .js files using jsx loader");
  const {
    unregister: unregisterJs
  } = register({
    target: `node${process.version.slice(1)}`,
    supported: {
      "dynamic-import": !0
    },
    extensions: [".js"],
    jsx: "automatic",
    loader: "jsx",
    format: "cjs"
  }), html = getDocumentHtml(studioRootPath, props, importMap, isApp);
  parentPort.postMessage({
    type: "result",
    html
  }), unregister(), unregisterJs();
}
function getDocumentHtml(studioRootPath, props, importMap, isApp) {
  const Document = getDocumentComponent(studioRootPath, isApp), css = props?.css?.map((url) => {
    try {
      return new URL(url).toString();
    } catch {
      return _prefixUrlWithBasePath(url, props.basePath);
    }
  });
  return debug$2("Rendering document component using React"), `<!DOCTYPE html>${addTimestampedImportMapScriptToHtml(renderToStaticMarkup(/* @__PURE__ */ jsx(Document, { ...defaultProps, ...props, css })), importMap)}`;
}
function addTimestampedImportMapScriptToHtml(html, importMap) {
  if (!importMap) return html;
  let root = parse(html), htmlEl = root.querySelector("html");
  if (!htmlEl) {
    const oldRoot = root;
    root = parse("<html></html>"), htmlEl = root.querySelector("html"), htmlEl.appendChild(oldRoot);
  }
  let headEl = htmlEl.querySelector("head");
  return headEl || (htmlEl.insertAdjacentHTML("afterbegin", "<head></head>"), headEl = root.querySelector("head")), headEl.insertAdjacentHTML("beforeend", `<script type="application/json" id="__imports">${JSON.stringify(importMap)}<\/script>`), headEl.insertAdjacentHTML("beforeend", TIMESTAMPED_IMPORTMAP_INJECTOR_SCRIPT), root.outerHTML;
}
function getDocumentComponent(studioRootPath, isApp) {
  debug$2("Loading default document component from `sanity` module");
  const Document = isApp ? BasicDocument : DefaultDocument;
  debug$2("Attempting to load user-defined document component from %s", studioRootPath);
  const userDefined = tryLoadDocumentComponent(studioRootPath);
  if (!userDefined)
    return debug$2("Using default document component"), Document;
  debug$2("Found user defined document component at %s", userDefined.path);
  const DocumentComp = userDefined.component.default || userDefined.component;
  if (typeof DocumentComp == "function")
    return debug$2("User defined document component is a function, assuming valid"), DocumentComp;
  debug$2("User defined document component did not have a default export");
  const userExports = Object.keys(userDefined.component).join(", ") || "None", relativePath = path.relative(process.cwd(), userDefined.path), typeHint = typeof userDefined.component.default > "u" ? "" : ` (type was ${typeof userDefined.component.default})`, warnKey = `${relativePath}/${userDefined.modified}`;
  return parentPort?.postMessage({
    type: "warning",
    message: [`${relativePath} did not have a default export that is a React component${typeHint}`, `Named exports/properties found: ${userExports}`.trim(), 'Using default document component from "sanity".'],
    warnKey
  }), DefaultDocument;
}
function tryLoadDocumentComponent(studioRootPath) {
  const locations = getPossibleDocumentComponentLocations(studioRootPath);
  for (const componentPath of locations) {
    debug$2("Trying to load document component from %s", componentPath);
    try {
      return {
        component: importFresh(componentPath),
        path: componentPath,
        modified: Math.floor(fs.statSync(componentPath)?.mtimeMs)
      };
    } catch (err) {
      if (err.code !== "MODULE_NOT_FOUND")
        throw debug$2("Failed to load document component: %s", err.message), err;
      debug$2("Document component not found at %s", componentPath);
    }
  }
  return null;
}
const entryChunkId = ".sanity/runtime/app.js";
function sanityBuildEntries(options) {
  const {
    cwd,
    basePath,
    importMap,
    isApp
  } = options;
  return {
    name: "sanity/server/build-entries",
    apply: "build",
    buildStart() {
      this.emitFile({
        type: "chunk",
        id: entryChunkId,
        name: "sanity"
      });
    },
    async generateBundle(_options, outputBundle) {
      const bundle = outputBundle, entryFile = Object.values(bundle).find((file) => file.type === "chunk" && file.name === "sanity" && file.facadeModuleId?.endsWith(entryChunkId));
      if (!entryFile)
        throw new Error(`Failed to find entry file in bundle (${entryChunkId})`);
      if (entryFile.type !== "chunk")
        throw new Error("Entry file is not a chunk");
      const entryFileName = entryFile.fileName, entryPath = [basePath.replace(/\/+$/, ""), entryFileName].join("/");
      let css = [];
      if (entryFile.viteMetadata?.importedCss) {
        css = [...entryFile.viteMetadata.importedCss];
        for (const key of entryFile.imports) {
          const entry = bundle[key], importedCss = entry && entry.type === "chunk" ? entry.viteMetadata.importedCss : void 0;
          importedCss && css.push(...importedCss);
        }
      }
      this.emitFile({
        type: "asset",
        fileName: "index.html",
        source: decorateIndexWithBridgeScript(await renderDocument({
          studioRootPath: cwd,
          importMap,
          props: {
            basePath,
            entryPath,
            css
          },
          isApp
        }))
      });
    }
  };
}
function generateWebManifest(basePath) {
  return {
    icons: [{
      src: `${basePath}/favicon-96.png`,
      type: "image/png",
      sizes: "96x96"
    }, {
      src: `${basePath}/favicon-192.png`,
      type: "image/png",
      sizes: "192x192"
    }, {
      src: `${basePath}/favicon-512.png`,
      type: "image/png",
      sizes: "512x512"
    }]
  };
}
const mimeTypes = {
  ".ico": "image/x-icon",
  ".svg": "image/svg+xml",
  ".png": "image/png"
};
function sanityFaviconsPlugin({
  defaultFaviconsPath,
  customFaviconsPath,
  staticUrlPath
}) {
  const cache = {};
  async function getFavicons() {
    return cache.favicons || (cache.favicons = await fs$1.readdir(defaultFaviconsPath)), cache.favicons;
  }
  async function hasCustomFavicon(fileName) {
    try {
      return await fs$1.access(path.join(customFaviconsPath, fileName)), !0;
    } catch {
      return !1;
    }
  }
  return {
    name: "sanity/server/sanity-favicons",
    apply: "serve",
    configureServer(viteDevServer) {
      const webManifest = JSON.stringify(generateWebManifest(staticUrlPath), null, 2), webManifestPath = `${staticUrlPath}/manifest.webmanifest`;
      viteDevServer.middlewares.use(async (req, res, next) => {
        if (req.url?.endsWith(webManifestPath)) {
          res.writeHead(200, "OK", {
            "content-type": "application/manifest+json"
          }), res.write(webManifest), res.end();
          return;
        }
        const pathName = (req._parsedUrl || new URL(req.url || "/", "http://localhost:3333")).pathname || "", fileName = path.basename(pathName || ""), icons = await getFavicons();
        if (!(pathName.startsWith("/favicon.ico") || icons.includes(fileName) && pathName.includes(staticUrlPath))) {
          next();
          return;
        }
        const faviconPath = await hasCustomFavicon(fileName) ? path.join(customFaviconsPath, fileName) : path.join(defaultFaviconsPath, fileName), mimeType = mimeTypes[path.extname(fileName)] || "application/octet-stream";
        res.writeHead(200, "OK", {
          "content-type": mimeType
        }), res.write(await fs$1.readFile(faviconPath)), res.end();
      });
    }
  };
}
function sanityRuntimeRewritePlugin() {
  return {
    name: "sanity/server/sanity-runtime-rewrite",
    apply: "serve",
    configureServer(viteDevServer) {
      return () => {
        viteDevServer.middlewares.use((req, res, next) => {
          req.url === "/index.html" && (req.url = "/.sanity/runtime/index.html"), next();
        });
      };
    }
  };
}
const DEFAULT_SCHEMA_PATTERNS = ["sanity.config.{js,jsx,ts,tsx,mjs}", "schema*/**/*.{js,jsx,ts,tsx,mjs}"], DEFAULT_DEBOUNCE_MS$1 = 1e3, INITIAL_EXTRACTION_DELAY_MS = 1e3;
function sanitySchemaExtractionPlugin(options = {}) {
  const {
    workDir: workDirOption,
    outputPath: outputPathOption = "schema.json",
    output = console,
    workspaceName,
    additionalPatterns = [],
    debounceMs = DEFAULT_DEBOUNCE_MS$1,
    enforceRequiredFields = !1,
    telemetryLogger,
    format = "groq-type-nodes"
  } = options, watchPatterns = [...DEFAULT_SCHEMA_PATTERNS, ...additionalPatterns];
  let resolvedWorkDir, resolvedOutputPath, isExtracting = !1, pendingExtraction = !1;
  const startTime = Date.now(), stats = {
    successfulDurations: [],
    failedCount: 0
  }, extractSchema = () => extractSchemaToFile({
    workDir: resolvedWorkDir,
    outputPath: resolvedOutputPath,
    workspaceName,
    enforceRequiredFields,
    format
  });
  async function runExtraction(isBuilding = !1) {
    if (isExtracting) {
      pendingExtraction = !0;
      return;
    }
    isExtracting = !0, pendingExtraction = !1;
    const extractionStartTime = Date.now();
    try {
      await extractSchema(), isBuilding && output.log(""), output.log(logSymbols.success, `Extracted schema to ${outputPathOption}`), stats.successfulDurations.push(Date.now() - extractionStartTime);
    } catch (err) {
      output.log(logSymbols.error, `Extraction failed: ${err instanceof Error ? err.message : String(err)}`), err instanceof SchemaExtractionError && err.validation && err.validation.length > 0 && output.log(logSymbols.error, formatSchemaValidation(err.validation)), stats.failedCount++;
    } finally {
      isExtracting = !1, pendingExtraction && (pendingExtraction = !1, await runExtraction());
    }
  }
  const debouncedExtract = debounce(() => {
    runExtraction();
  }, debounceMs), isMatch = picomatch(watchPatterns);
  return {
    name: "sanity/schema-extraction",
    configResolved(config) {
      resolvedWorkDir = workDirOption ?? config.root, isAbsolute(outputPathOption) ? resolvedOutputPath = outputPathOption : resolvedOutputPath = path.join(resolvedWorkDir, outputPathOption);
    },
    configureServer(server) {
      const trace = telemetryLogger?.trace(SchemaExtractionWatchModeTrace);
      trace?.start(), trace?.log({
        step: "started",
        enforceRequiredFields,
        schemaFormat: format
      });
      const absolutePatterns = watchPatterns.map((pattern) => path.join(resolvedWorkDir, pattern));
      server.watcher.add(absolutePatterns);
      const handleChange = (filePath) => {
        const relativePath = path.isAbsolute(filePath) ? path.relative(resolvedWorkDir, filePath) : filePath;
        isMatch(relativePath) && debouncedExtract();
      }, onClose = once(() => {
        trace && (trace.log({
          step: "stopped",
          watcherDuration: Date.now() - startTime,
          extractionSuccessfulCount: stats.successfulDurations.length,
          extractionFailedCount: stats.failedCount,
          averageExtractionDuration: mean(stats.successfulDurations)
        }), trace.complete());
      });
      server.watcher.on("change", handleChange), server.watcher.on("add", handleChange), server.watcher.on("unlink", handleChange), server.watcher.on("close", onClose), process.on("SIGTERM", onClose), process.on("SIGINT", onClose);
      const startExtraction = () => {
        setTimeout(() => {
          output.info(logSymbols.info, "Schema extraction enabled. Watching:");
          for (const pattern of watchPatterns)
            output.info(`  - ${pattern}`);
          runExtraction();
        }, INITIAL_EXTRACTION_DELAY_MS);
      };
      server.httpServer ? server.httpServer.once("listening", startExtraction) : startExtraction();
    },
    async buildEnd() {
      const trace = telemetryLogger?.trace(SchemaExtractedTrace);
      trace?.start();
      try {
        const start = Date.now(), schema = await extractSchema();
        console.error(`\u2713 Extract schema (${Date.now() - start}ms)`), trace?.log({
          schemaAllTypesCount: schema.length,
          schemaDocumentTypesCount: schema.filter((type) => type.type === "document").length,
          schemaTypesCount: schema.filter((type) => type.type === "type").length,
          enforceRequiredFields,
          schemaFormat: format
        });
      } catch (err) {
        throw trace?.error(err), err;
      } finally {
        trace?.complete();
      }
    }
  };
}
const DEFAULT_QUERY_PATTERNS = ["./src/**/*.{ts,tsx,js,jsx}", "./app/**/*.{ts,tsx,js,jsx}"], DEFAULT_DEBOUNCE_MS = 1e3, INITIAL_GENERATION_DELAY_MS = 1e3;
function sanityTypegenPlugin(options) {
  const {
    workDir,
    config: inputConfig,
    output = console,
    telemetryLogger
  } = options, config = {
    schema: inputConfig.schema ?? "schema.json",
    generates: inputConfig.generates ?? "sanity.types.ts",
    path: inputConfig.path ?? DEFAULT_QUERY_PATTERNS,
    overloadClientMethods: inputConfig.overloadClientMethods ?? !1,
    formatGeneratedCode: inputConfig.formatGeneratedCode ?? !1
  }, queryPatterns = Array.isArray(config.path) ? config.path : [config.path];
  let resolvedSchemaPath, isGenerating = !1, pendingGeneration = !1;
  const startTime = Date.now(), stats = {
    successfulDurations: [],
    failedCount: 0
  };
  async function runGeneration(isBuilding = !1) {
    if (isGenerating)
      return pendingGeneration = !0, null;
    isGenerating = !0, pendingGeneration = !1;
    const generationStartTime = Date.now();
    try {
      if (!existsSync(resolvedSchemaPath))
        return output.error(`${logSymbols.error} Schema file not found: ${config.schema}
Run "sanity schema extract" first to generate the schema file.`), null;
      const result = await runTypegenGenerate({
        workDir,
        config
      });
      return isBuilding && output.log(""), result.filesWithErrors > 0 ? output.log(logSymbols.warning, `Generated types to ${config.generates} (with errors in ${result.filesWithErrors} file${result.filesWithErrors === 1 ? "" : "s"})`) : output.log(logSymbols.success, `Generated types to ${config.generates}`), stats.successfulDurations.push(Date.now() - generationStartTime), result;
    } catch (err) {
      return output.error(`${logSymbols.error} Generation failed: ${err instanceof Error ? err.message : String(err)}`), stats.failedCount++, null;
    } finally {
      isGenerating = !1, pendingGeneration && (pendingGeneration = !1, runGeneration());
    }
  }
  const debouncedGenerate = debounce(() => {
    runGeneration();
  }, DEFAULT_DEBOUNCE_MS), isQueryMatch = picomatch(queryPatterns);
  return {
    name: "sanity/typegen",
    configResolved(viteConfig) {
      const rootDir = workDir ?? viteConfig.root;
      resolvedSchemaPath = path.isAbsolute(config.schema) ? config.schema : path.join(rootDir, config.schema), path.isAbsolute(config.generates) ? config.generates : path.join(rootDir, config.generates);
    },
    configureServer(server) {
      const trace = telemetryLogger?.trace(TypegenWatchModeTrace);
      trace?.start(), trace?.log({
        step: "started"
      });
      const absoluteQueryPatterns = queryPatterns.map((pattern) => path.isAbsolute(pattern) ? pattern : path.join(workDir, pattern));
      server.watcher.add([...absoluteQueryPatterns, resolvedSchemaPath]);
      const handleChange = (filePath) => {
        const relativePath = path.isAbsolute(filePath) ? path.relative(workDir, filePath) : filePath;
        (filePath === resolvedSchemaPath || isQueryMatch(relativePath)) && debouncedGenerate();
      }, onClose = once(() => {
        trace && (trace.log({
          step: "stopped",
          watcherDuration: Date.now() - startTime,
          generationSuccessfulCount: stats.successfulDurations.length,
          generationFailedCount: stats.failedCount,
          averageGenerationDuration: mean(stats.successfulDurations) || 0
        }), trace.complete());
      });
      server.watcher.on("change", handleChange), server.watcher.on("add", handleChange), server.watcher.on("unlink", handleChange), server.watcher.on("close", onClose), process.on("SIGTERM", onClose), process.on("SIGINT", onClose);
      const startGeneration = () => {
        setTimeout(() => {
          output.info(logSymbols.info, "Typegen enabled. Watching:");
          for (const pattern of queryPatterns)
            output.info(`  - ${pattern}`);
          output.info(`  - ${config.schema} (schema)`), runGeneration();
        }, INITIAL_GENERATION_DELAY_MS);
      };
      server.httpServer ? server.httpServer.once("listening", startGeneration) : startGeneration();
    },
    async buildEnd() {
      const result = await runGeneration(!0);
      if (result && telemetryLogger) {
        const trace = telemetryLogger.trace(TypesGeneratedTrace);
        trace.start(), trace.log({
          outputSize: result.code.length,
          queriesCount: result.queriesCount,
          schemaTypesCount: result.schemaTypesCount,
          queryFilesCount: result.queryFilesCount,
          filesWithErrors: result.filesWithErrors,
          typeNodesGenerated: result.typeNodesGenerated,
          unknownTypeNodesGenerated: result.unknownTypeNodesGenerated,
          unknownTypeNodesRatio: result.typeNodesGenerated > 0 ? result.unknownTypeNodesGenerated / result.typeNodesGenerated : 0,
          emptyUnionTypeNodesGenerated: result.emptyUnionTypeNodesGenerated,
          configOverloadClientMethods: config.overloadClientMethods ?? !1,
          configMethod: "cli"
        }), trace.complete();
      }
    }
  };
}
const __dirname$1 = path.dirname(fileURLToPath(import.meta.url));
async function getViteConfig(options) {
  const {
    cwd,
    mode,
    outputDir,
    // default to `true` when `mode=development`
    sourceMap = options.mode === "development",
    server,
    minify,
    basePath: rawBasePath = "/",
    importMap,
    reactCompiler,
    isApp,
    typegen,
    telemetryLogger,
    schemaExtraction
  } = options, basePath = normalizeBasePath(rawBasePath), sanityPkgPath = (await readPkgUp({
    cwd: __dirname$1
  }))?.path;
  if (!sanityPkgPath)
    throw new Error("Unable to resolve `sanity` module root");
  const customFaviconsPath = path.join(cwd, "static"), defaultFaviconsPath = path.join(path.dirname(sanityPkgPath), "static", "favicons"), staticPath = `${basePath}static`, {
    default: viteReact
  } = await import("@vitejs/plugin-react"), envVars = isApp ? getAppEnvironmentVariables({
    prefix: "process.env.",
    jsonEncode: !0
  }) : getStudioEnvironmentVariables({
    prefix: "process.env.",
    jsonEncode: !0
  }), viteConfig = {
    // Define a custom cache directory so that sanity's vite cache
    // does not conflict with any potential local vite projects
    cacheDir: "node_modules/.sanity/vite",
    root: cwd,
    base: basePath,
    build: {
      outDir: outputDir || path.resolve(cwd, "dist"),
      sourcemap: sourceMap
    },
    server: {
      host: server?.host,
      port: server?.port || 3333,
      // Only enable strict port for studio,
      // since apps can run on any port
      strictPort: !isApp,
      /**
       * Significantly speed up startup time,
       * and most importantly eliminates the `new dependencies optimized: foobar. optimized dependencies changed. reloading`
       * types of initial reload loops that otherwise happen as vite discovers deps that need to be optimized.
       * This option starts the traversal up front, and warms up the dep tree required to render the userland sanity.config.ts file,
       * and thus avoids frustrating reload loops.
       */
      warmup: {
        clientFiles: ["./.sanity/runtime/app.js"]
      }
    },
    configFile: !1,
    mode,
    plugins: [
      viteReact(reactCompiler ? {
        babel: {
          plugins: [["babel-plugin-react-compiler", reactCompiler]],
          generatorOpts: {
            compact: !0
          }
        }
      } : {}),
      sanityFaviconsPlugin({
        defaultFaviconsPath,
        customFaviconsPath,
        staticUrlPath: staticPath
      }),
      sanityRuntimeRewritePlugin(),
      sanityBuildEntries({
        basePath,
        cwd,
        importMap,
        isApp
      }),
      // Add typegen plugin when enabled
      ...typegen?.enabled ? [sanityTypegenPlugin({
        workDir: cwd,
        config: typegen,
        telemetryLogger
      })] : [],
      // Add schema extraction when enabled
      ...schemaExtraction?.enabled ? [sanitySchemaExtractionPlugin({
        workDir: cwd,
        outputPath: schemaExtraction.path,
        workspaceName: schemaExtraction.workspace,
        additionalPatterns: schemaExtraction.watchPatterns,
        enforceRequiredFields: schemaExtraction.enforceRequiredFields,
        telemetryLogger
      })] : []
    ],
    envPrefix: isApp ? "SANITY_APP_" : "SANITY_STUDIO_",
    logLevel: mode === "production" ? "silent" : "info",
    resolve: {
      dedupe: ["react", "react-dom", "sanity", "styled-components"]
    },
    define: {
      __SANITY_STAGING__: process.env.SANITY_INTERNAL_ENV === "staging",
      __SANITY_BUILD_TIMESTAMP__: JSON.stringify(Date.now()),
      "process.env.PKG_BUILD_VERSION": JSON.stringify(process.env.PKG_BUILD_VERSION),
      "process.env.MODE": JSON.stringify(mode),
      /**
       * Yes, double negatives are confusing.
       * The default value of `SC_DISABLE_SPEEDY` is `process.env.NODE_ENV === 'production'`: https://github.com/styled-components/styled-components/blob/99c02f52d69e8e509c0bf012cadee7f8e819a6dd/packages/styled-components/src/constants.ts#L34
       * Which means that in production, use the much faster way of inserting CSS rules, based on the CSSStyleSheet API (https://developer.mozilla.org/en-US/docs/Web/API/CSSStyleSheet/insertRule)
       * while in dev mode, use the slower way of inserting CSS rules, which appends text nodes to the `<style>` tag: https://github.com/styled-components/styled-components/blob/99c02f52d69e8e509c0bf012cadee7f8e819a6dd/packages/styled-components/src/sheet/Tag.ts#L74-L76
       * There are historical reasons for this, primarily that browsers initially did not support editing CSS rules in the DevTools inspector if `CSSStyleSheet.insetRule` were used.
       * However, that's no longer the case (since Chrome 81 back in April 2020: https://developer.chrome.com/docs/css-ui/css-in-js), the latest version of FireFox also supports it,
       * and there is no longer any reason to use the much slower method in dev mode.
       */
      "process.env.SC_DISABLE_SPEEDY": JSON.stringify("false"),
      ...envVars
    }
  };
  return mode === "production" && (viteConfig.build = {
    ...viteConfig.build,
    assetsDir: "static",
    minify: minify ? "esbuild" : !1,
    emptyOutDir: !1,
    // Rely on CLI to do this
    rollupOptions: {
      onwarn: onRollupWarn,
      external: createExternalFromImportMap(importMap),
      input: {
        sanity: path.join(cwd, ".sanity", "runtime", "app.js")
      }
    }
  }), viteConfig;
}
function onRollupWarn(warning, warn) {
  suppressUnusedImport(warning) || warn(warning);
}
function suppressUnusedImport(warning) {
  return warning.code !== "UNUSED_EXTERNAL_IMPORT" ? !1 : !!(warning.names?.includes("useDebugValue") && (warning.names = warning.names.filter((n) => n !== "useDebugValue"), warning.names.length === 0) || warning.ids?.every((id) => id.includes("/node_modules/")));
}
async function finalizeViteConfig(config) {
  if (typeof config.build?.rollupOptions?.input != "object")
    throw new Error("Vite config must contain `build.rollupOptions.input`, and it must be an object");
  if (!config.root)
    throw new Error("Vite config must contain `root` property, and must point to the Sanity root directory");
  const {
    mergeConfig
  } = await import("vite");
  return mergeConfig(config, {
    build: {
      rollupOptions: {
        input: {
          sanity: path.join(config.root, ".sanity", "runtime", "app.js")
        }
      }
    }
  });
}
async function extendViteConfigWithUserConfig(env, defaultConfig, userConfig) {
  let config = defaultConfig;
  if (typeof userConfig == "function")
    debug$4("Extending vite config using user-specified function"), config = await userConfig(config, env);
  else if (typeof userConfig == "object") {
    debug$4("Merging vite config using user-specified object");
    const {
      mergeConfig
    } = await import("vite");
    config = mergeConfig(config, userConfig);
  }
  return config;
}
const entryModule = `
// This file is auto-generated on 'sanity dev'
// Modifications to this file are automatically discarded
import studioConfig from %STUDIO_CONFIG_LOCATION%
import {renderStudio} from "sanity"

renderStudio(
  document.getElementById("sanity"),
  studioConfig,
  {reactStrictMode: %STUDIO_REACT_STRICT_MODE%, basePath: %STUDIO_BASE_PATH%}
)
`, noConfigEntryModule = `
// This file is auto-generated on 'sanity dev'
// Modifications to this file are automatically discarded
import {renderStudio} from "sanity"

const studioConfig = {missingConfigFile: true}

renderStudio(
  document.getElementById("sanity"),
  studioConfig,
  {reactStrictMode: %STUDIO_REACT_STRICT_MODE%, basePath: %STUDIO_BASE_PATH%}
)
`, appEntryModule = `
// This file is auto-generated on 'sanity dev'
// Modifications to this file are automatically discarded
import {createRoot} from 'react-dom/client'
import {createElement} from 'react'
import App from %ENTRY%

const root = createRoot(document.getElementById('root'))
const element = createElement(App)
root.render(element)
`;
function getEntryModule(options) {
  const {
    reactStrictMode,
    relativeConfigLocation,
    basePath,
    entry,
    isApp
  } = options;
  return isApp ? appEntryModule.replace(/%ENTRY%/, JSON.stringify(entry || "./src/App")) : (relativeConfigLocation ? entryModule : noConfigEntryModule).replace(/%STUDIO_REACT_STRICT_MODE%/, JSON.stringify(!!reactStrictMode)).replace(/%STUDIO_CONFIG_LOCATION%/, JSON.stringify(relativeConfigLocation)).replace(/%STUDIO_BASE_PATH%/, JSON.stringify(basePath || "/"));
}
const debug$1 = debug$3.extend("config");
async function getSanityStudioConfigPath(studioRootPath) {
  const configPaths = [path.join(studioRootPath, "sanity.config.mjs"), path.join(studioRootPath, "sanity.config.js"), path.join(studioRootPath, "sanity.config.ts"), path.join(studioRootPath, "sanity.config.jsx"), path.join(studioRootPath, "sanity.config.tsx")];
  debug$1("Looking for configuration file in %d possible locations", configPaths.length);
  const availableConfigs = (await Promise.all(configPaths.map(async (configPath) => ({
    path: configPath,
    exists: await fileExists(configPath)
  })))).filter((config) => config.exists);
  return debug$1("Found %d available configuration files", availableConfigs.length), availableConfigs.length === 0 ? (console.warn("No `sanity.config.js`/`sanity.config.ts` found - using default studio config"), null) : (availableConfigs.length > 1 && (console.warn("Found multiple potential studio configs:"), availableConfigs.forEach((config) => console.warn(` - ${config.path}`)), console.warn(`Using ${availableConfigs[0].path}`)), availableConfigs[0].path);
}
function fileExists(filePath) {
  return fs$1.stat(filePath).then(() => !0, () => !1);
}
const debug = debug$3.extend("runtime");
function toForwardSlashes(filePath) {
  return filePath.replace(/\\/g, "/");
}
async function writeSanityRuntime({
  cwd,
  reactStrictMode,
  watch,
  basePath,
  entry,
  isApp
}) {
  debug("Making runtime directory");
  const runtimeDir = path.join(cwd, ".sanity", "runtime");
  await fs$1.mkdir(runtimeDir, {
    recursive: !0
  });
  async function renderAndWriteDocument() {
    debug("Rendering document template");
    const indexHtml = decorateIndexWithBridgeScript(decorateIndexWithAutoGeneratedWarning(await renderDocument({
      studioRootPath: cwd,
      props: {
        entryPath: `/${toForwardSlashes(path.relative(cwd, path.join(runtimeDir, "app.js")))}`,
        basePath: basePath || "/"
      },
      isApp
    })));
    debug("Writing index.html to runtime directory"), await fs$1.writeFile(path.join(runtimeDir, "index.html"), indexHtml);
  }
  watch && chokidar.watch(getPossibleDocumentComponentLocations(cwd)).on("all", () => renderAndWriteDocument()), await renderAndWriteDocument(), debug("Writing app.js to runtime directory");
  let relativeConfigLocation = null;
  if (!isApp) {
    const studioConfigPath = await getSanityStudioConfigPath(cwd);
    relativeConfigLocation = studioConfigPath ? toForwardSlashes(path.relative(runtimeDir, studioConfigPath)) : null;
  }
  const relativeEntry = toForwardSlashes(path.relative(runtimeDir, path.resolve(cwd, entry || "./src/App"))), appJsContent = getEntryModule({
    reactStrictMode,
    relativeConfigLocation,
    basePath,
    entry: relativeEntry,
    isApp
  });
  await fs$1.writeFile(path.join(runtimeDir, "app.js"), appJsContent);
}
export {
  createExternalFromImportMap,
  debug$3 as debug,
  extendViteConfigWithUserConfig,
  finalizeViteConfig,
  generateWebManifest,
  getViteConfig,
  writeSanityRuntime
};
//# sourceMappingURL=runtime.js.map
