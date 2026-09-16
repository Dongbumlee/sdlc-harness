// ⚠️ WARNING: Generated without ADO wiki AVM/Bicep standards.
// Review against team standards before deployment.
targetScope = 'resourceGroup'

@description('Primary Azure region for this environment.')
param location string

@description('Short application identifier used in resource names.')
param appName string

@description('Environment name: dev, staging, or production.')
@allowed([
  'dev'
  'staging'
  'production'
])
param environmentName string

@description('Tag: owning team or person.')
param owner string

@description('Tag: finance cost center code.')
param costCenter string

@description('Tag: deployment origin.')
param createdBy string

@secure()
@description('Administrator password for PostgreSQL Flexible Server.')
param postgresAdminPassword string

@description('Administrator username for PostgreSQL Flexible Server.')
param postgresAdminUser string = 'pgadmin'

@description('Container image repository name in ACR.')
param imageRepository string = 'feedbackapi'

@description('Container image tag to deploy.')
param imageTag string = 'latest'

@description('Optional list of firewall rules if public access is enabled.')
param postgresFirewallRules array = [
  {
    name: 'AllowAzureServices'
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
]

// WAF and landing-zone behavior toggles
param enablePrivateNetworking bool = true
param enableMonitoring bool = true
param enableRedundancy bool = false
param enableScalability bool = true

// Environment-aware sizing choices
var appServicePlanSkuName = environmentName == 'production' ? 'P1v3' : 'B1'
var appServicePlanCapacity = enableScalability && environmentName == 'production' ? 2 : 1
var postgresSkuName = environmentName == 'production' ? 'Standard_D4s_v3' : 'Standard_B2s'
var postgresStorageGb = environmentName == 'production' ? 256 : 128
var acrSkuName = environmentName == 'production' ? 'Premium' : 'Standard'

// Consistent naming
var shortEnv = environmentName == 'production' ? 'prd' : environmentName == 'staging' ? 'stg' : 'dev'
var vnetName = 'vnet-${appName}-${shortEnv}'
var appSubnetName = 'snet-appsvc-int'
var privateEndpointSubnetName = 'snet-private-endpoints'
var appServicePlanName = 'asp-${appName}-${shortEnv}'
var webAppResourceName = 'app-${appName}-${shortEnv}'
var keyVaultResourceName = toLower('kv-${appName}-${shortEnv}-${uniqueString(subscription().id, resourceGroup().id)}')
var acrName = toLower('cr${appName}${shortEnv}${uniqueString(subscription().id, resourceGroup().id)}')
var pgServerName = toLower('psql-${appName}-${shortEnv}-${uniqueString(subscription().id, resourceGroup().id)}')
var logAnalyticsName = 'log-${appName}-${shortEnv}'
var appInsightsName = 'appi-${appName}-${shortEnv}'
var userAssignedIdentityName = 'id-${appName}-${shortEnv}'

var standardTags = {
  environment: environmentName
  owner: owner
  'cost-center': costCenter
  'azd-env-name': environmentName
  TemplateName: 'feedbackapi-appservice-stack'
  CreatedBy: createdBy
}

// AVM: Shared Log Analytics workspace for diagnostics and App Insights
module logAnalytics 'br/public:avm/res/operational-insights/workspace:1.0.2' = {
  name: 'law-${shortEnv}'
  params: {
    name: logAnalyticsName
    location: location
    tags: standardTags
    retentionInDays: 30
    skuName: 'PerGB2018'
  }
}

// AVM: App Insights workspace-based instance for traces, requests, and dependencies
module appInsights 'br/public:avm/res/insights/components:1.0.2' = {
  name: 'appi-${shortEnv}'
  dependsOn: [
    logAnalytics
  ]
  params: {
    name: appInsightsName
    location: location
    tags: standardTags
    workspaceResourceId: resourceId('Microsoft.OperationalInsights/workspaces', logAnalyticsName)
    applicationType: 'web'
  }
}

// AVM: Virtual network with dedicated subnets for App Service integration and private endpoints
module vnet 'br/public:avm/res/network/virtual-network:1.1.4' = {
  name: 'vnet-${shortEnv}'
  params: {
    name: vnetName
    location: location
    tags: standardTags
    addressPrefixes: [
      '10.30.0.0/16'
    ]
    subnets: [
      {
        name: appSubnetName
        addressPrefix: '10.30.1.0/24'
        delegations: [
          {
            name: 'webapp-delegation'
            properties: {
              serviceName: 'Microsoft.Web/serverFarms'
            }
          }
        ]
      }
      {
        name: privateEndpointSubnetName
        addressPrefix: '10.30.2.0/24'
        privateEndpointNetworkPolicies: 'Disabled'
      }
    ]
  }
}

// AVM: ACR for secure container image storage
module acr 'br/public:avm/res/container-registry/registry:1.0.0' = {
  name: 'acr-${shortEnv}'
  params: {
    name: acrName
    location: location
    tags: standardTags
    sku: acrSkuName
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    zoneRedundancy: enableRedundancy ? 'Enabled' : 'Disabled'
  }
}

// AVM: Linux App Service Plan with env-dependent SKU (P1v3 for production, B1 otherwise)
module appServicePlan 'br/public:avm/res/web/serverfarm:1.1.2' = {
  name: 'plan-${shortEnv}'
  params: {
    name: appServicePlanName
    location: location
    tags: standardTags
    skuName: appServicePlanSkuName
    capacity: appServicePlanCapacity
    kind: 'linux'
    reserved: true
  }
}

resource userAssignedIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: userAssignedIdentityName
  location: location
  tags: standardTags
}

