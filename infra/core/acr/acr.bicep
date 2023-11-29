param acrName string
param location string
param sku string = 'Standard' // Change SKU as needed: Basic, Standard, or Premium

resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: acrName
  location: location
  sku: {
    name: sku
  }
  properties: {
    adminUserEnabled: true
    anonymousPullEnabled: true
    publicNetworkAccess: 'Enabled'
  }
}

output loginServer string = acr.properties.loginServer
output name string = acr.name
