// QualiBact MCP server — Cloudflare Worker.
//
// Speaks the MCP JSON-RPC 2.0 wire protocol directly (the @modelcontextprotocol
// SDK's HTTP transport is Node-bound and not Worker-compatible). We implement
// the three methods every read-only tools server needs: initialize, tools/list,
// tools/call. Tools fetch /api/v2/ blobs from R2 and re-frame them.
//
// Deploy: `wrangler deploy` (from this directory).

interface Env {
  QUALIBACT_API_BASE: string;
}

interface IndexEntry {
  species: string;
  name?: string;
  preferred_scheme?: string;
  schemes: { scheme: string; manifest_url: string }[];
}

interface ThresholdsBlob {
  // species is keyed by Genus_species; schemes is keyed by scheme name.
  species: Record<
    string,
    {
      schemes: Record<
        string,
        {
          thresholds: Array<{
            metric: string;
            final_lower: number | null;
            final_upper: number | null;
            warn_lower: number | null;
            warn_upper: number | null;
            source: string;
          }>;
        }
      >;
    }
  >;
}

interface RationaleOverride {
  species: string;
  scheme: string;
  metric: string;
  lower?: number;
  upper?: number;
  reason: string;
}

const PROTOCOL_VERSION = '2025-03-26';
const SERVER_INFO = { name: 'qualibact', version: '0.1.0' };
const INSTRUCTIONS =
  'QualiBact publishes species-specific bacterial genome assembly QC thresholds. ' +
  'Use list_species to discover what is available, then get_thresholds for the 4-bound ' +
  '(FAIL_lower / WARN_lower / WARN_upper / FAIL_upper) table for a given (species, scheme). ' +
  'Hand-pinned (expert-override) values are surfaced via list_pinned_thresholds and ' +
  'get_pinned_threshold.';

// -- module-scoped fetch cache ---------------------------------------------
// Workers can reuse module-scope memory within a single isolate; not durable
// across deploys but cheap to keep.

const cache = new Map<string, { data: unknown; expires: number }>();
const TTL_MS = 60_000;

async function fetchJSON<T>(url: string): Promise<T> {
  const hit = cache.get(url);
  if (hit && hit.expires > Date.now()) return hit.data as T;
  const r = await fetch(url, { headers: { accept: 'application/json' } });
  if (!r.ok) throw new Error(`upstream ${r.status} for ${url}`);
  const data = (await r.json()) as T;
  cache.set(url, { data, expires: Date.now() + TTL_MS });
  return data;
}

async function fetchText(url: string): Promise<string> {
  const hit = cache.get(url);
  if (hit && hit.expires > Date.now()) return hit.data as string;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`upstream ${r.status} for ${url}`);
  const data = await r.text();
  cache.set(url, { data, expires: Date.now() + TTL_MS });
  return data;
}

// -- tiny YAML parser (just enough for threshold-rationale.yml) ------------

function parseRationale(yml: string): RationaleOverride[] {
  const out: RationaleOverride[] = [];
  let cur: Partial<RationaleOverride> | null = null;
  const push = () => {
    if (cur?.species && cur.scheme && cur.metric && cur.reason) {
      out.push(cur as RationaleOverride);
    }
  };
  for (const raw of yml.split('\n')) {
    const line = raw.trimEnd();
    if (line.startsWith('  - species:')) {
      push();
      cur = { species: line.slice('  - species:'.length).trim() };
    } else if (cur && line.startsWith('    scheme:')) {
      cur.scheme = line.slice('    scheme:'.length).trim();
    } else if (cur && line.startsWith('    metric:')) {
      cur.metric = line.slice('    metric:'.length).trim();
    } else if (cur && line.startsWith('    lower:')) {
      cur.lower = Number(line.slice('    lower:'.length).trim());
    } else if (cur && line.startsWith('    upper:')) {
      cur.upper = Number(line.slice('    upper:'.length).trim());
    } else if (cur && line.startsWith('    reason:')) {
      cur.reason = line
        .slice('    reason:'.length)
        .trim()
        .replace(/^"|"$/g, '');
    }
  }
  push();
  return out;
}

const underscore = (s: string) => s.replace(/\s+/g, '_');
const pretty = (s: string) => s.replace(/_/g, ' ');

// -- tool definitions ------------------------------------------------------

