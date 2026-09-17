#!/usr/bin/env bash
set -euo pipefail

# Rollback by swapping production and staging slots back.

RESOURCE_GROUP="${1:?Usage: rollback.sh <resource-group> <webapp-name>}"
WEBAPP_NAME="${2:?Usage: rollback.sh <resource-group> <webapp-name>}"

echo "Rolling back slot swap for ${WEBAPP_NAME} in ${RESOURCE_GROUP}..."
az webapp deployment slot swap \
  --resource-group "$RESOURCE_GROUP" \
  --name "$WEBAPP_NAME" \
  --slot staging \
  --target-slot production \
  --output none

echo "Rollback swap completed."
