# qualibact-mcp

Read-only MCP (Model Context Protocol) server that exposes QualiBact threshold lookups to MCP-aware clients (Claude Desktop, Claude Code, Cursor, etc.).

It's a tiny Cloudflare Worker that wraps the public `/api/v2/` endpoints on `static.qualibact.org` and re-frames them as MCP tools.

## What it does

Five tools:

| Tool | Returns |
|------|---------|
| `list_species(genus?)` | Every published species + its preferred scheme + all schemes |
| `list_schemes()` | Every QC scheme + how many species it covers |
| `get_thresholds(species, scheme?, metric?)` | The 4-bound (FAIL\_lower / WARN\_lower / WARN\_upper / FAIL\_upper) rows |
| `list_pinned_thresholds(species?)` | All hand-pinned (expert-override) values with rationale strings |
| `get_pinned_threshold(species, scheme, metric)` | Rationale for one specific pin |

All data is fetched from `https://static.qualibact.org/api/v2/` — no local state, no DB. The Worker is essentially a read-through cache.

## Deploy

Once per machine:

```bash
cd mcp
npm install
npx wrangler login          # auth with the Cloudflare account
```

Then:

```bash
npm run deploy
```

The first deploy will provision the Worker. `mcp.qualibact.org` needs to point at it — set up the custom-domain binding in Cloudflare dashboard (Workers > qualibact-mcp > Settings > Domains) **once**.

## Dev / local testing

```bash
npm run dev            # localhost:8787
# Then in another terminal, test with curl:
curl -X POST http://localhost:8787/mcp \
  -H 'content-type: application/json' \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

## Wiring it into Claude Desktop / Claude Code

Once deployed, users add one entry to their MCP config:

```jsonc
{
  "mcpServers": {
    "qualibact": {
      "transport": { "type": "http", "url": "https://mcp.qualibact.org/mcp" }
    }
  }
}
```

Then in conversation: *"What's the QualiBact threshold for E. coli N50?"* — Claude will call `qualibact.get_thresholds(species="Escherichia_coli", metric="N50")` and answer with the authoritative number.

## Why a Worker (not stdio)

A stdio MCP would require every user to `npm install` and configure a local subprocess. Hosting it as a Worker means users add one URL to their config and it just works — and we keep parity with where the rest of QualiBact lives on Cloudflare.
