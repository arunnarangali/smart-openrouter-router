import express from "express"
import { createSmartRouter } from "../../index.js"

const app = express()
app.use(express.json())

const router = createSmartRouter({ apiKey: process.env.OPENROUTER_API_KEY })
await router.start()

app.post("/api/chat", async (req, res) => {
  try {
    const out = await router.routeChat({ messages: req.body.messages || [] })
    res.json(out)
  } catch (err) {
    res.status(500).json({ error: String(err) })
  }
})

app.listen(3000, () => {
  console.log("Listening on http://127.0.0.1:3000")
})
