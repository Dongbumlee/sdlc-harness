// ⚠️ WARNING: Generated without ADO wiki AVM/Bicep standards.
// Review against team standards before deployment.
targetScope = 'subscription'

@description('Primary Azure region for this environment.')
param location string = deployment().location

@description('Short application identifier used in resource names.')
param appName string = 'feedbackapi'

@description('Environment name: dev, staging, or production.')
@allowed([
  'dev'
  'staging'
  'production'
])
param environmentName string

@description('Resource group name for the environment.')
param resourceGroupName string = 'rg-${appName}-${environmentName}'

@description('Tag: owning team or person.')
param owner string

@description('Tag: finance cost center code.')
param costCenter string

@description('Tag: deployment origin.')
param createdBy string = 'azd'

@description('Administrator username for PostgreSQL Flexible Server.')
param postgresAdminUser string = 'pgadmin'

@secure()
@description('Administrator password for PostgreSQL Flexible Server.')
param postgresAdminPassword string

@description('Container image repository in ACR.')
param imageRepository string = 'feedbackapi'

@description('Container image tag to deploy.')
param imageTag string = 'latest'

@description('Optional firewall rules when public PostgreSQL access is enabled.')
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

// Shared tags across all resources
var standardTags = {
  environment: environmentName
  owner: owner
  'cost-center': costCenter
  'azd-env-name': environmentName
  TemplateName: 'feedbackapi-appservice-stack'
  CreatedBy: createdBy
}

// AVM: Create resource group with standard tags
module rg 'br/public:avm/res/resources/resource-group:1.0.2' = {
  name: 'rg-${environmentName}'
  params: {
    name: resourceGroupName
    location: location
    tags: standardTags
  }
}

// Deploy the full platform stack into the resource group
module appStack './modules/app-stack.bicep' = {
  name: 'app-stack-${environmentName}'
  scope: resourceGroup(resourceGroupName)
  dependsOn: [
    rg
  ]
  params: {
    location: location
    appName: appName
    environmentName: environmentName
    owner: owner
    costCenter: costCenter
    createdBy: createdBy
    enablePrivateNetworking: enablePrivateNetworking
    enableMonitoring: enableMonitoring
    enableRedundancy: enableRedundancy
    enableScalability: enableScalability
    postgresAdminUser: postgresAdminUser
    postgresAdminPassword: postgresAdminPassword
    imageRepository: imageRepository
    imageTag: imageTag
    postgresFirewallRules: postgresFirewallRules
  }
}

output webAppName string = appStack.outputs.webAppName
output productionUrl string = appStack.outputs.productionUrl
output stagingUrl string = appStack.outputs.stagingUrl
output keyVaultName string = appStack.outputs.keyVaultName
