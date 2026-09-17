#!/usr/bin/env bash
set -euo pipefail

# Post-provision hook:
# - stores DB connection pieces in Key Vault (if not already set)
# - enables App Service health check behavior

RESOURCE_GROUP="${AZURE_RESOURCE_GROUP:?AZURE_RESOURCE_GROUP is required}"
WEBAPP_NAME="${WEBAPP_NAME:?WEBAPP_NAME is required}"
KEY_VAULT_NAME="${KEY_VAULT_NAME:?KEY_VAULT_NAME is required}"
POSTGRES_SERVER_NAME="${POSTGRES_SERVER_NAME:?POSTGRES_SERVER_NAME is required}"
POSTGRES_ADMIN_USER="${POSTGRES_ADMIN_USER:?POSTGRES_ADMIN_USER is required}"
POSTGRES_ADMIN_PASSWORD="${POSTGRES_ADMIN_PASSWORD:?POSTGRES_ADMIN_PASSWORD is required}"

az keyvault secret set \
  --vault-name "$KEY_VAULT_NAME" \
  --name postgres-admin-password \
  --value "$POSTGRES_ADMIN_PASSWORD" \
  --output none

az keyvault secret set \
  --vault-name "$KEY_VAULT_NAME" \
  --name postgres-username \
  --value "$POSTGRES_ADMIN_USER" \
  --output none

az keyvault secret set \
  --vault-name "$KEY_VAULT_NAME" \
  --name postgres-host \
  --value "${POSTGRES_SERVER_NAME}.postgres.database.azure.com" \
  --output none

az webapp update \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEBAPP_NAME" \
  --set siteConfig.healthCheckPath=/health \
  --output none

echo "Post-provisioning completed."
