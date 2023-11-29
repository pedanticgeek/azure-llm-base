source .azure/llm-base/.env
echo "Logging in"
az acr login --name $AZURE_ACR_NAME
echo "Building the image"
docker buildx build --platform linux/amd64 -f ./docker/Dockerfile -t ${AZURE_ACR_NAME}.azurecr.io/${AZURE_ACR_IMAGE_NAME}:latest .
echo "Pushing the image to Azure ACR"
docker push ${AZURE_ACR_NAME}.azurecr.io/${AZURE_ACR_IMAGE_NAME}:latest