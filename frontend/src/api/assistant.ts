import { assistantEndpoints } from "@/endpoints";
import { IAssistant } from "@/types";

export const fetchAssistants = async (): Promise<IAssistant[]> => {
    const response = await fetch(assistantEndpoints.fetchAssistants, {
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch assistants");
    }
    return data;
};

export const fetchAssistant = async (
    assistantId: string
): Promise<IAssistant> => {
    const response = await fetch(
        assistantEndpoints.fetchAssistant(assistantId),
        {
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
        }
    );
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch assistant");
    }

    return data;
};

export const deleteAssistant = async (assistantId: string) => {
    const response = await fetch(
        assistantEndpoints.deleteAssistant(assistantId),
        {
            method: "DELETE",
            credentials: "include",
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to delete assistant");
    }

    return data;
};

export const fetchAssistantConversations = async (assistantId: string) => {
    const response = await fetch(
        assistantEndpoints.fetchAssistantConversations(assistantId),
        {
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.detail || "Failed to fetch assistant conversations"
        );
    }

    return data;
};

export const createConversation = async (assistantId: string) => {
    const response = await fetch(
        assistantEndpoints.createConversation(assistantId),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
        }
    );

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to create conversation");
    }

    return data;
};

export const exportFileConversations = async (assistantId: string) => {
    const response = await fetch(
        assistantEndpoints.exportConversations(assistantId),
        {
            credentials: "include",
        }
    );
    if (!response.ok) {
        throw new Error("Failed to export conversations");
    }
    const blob = await response.blob();

    return blob;
};
