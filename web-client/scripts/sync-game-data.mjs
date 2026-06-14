import { cp, mkdir, rm } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(__dirname, "..");
const clientRoot = path.resolve(root, "..", "client");
const publicRoot = path.resolve(root, "public", "game");

async function copyDir(source, target) {
  await cp(source, target, { recursive: true, force: true });
}

async function main() {
  await rm(publicRoot, { recursive: true, force: true });
  await mkdir(publicRoot, { recursive: true });
  await copyDir(path.join(clientRoot, "assets"), path.join(publicRoot, "assets"));
  await copyDir(path.join(clientRoot, "data"), path.join(publicRoot, "data"));
  console.log("web-client assets synced");
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
