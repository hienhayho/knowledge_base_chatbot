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
