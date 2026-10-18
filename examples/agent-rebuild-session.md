# Example: agent rebuilds a login flow

> How an AI agent uses ARGUS MCP tools to investigate + rebuild.
> Paste into your agent after `argus setup`.

**You:** Use ARGUS to figure out how the login works on
`https://example-shop.com`, then scaffold my own version.

**Agent:**
1. `web.analyze(url, deep)` → tech: Next.js; endpoints:
   `POST /api/v1/auth/login`, `GET /api/v1/me`; form posts to `/api/v1/auth/login`.
2. Follows `workflows/trace-feature.md`: hypothesis — "login POSTs
   email+password, gets a JWT, stored in localStorage."
3. Verifies: cites the JS bundle lines + form action as evidence.
4. `rebuild.scaffold(target)` → `rebuild-out/` with `src/api.js`
   (`call_auth_login()`), page shells, `REBUILD_NOTES.md`.
5. Reports: what was recovered, what needs manual work (token refresh
   logic wasn't visible statically — flagged honestly).

**You:** open `rebuild-out/`, keep building. The scaffold is yours.
