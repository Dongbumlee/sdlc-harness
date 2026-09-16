# Deployment and Promotion Strategy

## Environments

- **dev**: continuous deployment, low-cost SKU profile.
- **staging**: release candidate validation in staging slot.
- **production**: blue/green via slot swap.

## Promotion flow

1. Build and push image to ACR.
2. Deploy infra and app image to **staging slot**.
3. Run health checks (`/health`) and smoke tests.
4. Manual approval gate.
5. Swap `staging` -> `production`.
6. Run production smoke tests.
7. Auto-rollback (swap back) on smoke-test failure.

## Rollback procedure

- Pipeline rollback step automatically runs:
  - `scripts/rollback.sh <resource-group> <webapp-name>`
- Manual fallback command:

```bash
az webapp deployment slot swap \
  --resource-group <rg> \
  --name <webapp-name> \
  --slot staging \
  --target-slot production
```

## azd commands

```bash
azd env new <dev|staging|production>
azd provision
azd deploy
```
