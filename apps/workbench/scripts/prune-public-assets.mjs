import { readdir, unlink } from "node:fs/promises";
import { resolve } from "node:path";

const portfolioFiles = new Set(["after.png", "before.png", "bundle.json"]);
const directory = resolve("dist/generated-demo");

let entries;
try {
  entries = await readdir(directory, { withFileTypes: true });
} catch (error) {
  if (error && typeof error === "object" && error.code === "ENOENT") {
    process.exit(0);
  }
  throw error;
}

for (const entry of entries) {
  if (!entry.isFile() || portfolioFiles.has(entry.name)) continue;
  await unlink(resolve(directory, entry.name));
}
