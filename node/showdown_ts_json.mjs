import { writeFileSync, mkdirSync } from "node:fs";
import path from "node:path";
import { pathToFileURL, fileURLToPath } from "node:url";

// Usage:
//   npx tsx pokedex.mjs <ExportVarName> <inputPath> <outputPath>
// Example:
//   npx tsx pokedex.mjs Pokedex ../data/bronze/pokedex.ts ../data/silver/pokedex.json

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const exportVarName = process.argv[2];
const inputArg = process.argv[3];
const outputArg = process.argv[4];

if (!exportVarName || !inputArg || !outputArg) {
  throw new Error(
    "Usage: npx tsx pokedex.mjs <ExportVarName> <inputPath> <outputPath>"
  );
}

// Resolve paths relative to where you run the command (not script location)
const inputPath = path.resolve(process.cwd(), inputArg);
const outputPath = path.resolve(process.cwd(), outputArg);

// Ensure output directory exists
mkdirSync(path.dirname(outputPath), { recursive: true });

// Import the TS module at runtime (tsx handles TS on the fly)
const mod = await import(pathToFileURL(inputPath).href);

// Extract the requested export (fallback to default if they asked for 'default')
const data =
  exportVarName === "default" ? mod.default : mod[exportVarName] ?? mod.default;

if (!data) {
  const available = Object.keys(mod).sort().join(", ");
  throw new Error(
    `Could not find export "${exportVarName}" in ${inputPath}. ` +
      `Available exports: ${available || "(none)"}`
  );
}

writeFileSync(outputPath, JSON.stringify(data, null, 2), "utf8");
console.log("Wrote", outputPath);
