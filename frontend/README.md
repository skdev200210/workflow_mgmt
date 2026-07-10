# Workflow Builder (frontend)

A React + [React Flow](https://reactflow.dev) canvas for visually building workflows
and saving them to the FastAPI backend.

## What you can do
- Drag out **Calling** and **Message** nodes and fill in their templates
  (start/end/system-instructions or the message body + input/output variables).
- Connect nodes by dragging from a node's bottom dot to another node's top dot.
- Click an edge to add a **condition**: a hardcoded **column** dropdown, an
  **operator** dropdown (`> < >= <= == != is`), and a typed **value** field.
- Name the workflow and **Save** — the app creates an agent per calling/message
  node (`POST /agents`), then saves the graph (`POST /workflows`).

The **Start** node is the workflow entry point (`workflow_start`). Exactly one is
required. Cycles/self-loops are allowed.

## Prerequisites
- **Node.js 18+** (not currently installed on this machine — install from
  https://nodejs.org). Then `node --version` should work.
- The backend running with CORS enabled (already added). Start it with:
  ```bash
  uv run uvicorn app.main:app --reload
  ```

## Run
```bash
cd frontend
cp .env.example .env      # set VITE_API_BASE / VITE_API_KEY (or use the ⚙ Settings bar)
npm install
npm run dev               # opens http://localhost:5173
```

The API base URL and `X-API-Key` can also be set live via the **⚙ Settings**
button in the toolbar (persisted to localStorage).

## Notes
- Each **Save** currently creates fresh agents for the calling/message nodes. Re-saving
  the same workflow creates new agent rows — fine for now; agent de-duplication/reuse
  can be added later.
- Client-side validation mirrors the backend: it warns if a declared input variable is
  missing its `{placeholder}` in the template, and blocks save on the same rule.
- Numeric conditions send a JSON number, `is` sends a boolean, and `==`/`!=` default to
  string (switchable via the **Value type** dropdown) so the stored condition types match
  what you intend.
