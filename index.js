import { spawn } from "node:child_process"
import net from "node:net"
import { fileURLToPath } from "node:url"
import path from "node:path"

const THIS_DIR = path.dirname(fileURLToPath(import.meta.url))

function pickFreePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.listen(0, "127.0.0.1", () => {
      const addr = server.address()
      const port = typeof addr === "object" && addr ? addr.port : 0
      server.close(() => resolve(port))
    })
    server.on("error", reject)
  })
}

async function waitForStatus(baseURL, timeoutMs = 8000) {
  const started = Date.now()
  while (Date.now() - started < timeoutMs) {
    try {
      const resp = await fetch(`${baseURL}/status`)
      if (resp.ok) return
    } catch (_err) {
      // retry
    }
    await new Promise((r) => setTimeout(r, 200))
  }
  throw new Error("Smart Router failed to start")
}

export function createSmartRouter(opts = {}) {
  const apiKey = (opts.apiKey || process.env.OPENROUTER_API_KEY || "").trim()
  if (!apiKey) {
    throw new Error("OPENROUTER_API_KEY is required (argument or environment variable)")
  }

  const state = {
    apiKey,
    host: opts.host || "127.0.0.1",
    port: Number(opts.port || 0),
    autoStart: opts.autoStart !== false,
    pythonCmd: opts.pythonCmd || "python3",
    scriptPath: opts.scriptPath || path.join(THIS_DIR, "smart_router.py"),
    proc: null,
  }

  async function start() {
    if (state.proc && !state.proc.killed) return
    if (!state.port) state.port = await pickFreePort()
    const env = { ...process.env, OPENROUTER_API_KEY: state.apiKey, PROXY_PORT: String(state.port) }
    state.proc = spawn(state.pythonCmd, [state.scriptPath], { env, stdio: "ignore" })
    await waitForStatus(baseURL())
  }

  async function stop() {
    if (!state.proc) return
    state.proc.kill("SIGTERM")
    state.proc = null
  }

  function baseURL() {
    if (!state.port) throw new Error("Router not started")
    return `http://${state.host}:${state.port}`
  }

  async function ensureStarted() {
    if (state.proc && !state.proc.killed) return
    if (!state.autoStart) throw new Error("Router is not running. Call start() first.")
    await start()
  }

  async function status() {
    await ensureStarted()
    const resp = await fetch(`${baseURL()}/status`)
    return resp.json()
  }

  async function last() {
    await ensureStarted()
    const resp = await fetch(`${baseURL()}/last`)
    return resp.json()
  }

  async function routeChat(req) {
    await ensureStarted()
    const body = {
      model: req?.model || "smart-router/best",
      messages: req?.messages || [],
      stream: Boolean(req?.stream),
      ...(req?.extra || {}),
    }
    const resp = await fetch(`${baseURL()}/v1/chat/completions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
    const data = await resp.json()
    if (!resp.ok) {
      throw new Error(data?.error?.message || `Router error: ${resp.status}`)
    }
    return data
  }

  async function getBestModel(input = {}) {
    const scenario = input?.scenario || ""
    const prompt = input?.prompt || ""
    const s = await status()
    if (scenario) {
      const arr = (s?.top_per_scenario || {})[scenario] || []
      return arr[0] || ""
    }
    await routeChat({ model: "smart-router/fast", messages: [{ role: "user", content: prompt }], extra: { max_tokens: 1 } })
    const l = await last()
    return l?.final_model || ""
  }

  return { start, stop, status, last, routeChat, getBestModel, baseURL }
}
