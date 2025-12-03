# AI Builders MCP Server Setup

This repo now ships with a ready-to-use MCP server entry for the AI Builders coach. Use the steps below to register it with your MCP-compatible tools.

## What it does
- Runs the AI Builders coach MCP server via `npx`.
- Requires an `AI_BUILDER_TOKEN` from the AI Builders Space Settings page.
- Works with Cursor/Trae JSON configs, Codex CLI, and Claude Code.

## Quick config (Cursor/Trae)
Copy `mcp_ai_builders_coach.json` into your MCP settings (e.g. `~/.cursor/mcp.json` or `~/.trae/mcp.json`) and replace `sk_live_your_token_here` with your real token:

```json
{
  "mcpServers": {
    "ai-builders-coach": {
      "command": "npx",
      "args": ["-y", "@aibuilders/mcp-coach-server"],
      "env": {
        "AI_BUILDER_TOKEN": "sk_live_your_token_here"
      }
    }
  }
}
```

## Codex CLI
```bash
codex mcp add ai-builders-coach --env AI_BUILDER_TOKEN=sk_live_your_actual_token_here -- npx -y @aibuilders/mcp-coach-server
```

## Claude Code CLI
```bash
claude mcp add-json "ai-builders-coach" '{"command":"npx","args":["-y","@aibuilders/mcp-coach-server"],"env":{"AI_BUILDER_TOKEN":"sk_live_your_token_here"}}'
```

## Notes
- Replace the token placeholders with your live AI Builders token.
- The server is invoked with `npx -y @aibuilders/mcp-coach-server`; no extra files are needed.
- Keep your token out of version control—only fill it in locally.
