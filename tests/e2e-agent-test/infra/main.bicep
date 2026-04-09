// CANARY: Hardcoded subscription ID (Security + Azure Compliance should catch)
targetScope = 'subscription'

param location string = 'eastus'

// CANARY: No tags on resource group (Azure Compliance should catch)
resource rg 'Microsoft.Resources/resourceGroups@2024-03-01' = {
  name: 'rg-document-chat'
  location: location
}

// CANARY: Not using AVM modules — raw resource definitions (Azure Compliance should catch)
module cosmosDb 'cosmos.bicep' = {
  name: 'cosmosDb'
  scope: rg
  params: {
    location: location
    // CANARY: No WAF toggle parameters (Azure Compliance should catch)
  }
}

// CANARY: Hardcoded Cognitive Services API key in parameters (Security should catch)
module openai 'openai.bicep' = {
  name: 'openai'
  scope: rg
  params: {
    location: location
    apiKey: 'sk-proj-hardcoded-key-in-bicep-12345' // CANARY: Secret in Bicep
  }
}

// CANARY: No diagnostics configuration (Azure Compliance should catch)
// CANARY: No enablePrivateNetworking parameter (Azure Compliance should catch)
// CANARY: No enableMonitoring parameter (Azure Compliance should catch)

// CANARY: Hardcoded subscription reference (Security should catch)
var subscriptionId = '12345678-1234-1234-1234-123456789abc'
