# Workflow: trace-feature

Goal: explain **how one feature of a target works**, with evidence for every claim.

## Steps
1. Identify the target surface (web page, APK screen, binary CLI flag).
2. Web: run `web.analyze` with deep=true; read the JS bundles and API endpoints.
   APK: run `apk.overview`; note permissions + URLs related to the feature.
   Binary: run `binary.info`; look at strings referencing the feature.
3. Form a hypothesis: "Feature X works by calling Y with parameters Z."
4. Verify: every claim must cite a finding (file, endpoint, string, or address).
5. Output: 1) plain-language explanation, 2) evidence list, 3) what you could
   NOT verify (be honest — no guessing).

## Rules
- Never invent endpoints, functions, or behavior. If the evidence is missing,
  say so.
- Analysis only: do not produce cracks, keygens, or DRM bypasses.
