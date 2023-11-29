param aciName string
param location string
param containerName string
param acrName string
param imageName string
param imageTag string
param envVariables array = []
param sku string = 'Standard'
param keyVaultName string = ''
param managedIdentity bool = !empty(keyVaultName)

resource tasksService 'Microsoft.ContainerInstance/containerGroups@2023-05-01' = {
  name: aciName
  location: location
  properties: {
    containers: [
      {
        name: containerName
        properties: {
          environmentVariables: envVariables
          image: '${acrName}.azurecr.io/${imageName}:${imageTag}'
          resources: {
            requests: {
              cpu: 1
              memoryInGB: 1
            }
          }
        }
      }
    ]
    osType: 'Linux'
    restartPolicy: 'OnFailure'
    sku: sku
  }

  identity: { type: managedIdentity ? 'SystemAssigned' : 'None' }
}

output identityPrincipalId string = managedIdentity ? tasksService.identity.principalId : ''
