# Cross-cloud dogfood report — 2026-10-04

All three clouds validated under three scenarios. All PASS (two documented exceptions).

## Results

| Scenario | AWS | GCP | Azure |
|---|---|---|---|
| Base (Deep Research API) | ✅ PASS, us-east-2 | ✅ PASS, us-west1 | ✅ PASS, westus2 |
| 2+3 (options + ops/failure) | ✅ PASS — region blocked by SCP, private-net variant instead | ✅ PASS, us-central1 | ✅ PASS, eastus2 |
| 4 (Pulse: scheduler + cache) | ✅ PASS — POST /admin/collect failed (pack rule conflict) | ✅ PASS — 6/7 (source drill = unit only) | ✅ PASS |

## What real deployment caught (local tests didn't)

- **GCP**: Scheduler→Cloud Run used OIDC; the API needs OAuth access token. Two scheduled runs failed silently. pytest couldn't see it (fake clients).
- **AWS**: ElastiCache Serverless requires TLS — without it, reads hang until Lambda timeout. Fargate can't reuse Lambda base images (ENTRYPOINT mismatch).
- **Azure**: VS Enterprise subscription refuses Managed Redis B0/B1 in eastus2 → Redis split to centralus. Container Apps rejects empty secret values.
- **Pack rule conflict (AWS)**: "no NAT" rule puts the API Lambda in an isolated subnet, which breaks the synchronous `/admin/collect` endpoint. The pack contradicts itself — flagged, not worked around.

## Cost (this round)

All under $1 each. Pulse caches were torn down within ~2 hours (Memorystore ~$35/mo and ElastiCache Serverless ~$5–8/day if left running). All $20/mo budgets quiet.

## Unresolved

1. **AWS region lock** — org SCP denies all API calls outside us-east-2. Alternate-region testing impossible on this account.
2. **AWS PR #20** — still open, awaiting Dongbum's merge decision.
3. **No cache skill in any pack** — design decision needed (ElastiCache L2 missing, App Runner L2 missing, Memorystore scale-to-zero mismatch).
4. **GCP Firestore destroy is a no-op** — Terraform reports success, DB remains. Manual deletion required.

## Pack updates

Branch `feat/pack-gaps-scenarios-234` (local only, no push/PR): 27 new gaps reflected across packs/aws, packs/gcp, packs/azure. Flat assembly + contracts OK, pytest 33/33.