// AVM: Key Vault with RBAC enabled; app uses managed identity and Key Vault references
module keyVault 'br/public:avm/res/key-vault/vault:1.0.3' = {
  name: 'kv-${shortEnv}'
  params: {
    name: keyVaultResourceName
    location: location
    tags: standardTags
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
    skuName: 'standard'
    softDeleteRetentionInDays: 90
    enablePurgeProtection: environmentName == 'production'
  }
}

// AVM: PostgreSQL Flexible Server data tier
module postgres 'br/public:avm/res/db-for-postgresql/flexible-server:1.0.3' = {
  name: 'postgres-${shortEnv}'
  params: {
    name: pgServerName
    location: location
    tags: standardTags
    administratorLogin: postgresAdminUser
    administratorLoginPassword: postgresAdminPassword
    skuName: postgresSkuName
    version: '16'
    storageSizeGB: postgresStorageGb
    highAvailabilityMode: enableRedundancy ? 'ZoneRedundant' : 'Disabled'
    publicNetworkAccess: enablePrivateNetworking ? 'Disabled' : 'Enabled'
  }
}

// AVM: Linux Web App running a container image from ACR
module webApp 'br/public:avm/res/web/site:1.1.3' = {
  name: 'web-${shortEnv}'
  dependsOn: [
    appServicePlan
    acr
    keyVault
    appInsights
  ]
  params: {
    name: webAppResourceName
    location: location
    tags: standardTags
    kind: 'app,linux,container'
    serverFarmResourceId: resourceId('Microsoft.Web/serverfarms', appServicePlanName)
    httpsOnly: true
    identityType: 'SystemAssigned,UserAssigned'
    userAssignedIdentities: [
      userAssignedIdentity.id
    ]
    keyVaultReferenceIdentity: userAssignedIdentity.id
    siteConfig: {
      linuxFxVersion: 'DOCKER|${acrName}.azurecr.io/${imageRepository}:${imageTag}'
      alwaysOn: environmentName == 'production'
      healthCheckPath: '/health'
      acrUseManagedIdentityCreds: true
      acrUserManagedIdentityID: userAssignedIdentity.properties.clientId
      ftpsState: 'Disabled'
      minimumTlsVersion: '1.2'
      appSettings: [
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'ENVIRONMENT'
          value: environmentName
        }
        {
          name: 'APPINSIGHTS_CONNECTION_STRING'
          value: reference(resourceId('Microsoft.Insights/components', appInsightsName), '2020-02-02').ConnectionString
        }
        {
          name: 'POSTGRES_HOST'
          value: '${pgServerName}.postgres.database.azure.com'
        }
        {
          name: 'POSTGRES_DB'
          value: 'appdb'
        }
        {
          name: 'POSTGRES_USER'
          value: '${postgresAdminUser}'
        }
        {
          name: 'POSTGRES_PASSWORD'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultResourceName};SecretName=postgres-admin-password)'
        }
      ]
    }
  }
}

