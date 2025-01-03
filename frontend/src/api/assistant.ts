import { assistantEndpoints } from "@/endpoints";
import { IAssistant, ICreateAssistant } from "@/types";

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

export const fetchAssistant = async (assistantId: string) => {
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

export const createAssistant = async (payload: ICreateAssistant) => {
    const response = await fetch(assistantEndpoints.createAssistant, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to create assistant");
    }

    return data;
};

export const updateAssistant = async (
    assistantId: string,
    instructPrompt: string,
    agentBackstory: string,
    agentType: string
) => {
    const response = await fetch(
        assistantEndpoints.updateAssistant(assistantId),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
            body: JSON.stringify({
                instruct_prompt: instructPrompt,
                agent_backstory: agentBackstory,
                agent_type: agentType,
            }),
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to update assistant");
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

export const fetchConversationHistory = async (
    assistantId: string,
    conversationId: string
) => {
    const response = await fetch(
        assistantEndpoints.fetchConversationHistory(
            assistantId,
            conversationId
        ),
        {
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch conversation history");
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

export const renameConversation = async (
    assistantId: string,
    conversationId: string,
    name: string
) => {
    const response = await fetch(
        assistantEndpoints.renameConversation(assistantId, conversationId),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
            body: JSON.stringify({ name }),
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to rename conversation");
    }

    return data;
};

export const deleteConversation = async (
    assistantId: string,
    conversationId: string
) => {
    const response = await fetch(
        assistantEndpoints.deleteConversation(assistantId, conversationId),
        {
            method: "DELETE",
            credentials: "include",
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to delete conversation");
    }

    return data;
};

export const exportConversation = async (
    assistantId: string,
    conversationId: string
) => {
    const response = await fetch(
        assistantEndpoints.exportConversation(assistantId, conversationId),
        {
            credentials: "include",
        }
    );

    if (!response.ok) {
        throw new Error("Failed to export conversation");
    }

    const blob = await response.blob();

    return blob;
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

export const updateTools = async (
    assistantId?: string,
    updatedTools?: {
        name: string;
        description: string;
        return_as_answer: boolean;
    }[]
) => {
    const response = await fetch(assistantEndpoints.updateTools(assistantId), {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
            tools: updatedTools,
        }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to update tools");
    }

    return data;
};

export const sendMessage = async (
    assistantId: string,
    conversationId: string,
    message: string
) => {
    const response = await fetch(
        assistantEndpoints.sendMessage(assistantId, conversationId),
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            credentials: "include",
            body: JSON.stringify({ content: message }),
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to send message");
    }

    return data;
};
