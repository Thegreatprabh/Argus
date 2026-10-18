# Workflow: patch-diff

Goal: find **what changed between two versions** of the same target —
the fastest way to spot fixed bugs, new features, or silently patched
vulnerabilities.

## Steps
1. Run the same engine on v1 and v2 (e.g. `apk.overview` on both APKs).
2. Diff the findings: added/removed permissions, SDKs, endpoints, strings.
3. For each delta, hypothesize *why* it changed, citing both versions.
4. Flag security-relevant deltas (new dangerous permissions, removed
   certificate pinning markers, new network hosts) as medium+ severity.

## Rules
- Deltas are facts; motives are hypotheses — label them clearly.