const TOOLS = [
  {
    name: 'list_species',
    description:
      'List every species QualiBact publishes thresholds for. Returns species name (Genus_species), preferred QC scheme, and every scheme that has data.',
    inputSchema: {
      type: 'object',
      properties: {
        genus: {
          type: 'string',
          description:
            'Filter to one genus (e.g. "Campylobacter"). Case-sensitive, no underscore.',
        },
      },
    },
  },
  {
    name: 'list_schemes',
    description:
      'List every QC scheme QualiBact publishes (qualibact-v1.0, qualibact-v1.1, REFSEQ-QC-v1, …) with the species count for each.',
    inputSchema: { type: 'object', properties: {} },
  },
  {
    name: 'get_thresholds',
    description:
      'Return the 4-bound thresholds (FAIL_lower / WARN_lower / WARN_upper / FAIL_upper) for a single species. Defaults to the species\'s preferred scheme; pass `scheme` to override. Optional `metric` returns just that one row.',
    inputSchema: {
      type: 'object',
      required: ['species'],
      properties: {
        species: {
          type: 'string',
          description: 'Genus_species (e.g. "Escherichia_coli"). Spaces are accepted and normalised.',
        },
        scheme: {
          type: 'string',
          description: 'e.g. "qualibact-v1.0" / "qualibact-v1.1". Defaults to the species\'s preferred scheme.',
        },
        metric: {
          type: 'string',
          description: 'e.g. "N50", "Genome_Size", "GC_Content". Returns all metrics if omitted.',
        },
      },
    },
  },
  {
    name: 'list_pinned_thresholds',
    description:
      'List every hand-pinned threshold override across all species/schemes (the expert-requested values that bypass the engine\'s automatic percentile derivation). Each row carries (species, scheme, metric, lower/upper, reason).',
    inputSchema: {
      type: 'object',
      properties: {
        species: { type: 'string', description: 'Filter to one species.' },
      },
    },
  },
  {
    name: 'get_pinned_threshold',
    description:
      'Return the rationale string for a single hand-pinned threshold (species, scheme, metric). Returns a plain "no override" message if the published value is the engine\'s automatic derivation.',
    inputSchema: {
      type: 'object',
      required: ['species', 'scheme', 'metric'],
      properties: {
        species: { type: 'string' },
        scheme: { type: 'string' },
        metric: { type: 'string' },
      },
    },
  },
];

// -- tool implementations --------------------------------------------------

