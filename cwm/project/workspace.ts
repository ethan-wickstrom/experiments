import {
  lstat,
  mkdir,
  readdir,
  readFile,
  realpath,
  rename,
  rm,
  writeFile,
  link,
} from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { dirname, join, relative, sep } from "node:path";

export function sourcePath(name: string) {
  return (
    name.length <= 240 &&
    name
      .split("/")
      .every(
        (part) =>
          part.length > 0 &&
          !part.startsWith(".") &&
          !["node_modules", "dist", "build", "coverage"].includes(part) &&
          !/[\\:\p{Cc}]/u.test(part),
      ) &&
    /\.(?:[cm]?ts|tsx|json|md)$/i.test(name)
  );
}

export const maxFileBytes = 64 * 1024;
export const maxFiles = 128;

async function snapshot(root: string) {
  const files = new Map<string, string>();
  async function visit(dir: string) {
    for (const entry of await readdir(dir, { withFileTypes: true })) {
      if (
        entry.name.startsWith(".") ||
        ["node_modules", "dist", "build", "coverage"].includes(entry.name)
      )
        continue;
      const path = join(dir, entry.name);
      if (entry.isDirectory()) {
        await visit(path);
        continue;
      }
      const name = relative(root, path).split(sep).join("/");
      if (!entry.isFile() || !sourcePath(name)) continue;
      if (files.size >= maxFiles || (await lstat(path)).size > maxFileBytes)
        throw Error("Project exceeds the small-project context budget: " + name);
      const bytes = await readFile(path);
      files.set(name, new TextDecoder("utf-8", { fatal: true, ignoreBOM: true }).decode(bytes));
    }
  }
  await visit(root);
  return files;
}

export async function openProject(directory: string) {
  const root = await realpath(directory);
  const files = await snapshot(root);
  async function refresh() {
    const current = await snapshot(root);
    files.clear();
    for (const [path, source] of current) files.set(path, source);
  }
  async function persist(path: string, text: string) {
    if (!sourcePath(path)) throw Error("Unsupported project path");
    const parts = path.split("/");
    let parent = root;
    for (const part of parts.slice(0, -1)) {
      parent = join(parent, part);
      try {
        await mkdir(parent);
      } catch (error) {
        if ((error as NodeJS.ErrnoException).code !== "EEXIST") throw error;
      }
      if (!(await lstat(parent)).isDirectory() || (await realpath(parent)) !== parent)
        throw Error("Expected project directory");
    }
    const dest = join(root, path);
    const previous = files.get(path);
    const temp = join(dirname(dest), "." + randomUUID() + ".tmp");
    try {
      if (previous === undefined) {
        await writeFile(temp, text, { flag: "wx" });
        await link(temp, dest);
      } else {
        const stat = await lstat(dest);
        if (!stat.isFile() || (await readFile(dest, "utf8")) !== previous)
          throw Error("File changed since project opened");
        await writeFile(temp, text, { flag: "wx", mode: stat.mode });
        await rename(temp, dest);
      }
    } finally {
      await rm(temp, { force: true });
    }
  }
  return { files, refresh, persist };
}
