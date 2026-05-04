# Node/Express SDK Example

```bash
export OPENROUTER_API_KEY="sk-or-..."
npm i express
node server.js
```

Send `POST /api/chat` with JSON:

```json
{
  "messages": [
    { "role": "user", "content": "Write a React component" }
  ]
}
```