async function callTool(
  name: string,
  args: Record<string, unknown>,
  env: Env,
): Promise<{ content: Array<{ type: 'text'; text: string }>; isError?: boolean }> {
  const base = env.QUALIBACT_API_BASE.replace(/\/$/, '');
  try {
    switch (name) {
      case 'list_species': {
        const genus = typeof args.genus === 'string' ? args.genus : undefined;
        const idx = await fetchJSON<{ species: IndexEntry[] }>(`${base}/index.json`);
        const list = idx.species
          .filter((s) => (genus ? s.species.startsWith(`${genus}_`) : true))
          .map((s) => ({
            species: s.species,
            name: s.name ?? pretty(s.species),
            preferred_scheme: s.preferred_scheme ?? s.schemes[0]?.scheme,
            schemes: s.schemes.map((sc) => sc.scheme),
          }));
        return {
          content: [
            { type: 'text', text: `${list.length} species` },
            { type: 'text', text: JSON.stringify(list, null, 2) },
          ],
        };
      }

      case 'list_schemes': {
        const idx = await fetchJSON<{ species: IndexEntry[] }>(`${base}/index.json`);
        const counts = new Map<string, number>();
        for (const sp of idx.species) {
          for (const s of sp.schemes) {
            counts.set(s.scheme, (counts.get(s.scheme) ?? 0) + 1);
          }
        }
        const out = [...counts.entries()]
          .map(([scheme, n]) => ({ scheme, species_count: n }))
          .sort((a, b) => b.species_count - a.species_count);
        return {
          content: [
            { type: 'text', text: `${out.length} schemes` },
            { type: 'text', text: JSON.stringify(out, null, 2) },
          ],
        };
      }

      case 'get_thresholds': {
        const species = String(args.species ?? '');
        if (!species) throw new Error('`species` is required');
        const sp = underscore(species);
        const scheme = typeof args.scheme === 'string' ? args.scheme : undefined;
        const metric = typeof args.metric === 'string' ? args.metric : undefined;

        const idx = await fetchJSON<{ species: IndexEntry[] }>(`${base}/index.json`);
        const entry = idx.species.find((s) => s.species === sp);
        if (!entry) throw new Error(`species '${sp}' not found`);
        const useScheme = scheme || entry.preferred_scheme || entry.schemes[0]?.scheme;
        if (!useScheme) throw new Error(`species '${sp}' has no published scheme`);

        const blob = await fetchJSON<ThresholdsBlob>(`${base}/thresholds.json`);
        const schemeBlob = blob.species[sp]?.schemes[useScheme];
        if (!schemeBlob) {
          throw new Error(`no threshold rows for ${sp} / ${useScheme}`);
        }
        const rows = metric
          ? schemeBlob.thresholds.filter((t) => t.metric === metric)
          : schemeBlob.thresholds;
        if (rows.length === 0 && metric) {
          throw new Error(`no '${metric}' row for ${sp} / ${useScheme}`);
        }
        return {
          content: [
            {
              type: 'text',
              text: `Thresholds for ${pretty(sp)} / ${useScheme} (${rows.length} rows):`,
            },
            { type: 'text', text: JSON.stringify(rows, null, 2) },
          ],
        };
      }

      case 'list_pinned_thresholds': {
        const yml = await fetchText(`${base}/threshold-rationale.yml`);
        const all = parseRationale(yml);
        const filter = typeof args.species === 'string' ? underscore(args.species) : null;
        const filtered = filter ? all.filter((o) => o.species === filter) : all;
        return {
          content: [
            { type: 'text', text: `${filtered.length} pinned override(s)` },
            { type: 'text', text: JSON.stringify(filtered, null, 2) },
          ],
        };
      }

      case 'get_pinned_threshold': {
        const species = underscore(String(args.species ?? ''));
        const scheme = String(args.scheme ?? '');
        const metric = String(args.metric ?? '');
        if (!species || !scheme || !metric) {
          throw new Error('`species`, `scheme`, and `metric` are all required');
        }
        const yml = await fetchText(`${base}/threshold-rationale.yml`);
        const hit = parseRationale(yml).find(
          (o) => o.species === species && o.scheme === scheme && o.metric === metric,
        );
        if (!hit) {
          return {
            content: [
              {
                type: 'text',
                text: `No hand-pinned override for ${species} / ${scheme} / ${metric}. The published value is the engine's automatic derivation.`,
              },
            ],
          };
        }
        return { content: [{ type: 'text', text: JSON.stringify(hit, null, 2) }] };
      }

      default:
        throw new Error(`unknown tool: ${name}`);
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return { content: [{ type: 'text', text: `error: ${message}` }], isError: true };
  }
}

// -- JSON-RPC dispatcher ---------------------------------------------------

interface JsonRpcRequest {
  jsonrpc: '2.0';
  id?: number | string | null;
  method: string;
  params?: Record<string, unknown>;
}

interface JsonRpcSuccess {
  jsonrpc: '2.0';
  id: number | string | null;
  result: unknown;
}

interface JsonRpcError {
  jsonrpc: '2.0';
  id: number | string | null;
  error: { code: number; message: string; data?: unknown };
}

async function handleRpc(
  req: JsonRpcRequest,
  env: Env,
): Promise<JsonRpcSuccess | JsonRpcError | null> {
  // Notifications have no id and don't expect a response.
  const id = req.id ?? null;
  const isNotification = req.id === undefined || req.id === null;

  try {
    switch (req.method) {
      case 'initialize':
        return {
          jsonrpc: '2.0',
          id,
          result: {
            protocolVersion: PROTOCOL_VERSION,
            serverInfo: SERVER_INFO,
            capabilities: { tools: {} },
            instructions: INSTRUCTIONS,
          },
        };

      case 'initialized':
      case 'notifications/initialized':
        return isNotification ? null : { jsonrpc: '2.0', id, result: {} };

      case 'ping':
        return { jsonrpc: '2.0', id, result: {} };

      case 'tools/list':
        return { jsonrpc: '2.0', id, result: { tools: TOOLS } };

      case 'tools/call': {
        const p = (req.params ?? {}) as { name?: string; arguments?: Record<string, unknown> };
        if (!p.name) throw new Error('tools/call requires `name`');
        const result = await callTool(p.name, p.arguments ?? {}, env);
        return { jsonrpc: '2.0', id, result };
      }

      default:
        if (isNotification) return null;
        return {
          jsonrpc: '2.0',
          id,
          error: { code: -32601, message: `method not found: ${req.method}` },
        };
    }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return {
      jsonrpc: '2.0',
      id,
      error: { code: -32603, message },
    };
  }
}

// -- Worker entry ----------------------------------------------------------

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (request.method === 'GET' && url.pathname !== '/mcp') {
      return new Response(
        [
          'QualiBact MCP server',
          '',
          'POST /mcp with JSON-RPC 2.0 (MCP protocol).',
          'See https://modelcontextprotocol.io for the spec.',
          '',
          `Data source: ${env.QUALIBACT_API_BASE}`,
          '',
          `Tools: ${TOOLS.map((t) => t.name).join(', ')}`,
        ].join('\n'),
        { headers: { 'content-type': 'text/plain; charset=utf-8' } },
      );
    }

    if (url.pathname !== '/mcp') {
      return new Response('not found', { status: 404 });
    }

    if (request.method !== 'POST') {
      return new Response('method not allowed', {
        status: 405,
        headers: { allow: 'POST' },
      });
    }

    let body: unknown;
    try {
      body = await request.json();
    } catch {
      return Response.json(
        { jsonrpc: '2.0', id: null, error: { code: -32700, message: 'parse error' } },
        { status: 400 },
      );
    }

    const requests: JsonRpcRequest[] = Array.isArray(body) ? body : [body as JsonRpcRequest];
    const responses = (await Promise.all(requests.map((r) => handleRpc(r, env)))).filter(
      (r): r is JsonRpcSuccess | JsonRpcError => r !== null,
    );

    // Batch responses are returned as an array; single requests as a single object.
    // Empty (all notifications) → 202 with no body.
    if (responses.length === 0) {
      return new Response(null, { status: 202 });
    }
    const payload = Array.isArray(body) ? responses : responses[0];
    return Response.json(payload, {
      headers: {
        'access-control-allow-origin': '*',
        'access-control-allow-headers': 'content-type, mcp-protocol-version',
      },
    });
  },
} satisfies ExportedHandler<Env>;
