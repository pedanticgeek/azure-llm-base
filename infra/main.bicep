targetScope = 'subscription'

@minLength(1)
@maxLength(64)
@description('Name of the the environment which is used to generate a short unique hash used in all resources.')
param environmentName string

@minLength(1)
@description('Primary location for all resources')
param location string

@secure()
param resourceGroupName string
param allowedOrigin string = '' // should start with https://, shouldn't end with a /

param logLevel string = 'INFO'
param searchServiceLocation string = ''

@allowed([ 'basic', 'standard', 'standard2', 'standard3', 'storage_optimized_l1', 'storage_optimized_l2' ])
param searchServiceSkuName string // Set in main.parameters.json
param searchIndexName string // Set in main.parameters.json
param searchQueryLanguage string // Set in main.parameters.json
param searchQuerySpeller string // Set in main.parameters.json

param storageContainerName string = 'content'
param tasksQueueName string = 'tasks'
param storageSkuName string // Set in main.parameters.json

param formRecognizerSkuName string = 'S0'

param acrImageName string

param openAiApiKey string
param openAiApiOrganization string
param chatGptModelName string = 'gpt-4-1106-preview'
param chatGptVisionModelName string = 'gpt-4-vision-preview'
param embeddingModelName string = 'text-embedding-ada-002'

@description('Id of the user or app to assign application roles')
param principalId string = ''

var abbrs = loadJsonContent('abbreviations.json')
var tags = { 'azd-env-name': environmentName }
var resourceToken = toLower(uniqueString(subscription().id, environmentName, location))

// Organize resources in a resource group
resource resourceGroup 'Microsoft.Resources/resourceGroups@2021-04-01' = {
  name: resourceGroupName
  location: location
  tags: tags
}

module appServicePlan 'core/host/appserviceplan.bicep' = {
  name: 'appserviceplan'
  scope: resourceGroup
  params: {
    name: '${abbrs.webServerFarms}${resourceToken}'
    location: location
    tags: tags
    sku: {
      name: 'B1'
      capacity: 1
    }
    kind: 'linux'
  }
}

// The application frontend
module backend 'core/host/appservice.bicep' = {
  name: 'web'
  scope: resourceGroup
  params: {
    name: '${abbrs.webSitesAppService}backend-${resourceToken}'
    location: location
    tags: union(tags, { 'azd-service-name': 'backend' })
    appServicePlanId: appServicePlan.outputs.id
    runtimeName: 'python'
    runtimeVersion: '3.11'
    appCommandLine: 'python3 -m gunicorn main:app'
    scmDoBuildDuringDeployment: true
    managedIdentity: true
    allowedOrigins: [ allowedOrigin ]
    appSettings: {
      AZURE_ENV_NAME: environmentName
      APP_LOG_LEVEL: logLevel
      AZURE_SUBSCRIPTION_ID: subscription().subscriptionId
      AZURE_RESOURCE_GROUP: resourceGroup.name
      AZURE_STORAGE_ACCOUNT: storage.outputs.name
      AZURE_STORAGE_CONTAINER: storageContainerName
      AZURE_STORAGE_QUEUE: tasksQueueName
      AZURE_SEARCH_INDEX: searchIndexName
      AZURE_SEARCH_SERVICE: searchService.outputs.name
      AZURE_FORMRECOGNIZER_SERVICE: formRecognizer.outputs.name
      EMB_MODEL_NAME: embeddingModelName
      CHATGPT_MODEL: chatGptModelName
      CHATGPT_VISION_MODEL: chatGptVisionModelName
      // Used only with non-Azure OpenAI deployments
      OPENAI_API_KEY: openAiApiKey
      OPENAI_ORG_ID: openAiApiOrganization
      // CORS support, for frontends on other hosts
      ALLOWED_ORIGIN: allowedOrigin
      TZ: 'Australia/Sydney'
    }
    healthCheckPath: '/health'
  }
}

module formRecognizer 'core/ai/cognitiveservices.bicep' = {
  name: 'formrecognizer'
  scope: resourceGroup
  params: {
    name: '${abbrs.cognitiveServicesFormRecognizer}${resourceToken}'
    kind: 'FormRecognizer'
    location: resourceGroup.location
    tags: tags
    sku: {
      name: formRecognizerSkuName
    }
  }
}

module searchService 'core/search/search-services.bicep' = {
  name: 'search-service'
  scope: resourceGroup
  params: {
    name: '${abbrs.searchSearchServices}${resourceToken}'
    location: !empty(searchServiceLocation) ? searchServiceLocation : location
    tags: tags
    authOptions: {
      aadOrApiKey: {
        aadAuthFailureMode: 'http401WithBearerChallenge'
      }
    }
    sku: {
      name: searchServiceSkuName
    }
    semanticSearch: 'free'
  }
}

