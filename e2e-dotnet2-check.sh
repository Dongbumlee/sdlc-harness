#!/bin/bash
mkdir -p /home/azureuser/.vm-claims
printf 'harness %s e2e-dotnet2 publish check\n' "$(date -u +%FT%TZ)" > /home/azureuser/.vm-claims/harness
echo "== claims:"; ls /home/azureuser/.vm-claims/
echo "== e2e dirs:"; ls -d /home/azureuser/e2e* 2>/dev/null
APP=$(ls -d /home/azureuser/e2e-dotnet2/app 2>/dev/null || ls -d /home/azureuser/e2e-dotnet2 2>/dev/null)
echo "== app dir: $APP"
sudo -u azureuser git -C "$APP" status --porcelain=v1 -b 2>&1 | head -8
echo "== remotes:"; sudo -u azureuser git -C "$APP" remote -v 2>&1
echo "== log:"; sudo -u azureuser git -C "$APP" log --oneline -5 2>&1
echo "== last commit date:"; sudo -u azureuser git -C "$APP" log -1 --format=%cI 2>&1
chown -R azureuser:azureuser /home/azureuser/.vm-claims
