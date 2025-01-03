import { knowledgeBaseEndpoints } from "@/endpoints";
import { ICreateKnowledgeBase } from "@/types";

export const fetchKnowledgeBases = async () => {
    const response = await fetch(knowledgeBaseEndpoints.fetchKnowledgeBases, {
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
    });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data?.detail || "Failed to fetch knowledge bases");
    }

    return data;
};

export const fetchKnowledgeBase = async (id?: string) => {
    const response = await fetch(
        knowledgeBaseEndpoints.fetchKnowledgeBase(id),
        {
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
        }
    );
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch knowledge base");
    }

    return data;
};

export const inheritKnowledgeBase = async (
    source_knowledge_base_id?: string,
    target_knowledge_base_id?: string
) => {
    const response = await fetch(knowledgeBaseEndpoints.inheritKNowledgeBase, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
            source_knowledge_base_id,
            target_knowledge_base_id,
        }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to inherit knowledge base");
    }

    return data;
};

export const uploadToKnowledgeBase = async (kbId: string, body: FormData) => {
    const response = await fetch(
        knowledgeBaseEndpoints.uploadToKnowledgeBase(kbId),
        {
            method: "POST",
            body: body,
            credentials: "include",
        }
    );

    const result = await response.json();

    if (!response.ok) {
        throw new Error(result.detail || "Failed to upload file");
    }

    return result;
};

export const getDocumentStatus = async (documentId: string) => {
    const response = await fetch(
        knowledgeBaseEndpoints.getDocumentStatus(documentId),
        {
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to get document status");
    }

    return data;
};

export const downloadDocument = async (documentId: string) => {
    const response = await fetch(
        knowledgeBaseEndpoints.downloadDocument(documentId),
        {
            credentials: "include",
        }
    );
    if (!response.ok) {
        throw new Error("Failed to download document");
    }

    const blob = await response.blob();

    return blob;
};

export const deleteDocument = async (
    documentId: string,
    delete_to_retry: boolean
) => {
    const response = await fetch(
        knowledgeBaseEndpoints.deleteDocument(documentId),
        {
            method: "DELETE",
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
            body: JSON.stringify({ delete_to_retry: delete_to_retry }),
        }
    );
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to delete document");
    }

    return data;
};

export const processDocument = async (documentId: string) => {
    const response = await fetch(
        knowledgeBaseEndpoints.processDocument(documentId),
        {
            method: "POST",
            credentials: "include",
        }
    );

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to process document");
    }

    return data;
};

export const stopProcessingDocument = async (documentId: string) => {
    const response = await fetch(
        knowledgeBaseEndpoints.stopProcessingDocument(documentId),
        {
            method: "POST",
            credentials: "include",
        }
    );

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to stop processing document");
    }

    return data;
};

export const createKnowledgeBase = async (body: ICreateKnowledgeBase) => {
    const response = await fetch(knowledgeBaseEndpoints.createKnowledgeBase, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(body),
    });

    const newKnowledgeBase = await response.json();
    if (!response.ok) {
        throw new Error(
            newKnowledgeBase?.detail || "Failed to create knowledge base"
        );
    }

    return newKnowledgeBase;
};

export const deleteKnowledgeBase = async (id: string) => {
    const response = await fetch(
        knowledgeBaseEndpoints.deleteKnowledgeBase(id),
        {
            method: "DELETE",
            credentials: "include",
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to delete knowledge base");
    }

    return data;
};