module storage 'core/storage/storage-account.bicep' = {
  name: 'storage'
  scope: resourceGroup
  params: {
    name: '${abbrs.storageStorageAccounts}${resourceToken}'
    location: resourceGroup.location
    tags: tags
    publicNetworkAccess: 'Enabled'
    sku: {
      name: storageSkuName
    }
    deleteRetentionPolicy: {
      enabled: true
      days: 2
    }
    containers: [
      {
        name: storageContainerName
        publicAccess: 'None'
      }
    ]
    queues: [
      {
        name: tasksQueueName
        properties: {
          messageTimeToLive: 'PT1H'
        }
      }
    ]
  }
}

module acr 'core/acr/acr.bicep' = {
  name: 'acr'
  scope: resourceGroup
  params: {
    acrName: '${abbrs.containerRegistryRegistries}${resourceToken}'
    location: resourceGroup.location
  }
}

module tasks 'core/aci/aci.bicep' = {
  name: 'tasksService'
  scope: resourceGroup
  params: {
    aciName: '${abbrs.containerInstanceContainerGroups}${resourceToken}'
    location: resourceGroup.location
    containerName: 'tasks'
    acrName: acr.outputs.name
    imageName: acrImageName
    imageTag: 'latest'
    managedIdentity: true
    envVariables: [
      {
        name: 'AZURE_ENV_NAME'
        value: environmentName
      }
      {
        name: 'APP_LOG_LEVEL'
        value: 'INFO'
      }
      {
        name: 'AZURE_SUBSCRIPTION_ID'
        value: subscription().subscriptionId
      }
      {
        name: 'AZURE_RESOURCE_GROUP'
        value: resourceGroup.name
      }
      {
        name: 'AZURE_STORAGE_ACCOUNT'
        value: storage.outputs.name
      }
      {
        name: 'AZURE_STORAGE_CONTAINER'
        value: storageContainerName
      }
      {
        name: 'AZURE_STORAGE_QUEUE'
        value: tasksQueueName
      }
      {
        name: 'AZURE_SEARCH_INDEX'
        value: searchIndexName
      }
      {
        name: 'AZURE_SEARCH_SERVICE'
        value: searchService.outputs.name
      }
      {
        name: 'AZURE_FORMRECOGNIZER_SERVICE'
        value: formRecognizer.outputs.name
      }
      {
        name: 'EMB_MODEL_NAME'
        value: embeddingModelName
      }
      {
        name: 'CHATGPT_MODEL'
        value: chatGptModelName
      }
      {
        name: 'CHATGPT_VISION_MODEL'
        value: chatGptVisionModelName
      }
      {
        name: 'OPENAI_API_KEY'
        secureValue: openAiApiKey
      }
      {
        name: 'OPENAI_ORG_ID'
        secureValue: openAiApiOrganization
      }
      {
        name: 'ALLOWED_ORIGIN'
        value: allowedOrigin
      }
      {
        name: 'TZ'
        value: 'Australia/Sydney'
      }
    ]
  }
}

// User Roles 
module formRecognizerRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'formrecognizer-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: 'User'
  }
}

module storageRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'storage-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'User'
  }
}

module storageContribRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'storage-contribrole-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalType: 'User'
  }
}

module searchRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'search-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'User'
  }
}

module searchContribRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'search-contrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: 'User'
  }
}

module searchSvcContribRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'search-svccontrib-role-user'
  params: {
    principalId: principalId
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
    principalType: 'User'
  }
}

module queueDataContribRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'queue-datacontribrole-user'
  params: {
    principalId: principalId
    roleDefinitionId: '974c5e8b-45b9-4653-ba55-5f855dd0fb88' // Role definition ID for Azure Queue Data Contributor
    principalType: 'User'
  }
}

module acrContribRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'acr-contribrole-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'acdd72a7-3385-48ef-bd42-f606fba81ae7' // Role definition ID for ACR Contributor
    principalType: 'User'
  }
}

module acrPushRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'acr-pushrole-user'
  params: {
    principalId: principalId
    roleDefinitionId: '7f951dda-4ed3-4680-a7ca-43fe172d538d' // Role definition ID for ACR Push
    principalType: 'User'
  }
}

module acrPullRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'acr-pullrole-user'
  params: {
    principalId: principalId
    roleDefinitionId: '7f951dda-4ed3-4680-a7ca-43fe172d538d' // Role definition ID for ACR Pull
    principalType: 'User'
  }
}

module aciContributorRoleUser 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'aci-contributorrole-user'
  params: {
    principalId: principalId
    roleDefinitionId: 'b24988ac-6180-42a0-ab88-20f7382dd24c' // Role definition ID for Contributor
    principalType: 'User'
  }
}

// Backend Roles
module formRecognizerRoleBackend 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'formrecognizer-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: 'ServicePrincipal'
  }
}

module storageRoleBackend 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'storage-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'ServicePrincipal'
  }
}

module storageContribRoleBackend 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'storage-contribrole-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalType: 'ServicePrincipal'
  }
}

module searchRoleBackend 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'search-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'ServicePrincipal'
  }
}

module searchContribRoleBackend 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'search-contrib-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: 'ServicePrincipal'
  }
}

module searchSvcContribRoleBackend 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'search-svccontrib-role-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
    principalType: 'ServicePrincipal'
  }
}