resource webAppExisting 'Microsoft.Web/sites@2023-12-01' existing = {
  name: webAppResourceName
}

resource appServicePlanExisting 'Microsoft.Web/serverfarms@2023-12-01' existing = {
  name: appServicePlanName
}

resource keyVaultExisting 'Microsoft.KeyVault/vaults@2023-07-01' existing = {
  name: keyVaultResourceName
}

resource postgresExisting 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' existing = {
  name: pgServerName
}

resource vnetExisting 'Microsoft.Network/virtualNetworks@2023-09-01' existing = {
  name: vnetName
}

resource acrExisting 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = {
  name: acrName
}

resource logAnalyticsExisting 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: logAnalyticsName
}

resource appInsightsExisting 'Microsoft.Insights/components@2020-02-02' existing = {
  name: appInsightsName
}

// App Service regional VNet integration
resource webAppVnetIntegration 'Microsoft.Web/sites/networkConfig@2023-12-01' = if (enablePrivateNetworking) {
  name: '${webAppResourceName}/virtualNetwork'
  properties: {
    subnetResourceId: resourceId('Microsoft.Network/virtualNetworks/subnets', vnetName, appSubnetName)
    swiftSupported: true
  }
  dependsOn: [
    webApp
    vnet
  ]
}

// PostgreSQL private endpoint with private DNS resolution
resource postgresPrivateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = if (enablePrivateNetworking) {
  name: 'privatelink.postgres.database.azure.com'
  location: 'global'
  tags: standardTags
}

resource postgresPrivateDnsVnetLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = if (enablePrivateNetworking) {
  name: '${postgresPrivateDnsZone.name}/${vnetName}-link'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetExisting.id
    }
  }
  dependsOn: [
    postgresPrivateDnsZone
    vnet
  ]
}

resource postgresPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-09-01' = if (enablePrivateNetworking) {
  name: 'pe-${pgServerName}'
  location: location
  tags: standardTags
  properties: {
    subnet: {
      id: resourceId('Microsoft.Network/virtualNetworks/subnets', vnetName, privateEndpointSubnetName)
    }
    privateLinkServiceConnections: [
      {
        name: 'psc-${pgServerName}'
        properties: {
          privateLinkServiceId: postgresExisting.id
          groupIds: [
            'postgresqlServer'
          ]
        }
      }
    ]
  }
  dependsOn: [
    postgres
    vnet
  ]
}

resource postgresPrivateEndpointDnsGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-09-01' = if (enablePrivateNetworking) {
  name: '${postgresPrivateEndpoint.name}/default'
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'postgresDns'
        properties: {
          privateDnsZoneId: postgresPrivateDnsZone.id
        }
      }
    ]
  }
  dependsOn: [
    postgresPrivateDnsVnetLink
    postgresPrivateEndpoint
  ]
}

// Optional public firewall rules for scenarios where public access is intentionally enabled
resource postgresFirewallRuleResources 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-06-01-preview' = [for rule in postgresFirewallRules: if (!enablePrivateNetworking) {
  name: '${pgServerName}/${rule.name}'
  properties: {
    startIpAddress: rule.startIpAddress
    endIpAddress: rule.endIpAddress
  }
  dependsOn: [
    postgres
  ]
}]

