# Workflow: map-api-surface

Goal: enumerate **every network API** a target talks to.

## Steps
1. Web: `web.analyze` deep=true → collect endpoints from JS + HTML.
   APK: `apk.overview` → collect hardcoded URLs.
2. Cluster by host and path prefix (`/api/v1/...`).
3. For each cluster, infer: auth required? (look for tokens/headers),
   method, likely purpose — each inference cites its evidence.
4. Output a table: method | host | path | evidence | confidence.

## Rules
- Candidate endpoints are leads, not facts — mark confidence honestly.
- Do not attack the endpoints. Mapping is reconnaissance for understanding.