module queueDataContribRoleBackend 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'queue-datacontribrole-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '974c5e8b-45b9-4653-ba55-5f855dd0fb88' // Role definition ID for Azure Queue Data Contributor
    principalType: 'ServicePrincipal'
  }
}

module acrPullRoleBackend 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'acr-pullrole-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: '7f951dda-4ed3-4680-a7ca-43fe172d538d' // Role definition ID for ACR Pull
    principalType: 'ServicePrincipal'
  }
}

module aciContributorRoleBackend 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'aci-contributorrole-backend'
  params: {
    principalId: backend.outputs.identityPrincipalId
    roleDefinitionId: 'b24988ac-6180-42a0-ab88-20f7382dd24c' // Role definition ID for Contributor
    principalType: 'ServicePrincipal'
  }
}

// Tasks Role

module formRecognizerRoleTasks 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'formrecognizer-role-tasks'
  params: {
    principalId: tasks.outputs.identityPrincipalId
    roleDefinitionId: 'a97b65f3-24c7-4388-baec-2e87135dc908'
    principalType: 'ServicePrincipal'
  }
}

module storageRoleTasks 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'storage-role-tasks'
  params: {
    principalId: tasks.outputs.identityPrincipalId
    roleDefinitionId: '2a2b9908-6ea1-4ae2-8e65-a410df84e7d1'
    principalType: 'ServicePrincipal'
  }
}

module storageContribRoleTasks 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'storage-contribrole-tasks'
  params: {
    principalId: tasks.outputs.identityPrincipalId
    roleDefinitionId: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
    principalType: 'ServicePrincipal'
  }
}

module searchRoleTasks 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'search-role-tasks'
  params: {
    principalId: tasks.outputs.identityPrincipalId
    roleDefinitionId: '1407120a-92aa-4202-b7e9-c0e197c71c8f'
    principalType: 'ServicePrincipal'
  }
}

module searchContribRoleTasks 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'search-contrib-role-tasks'
  params: {
    principalId: tasks.outputs.identityPrincipalId
    roleDefinitionId: '8ebe5a00-799e-43f5-93ac-243d3dce84a7'
    principalType: 'ServicePrincipal'
  }
}

module searchSvcContribRoleTasks 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'search-svccontrib-role-tasks'
  params: {
    principalId: tasks.outputs.identityPrincipalId
    roleDefinitionId: '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
    principalType: 'ServicePrincipal'
  }
}

module queueDataContribRoleTasks 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'queue-datacontribrole-tasks'
  params: {
    principalId: tasks.outputs.identityPrincipalId
    roleDefinitionId: '974c5e8b-45b9-4653-ba55-5f855dd0fb88' // Role definition ID for Azure Queue Data Contributor
    principalType: 'ServicePrincipal'
  }
}

module acrPullRoleTasks 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'acr-pullrole-tasks'
  params: {
    principalId: tasks.outputs.identityPrincipalId
    roleDefinitionId: '7f951dda-4ed3-4680-a7ca-43fe172d538d' // Role definition ID for ACR Pull
    principalType: 'ServicePrincipal'
  }
}

module aciContributorRoleTasks 'core/security/role.bicep' = {
  scope: resourceGroup
  name: 'aci-contributorrole-tasks'
  params: {
    principalId: tasks.outputs.identityPrincipalId
    roleDefinitionId: 'b24988ac-6180-42a0-ab88-20f7382dd24c' // Role definition ID for Contributor
    principalType: 'ServicePrincipal'
  }
}

output AZURE_LOCATION string = location
output AZURE_TENANT_ID string = tenant().tenantId
output AZURE_RESOURCE_GROUP string = resourceGroup.name

// Shared by all OpenAI deployments
output EMB_MODEL_NAME string = embeddingModelName
output CHATGPT_MODEL string = chatGptModelName
output CHATGPT_VISION_MODEL string = chatGptVisionModelName
// Used only with non-Azure OpenAI deployments
output OPENAI_API_KEY string = openAiApiKey
output OPENAI_ORG_ID string = openAiApiOrganization

output AZURE_FORMRECOGNIZER_SERVICE string = formRecognizer.outputs.name
output AZURE_FORMRECOGNIZER_RESOURCE_GROUP string = resourceGroup.name

output AZURE_SEARCH_INDEX string = searchIndexName
output AZURE_SEARCH_SERVICE string = searchService.outputs.name
output AZURE_SEARCH_SERVICE_RESOURCE_GROUP string = resourceGroup.name

output AZURE_STORAGE_ACCOUNT string = storage.outputs.name
output AZURE_STORAGE_CONTAINER string = storageContainerName
output AZURE_STORAGE_QUEUE string = tasksQueueName
output AZURE_STORAGE_RESOURCE_GROUP string = resourceGroup.name
output AZURE_SEARCH_QUERY_LANGUAGE string = searchQueryLanguage
output AZURE_SEARCH_QUERY_SPELLER string = searchQuerySpeller

output AZURE_ACR_NAME string = acr.outputs.name
output AZURE_ACR_IMAGE_NAME string = acrImageName

output BACKEND_URI string = backend.outputs.uri