// Staging slot for blue/green deployment
resource stagingSlot 'Microsoft.Web/sites/slots@2023-12-01' = {
  name: '${webAppResourceName}/staging'
  location: location
  tags: union(standardTags, {
    slot: 'staging'
  })
  properties: {
    serverFarmId: appServicePlanExisting.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'DOCKER|${acrName}.azurecr.io/${imageRepository}:${imageTag}'
      healthCheckPath: '/health'
      acrUseManagedIdentityCreds: true
      acrUserManagedIdentityID: userAssignedIdentity.properties.clientId
      appSettings: [
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'ENVIRONMENT'
          value: '${environmentName}-staging'
        }
        {
          name: 'APPINSIGHTS_CONNECTION_STRING'
          value: reference(appInsightsExisting.id, '2020-02-02').ConnectionString
        }
        {
          name: 'POSTGRES_HOST'
          value: '${pgServerName}.postgres.database.azure.com'
        }
        {
          name: 'POSTGRES_DB'
          value: 'appdb'
        }
        {
          name: 'POSTGRES_USER'
          value: '${postgresAdminUser}'
        }
        {
          name: 'POSTGRES_PASSWORD'
          value: '@Microsoft.KeyVault(VaultName=${keyVaultResourceName};SecretName=postgres-admin-password)'
        }
      ]
    }
  }
  dependsOn: [
    webApp
  ]
}

// Production slot swap behavior: DB and secrets settings stick to slot
resource slotConfig 'Microsoft.Web/sites/config@2023-12-01' = {
  name: '${webAppResourceName}/slotConfigNames'
  properties: {
    appSettingNames: [
      'POSTGRES_HOST'
      'POSTGRES_DB'
      'POSTGRES_USER'
      'POSTGRES_PASSWORD'
      'APPINSIGHTS_CONNECTION_STRING'
    ]
  }
  dependsOn: [
    stagingSlot
  ]
}

// RBAC: App identity can pull images from ACR
resource acrPullRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acrExisting.id, userAssignedIdentity.properties.principalId, 'AcrPull')
  scope: acrExisting
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d') // AcrPull
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [
    acr
    userAssignedIdentity
  ]
}

// RBAC: App identity can read Key Vault secrets
resource keyVaultSecretsUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(keyVaultExisting.id, userAssignedIdentity.properties.principalId, 'KeyVaultSecretsUser')
  scope: keyVaultExisting
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6') // Key Vault Secrets User
    principalId: userAssignedIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
  dependsOn: [
    keyVault
    userAssignedIdentity
  ]
}

// Seed secret value; app reads it via Key Vault reference
resource postgresAdminPasswordSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  name: '${keyVaultResourceName}/postgres-admin-password'
  properties: {
    value: postgresAdminPassword
  }
  dependsOn: [
    keyVault
  ]
}

// Centralized diagnostics to Log Analytics
resource diagAcr 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableMonitoring) {
  name: 'diag-acr'
  scope: acrExisting
  properties: {
    workspaceId: logAnalyticsExisting.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource diagPlan 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableMonitoring) {
  name: 'diag-plan'
  scope: appServicePlanExisting
  properties: {
    workspaceId: logAnalyticsExisting.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource diagWebApp 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableMonitoring) {
  name: 'diag-webapp'
  scope: webAppExisting
  properties: {
    workspaceId: logAnalyticsExisting.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource diagSlot 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableMonitoring) {
  name: 'diag-webapp-staging-slot'
  scope: stagingSlot
  properties: {
    workspaceId: logAnalyticsExisting.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource diagPostgres 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableMonitoring) {
  name: 'diag-postgres'
  scope: postgresExisting
  properties: {
    workspaceId: logAnalyticsExisting.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource diagKeyVault 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableMonitoring) {
  name: 'diag-keyvault'
  scope: keyVaultExisting
  properties: {
    workspaceId: logAnalyticsExisting.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource diagVnet 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableMonitoring) {
  name: 'diag-vnet'
  scope: vnetExisting
  properties: {
    workspaceId: logAnalyticsExisting.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

resource diagAppInsights 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (enableMonitoring) {
  name: 'diag-appinsights'
  scope: appInsightsExisting
  properties: {
    workspaceId: logAnalyticsExisting.id
    logs: [
      {
        categoryGroup: 'allLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
  }
}

output webAppName string = webAppResourceName
output productionUrl string = 'https://${webAppResourceName}.azurewebsites.net'
output stagingUrl string = 'https://${webAppResourceName}-staging.azurewebsites.net'
output keyVaultName string = keyVaultResourceName
