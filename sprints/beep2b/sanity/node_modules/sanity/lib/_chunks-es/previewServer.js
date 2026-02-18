import { constants } from "node:fs";
import fs from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import readPkgUp from "read-pkg-up";
import { writeSanityRuntime, getViteConfig, extendViteConfigWithUserConfig, finalizeViteConfig, debug as debug$2, generateWebManifest } from "./runtime.js";
import chalk from "chalk";
import { version } from "vite";
const __dirname$1 = path.dirname(fileURLToPath(import.meta.url)), debug$1 = debug$2.extend("static");
async function buildStaticFiles(options) {
  const {
    cwd,
    outputDir,
    sourceMap = !1,
    minify = !0,
    basePath,
    vite: extendViteConfig,
    importMap,
    reactCompiler,
    entry,
    isApp,
    telemetryLogger,
    schemaExtraction
  } = options;
  debug$1("Writing Sanity runtime files"), await writeSanityRuntime({
    cwd,
    reactStrictMode: !1,
    watch: !1,
    basePath,
    entry,
    isApp
  }), debug$1("Resolving vite config");
  const mode = "production";
  let viteConfig = await getViteConfig({
    cwd,
    basePath,
    outputDir,
    minify,
    sourceMap,
    mode,
    importMap,
    reactCompiler,
    isApp,
    telemetryLogger,
    schemaExtraction
  });
  extendViteConfig && (viteConfig = await extendViteConfigWithUserConfig({
    command: "build",
    mode
  }, viteConfig, extendViteConfig), viteConfig = await finalizeViteConfig(viteConfig)), debug$1("Copying static files from /static to output dir");
  const staticPath = path.join(outputDir, "static");
  await copyDir(path.join(cwd, "static"), staticPath), debug$1("Writing favicons to output dir");
  const faviconBasePath = `${basePath.replace(/\/+$/, "")}/static`;
  await writeFavicons(faviconBasePath, staticPath), debug$1("Bundling using vite");
  const {
    build
  } = await import("vite"), bundle = await build(viteConfig);
  if (debug$1("Bundling complete"), Array.isArray(bundle) || !("output" in bundle))
    return {
      chunks: []
    };
  const stats = [];
  return bundle.output.forEach((chunk) => {
    chunk.type === "chunk" && stats.push({
      name: chunk.name,
      modules: Object.entries(chunk.modules).map(([rawFilePath, chunkModule]) => {
        const filePath = rawFilePath.startsWith("\0") ? rawFilePath.slice(1) : rawFilePath;
        return {
          name: path.isAbsolute(filePath) ? path.relative(cwd, filePath) : filePath,
          originalLength: chunkModule.originalLength,
          renderedLength: chunkModule.renderedLength
        };
      })
    });
  }), {
    chunks: stats
  };
}
async function copyDir(srcDir, destDir, skipExisting) {
  await fs.mkdir(destDir, {
    recursive: !0
  });
  for (const file of await tryReadDir(srcDir)) {
    const srcFile = path.resolve(srcDir, file);
    if (srcFile === destDir)
      continue;
    const destFile = path.resolve(destDir, file);
    (await fs.stat(srcFile)).isDirectory() ? await copyDir(srcFile, destFile, skipExisting) : skipExisting ? await fs.copyFile(srcFile, destFile, constants.COPYFILE_EXCL).catch(skipIfExistsError) : await fs.copyFile(srcFile, destFile);
  }
}
async function tryReadDir(dir) {
  try {
    return await fs.readdir(dir);
  } catch (err) {
    if (err.code === "ENOENT")
      return [];
    throw err;
  }
}
function skipIfExistsError(err) {
  if (err.code !== "EEXIST")
    throw err;
}
async function writeFavicons(basePath, destDir) {
  const sanityPkgPath = (await readPkgUp({
    cwd: __dirname$1
  }))?.path, faviconsPath = sanityPkgPath ? path.join(path.dirname(sanityPkgPath), "static", "favicons") : void 0;
  if (!faviconsPath)
    throw new Error("Unable to resolve `sanity` module root");
  await fs.mkdir(destDir, {
    recursive: !0
  }), await copyDir(faviconsPath, destDir, !0), await writeWebManifest(basePath, destDir), await fs.copyFile(path.join(destDir, "favicon.ico"), path.join(destDir, "..", "favicon.ico"));
}
async function writeWebManifest(basePath, destDir) {
  const content = JSON.stringify(generateWebManifest(basePath), null, 2);
  await fs.writeFile(path.join(destDir, "manifest.webmanifest"), content, "utf8").catch(skipIfExistsError);
}
function sanityBasePathRedirectPlugin(basePath) {
  return {
    name: "sanity/server/sanity-base-path-redirect",
    apply: "serve",
    configurePreviewServer(vitePreviewServer) {
      return () => {
        basePath && vitePreviewServer.middlewares.use((req, res, next) => {
          if (req.url !== "/") {
            next();
            return;
          }
          res.writeHead(302, {
            Location: basePath
          }), res.end();
        });
      };
    }
  };
}
const debug = debug$2.extend("preview");
async function startPreviewServer(options) {
  const {
    httpPort,
    httpHost,
    root,
    vite: extendViteConfig,
    isApp
  } = options, startTime = Date.now(), indexPath = path.join(root, "index.html");
  let basePath;
  try {
    const index = await fs.readFile(indexPath, "utf8");
    basePath = tryResolveBasePathFromIndex(index);
  } catch (err) {
    if (err.code !== "ENOENT")
      throw err;
    const error = new Error(`Could not find a production build in the '${root}' directory.
Try building your ${isApp ? "application" : "studio "}app with 'sanity build' before starting the preview server.`);
    throw error.name = "BUILD_NOT_FOUND", error;
  }
  const mode = "production";
  let previewConfig = {
    root,
    base: basePath || "/",
    plugins: [sanityBasePathRedirectPlugin(basePath)],
    configFile: !1,
    preview: {
      port: httpPort,
      host: httpHost,
      strictPort: !0
    },
    // Needed for vite to not serve `root/dist`
    build: {
      outDir: root
    },
    mode
  };
  extendViteConfig && (previewConfig = await extendViteConfigWithUserConfig({
    command: "serve",
    mode
  }, previewConfig, extendViteConfig)), debug("Creating vite server");
  const {
    preview
  } = await import("vite"), server = await preview(previewConfig), warn = server.config.logger.warn, info = server.config.logger.info, url = server.resolvedUrls.local[0];
  typeof basePath > "u" ? warn('Could not determine base path from index.html, using "/" as default') : basePath && basePath !== "/" && info(`Using resolved base path from static build: ${chalk.cyan(basePath)}`);
  const startupDuration = Date.now() - startTime;
  return info(`Sanity ${isApp ? "application" : "Studio"} using ${chalk.cyan(`vite@${version}`)} ready in ${chalk.cyan(`${Math.ceil(startupDuration)}ms`)} and running at ${chalk.cyan(url)} (production preview mode)`), {
    urls: server.resolvedUrls,
    close: () => new Promise((resolve, reject) => server.httpServer.close((err) => err ? reject(err) : resolve()))
  };
}
function tryResolveBasePathFromIndex(index) {
  const basePath = index.match(/<script[^>]+src="(.*?)\/static\/sanity-/)?.[1];
  if (!(typeof basePath > "u"))
    return basePath === "" ? "/" : basePath;
}
export {
  buildStaticFiles,
  startPreviewServer
};
//# sourceMappingURL=previewServer.js.map
