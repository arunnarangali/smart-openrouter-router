import { readFile } from "node:fs/promises";
import { homedir } from "node:os";
import { join } from "node:path";

const CACHE_DIR = join(homedir(), ".cache", "smart-openrouter-router");
const ACTIVE_FILE = join(CACHE_DIR, "active.json");

async function getRouterPort() {
  try {
    const raw = await readFile(ACTIVE_FILE, "utf-8");
    const data = JSON.parse(raw);
    return data.port;
  } catch {
    return null;
  }
}

async function fetchLastModel(port) {
  try {
    const res = await fetch(`http://127.0.0.1:${port}/last`, {
      signal: AbortSignal.timeout(2000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    return data.final_model || null;
  } catch {
    return null;
  }
}

const plugin = async (api) => {
  let lastShownModel = "";
  let lastMessageID = "";

  const unsubscribe = api.event.on("message.updated", (event) => {
    const info = event.properties?.info;
    if (!info) return;
    if (info.role !== "assistant") return;
    if (!info.time?.completed) return;
    if (info.id === lastMessageID) return;
    lastMessageID = info.id;

    getRouterPort()
      .then((port) => {
        if (!port) return;
        return fetchLastModel(port);
      })
      .then((model) => {
        if (!model || model === lastShownModel) return;
        lastShownModel = model;
        api.ui.toast({
          variant: "info",
          title: "Smart Router",
          message: model,
          duration: 4000,
        });
      })
      .catch(() => {});
  });

  api.lifecycle.onDispose(() => {
    unsubscribe();
  });
};

export default plugin;
