# Azure LLM App Base

This is the base code for running an LLM App on Azure that I use for my clients.
It's based on the [original solution from Microsoft](https://github.com/Azure-Samples/azure-search-openai-demo), but I've added/removed some things to suit my needs.

## Key Changes

1. I've added a few more features to the UI, such as the ability to upload files and delete files.
2. The same above features added to API, so you can use it in your own apps.
3. I've added Storage Queue and Container Instances (ACI) to run long LLM tasks, such as document scanning and indexing.
4. Removed authentication, because it's not needed for the base solution, and everyone wants things set up differently.
5. Reorganized the entire structure of the Backend. I am sure, Azure engineers know what they are doing, but it was confusing the hell out of me.
6. I've removed Azure OpenAI service and left only the OpenAI API, because it's a few months ahead of Azure and two months is a significant time in AI nowadays.
7. I've added OpenAI assistants approach for documents summarization and text recognition. I've left old approach for /chat, because Assistants don't yet support streaming.
8. I've added the GPT-4-Vision model to scan files where OCR is not enough, such as graphs (without much numbers) or diagrams. It's not perfect, but way better than OCR solutions.
9. Removed all powershell scripts and only kept bash scripts for Linux/MacOS users - damn, [devgeek27](https://github.com/devgeek27)!!!, hooked me to macs.

## Infrastructure

#### Deploy

`azd up` - to deploy the entire solution to Azure. You need to have Azure CLI installed and logged in.
It will fail because there is no image in the ACR.
`bash deploy_image.sh` to push the image
`azd up` again to deploy the entire solution to Azure.

#### Destroy

`azd down` - to remove the entire solution from Azure.

## Local Run

> Note! You can only run local once you have Cloud resources deployed. Otherwise, you will get errors.

## Backend

The backend API runs on python/quart/uvicorn.

```
cd app/backend
bash run_quart.sh
```

## Frontend

The frontend runs on React.

```
cd app/frontend
npm run dev
```
