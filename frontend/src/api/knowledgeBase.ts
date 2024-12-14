import { knowledgeBaseEndpoints } from "@/endpoints";
import { ICreateKnowledgeBase } from "@/types";
import { getCookie } from "cookies-next";

export const fetchKnowledgeBases = async () => {
    const token = getCookie("access_token");
    const response = await fetch(knowledgeBaseEndpoints.fetchKnowledgeBases, {
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data?.detail || "Failed to fetch knowledge bases");
    }

    return data;
};

export const createKnowledgeBase = async (body: ICreateKnowledgeBase) => {
    const token = getCookie("access_token");
    const response = await fetch(knowledgeBaseEndpoints.createKnowledgeBase, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
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
