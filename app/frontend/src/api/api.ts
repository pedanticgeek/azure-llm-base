const BACKEND_URI = "";

import { ChatAppResponseOrError, ChatAppRequest, DocumentUploadRequest, DocumentUploadResponse, DocumentsStructureResponse } from "./models";
import { useLogin } from "../authConfig";

function getHeaders(idToken: string | undefined): Record<string, string> {
    var headers: Record<string, string> = {
        "Content-Type": "application/json"
    };

    if (useLogin) {
        if (idToken) {
            headers["Authorization"] = `Bearer ${idToken}`;
        }
    }

    return headers;
}

export async function getDocumentsStructureApi(idToken: string | undefined): Promise<DocumentsStructureResponse> {
    const response = await fetch(`${BACKEND_URI}/get_docs_info`, {
        method: "GET",
        headers: getHeaders(idToken)
    });

    const parsedResponse: ChatAppResponseOrError = await response.json();
    if (response.status > 299 || !response.ok) {
        throw Error(parsedResponse.error || "Unknown error");
    }
    return { documents: parsedResponse } as DocumentsStructureResponse;
}

export async function uploadDocumentsApi(request: DocumentUploadRequest[], idToken: string | undefined): Promise<DocumentUploadResponse[]> {
    const formData = new FormData();
    request.forEach(request => {
        formData.append(
            "document",
            new Blob([request.fileContent], { type: "application/octet-stream" }),
            request.scan ? request.filename + ".v-scan" : request.filename
        );
    });

    const headers = getHeaders(idToken);
    delete headers["Content-Type"];

    const response = await fetch(`${BACKEND_URI}/upload_documents`, {
        method: "POST",
        headers: headers,
        body: formData
    });

    if (!response.ok) {
        const htmlText = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlText, "text/html");
        const pElement = doc.querySelector("p");
        const errorMessage = pElement ? pElement.textContent : "Unknown error";
        throw new Error(errorMessage || undefined);
    }
    const parsedResponse = await response.json();
    return parsedResponse;
}

export async function deleteDocumentApi(request: { filename: string }, idToken: string | undefined): Promise<Response> {
    return await fetch(`${BACKEND_URI}/delete_documents`, {
        method: "DELETE",
        headers: getHeaders(idToken),
        body: JSON.stringify(request)
    });
}

export async function chatApi(request: ChatAppRequest, idToken: string | undefined): Promise<Response> {
    return await fetch(`${BACKEND_URI}/chat`, {
        method: "POST",
        headers: getHeaders(idToken),
        body: JSON.stringify(request)
    });
}

export function getCitationFilePath(citation: string): string {
    return `${BACKEND_URI}/content/${citation}`;
}

export function getSourceFilePath(filename: string): string {
    return `${BACKEND_URI}/content/sourcefiles/${filename}`;
}
