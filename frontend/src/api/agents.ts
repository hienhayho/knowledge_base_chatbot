import { agentEndpoints } from "@/endpoints";

export const fetchAllAgentChoices = async () => {
    const response = await fetch(agentEndpoints.fetchAllExistAgent, {
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch agents");
    }

    return data;
};
