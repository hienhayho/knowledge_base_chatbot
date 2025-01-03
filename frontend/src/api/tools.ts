import { toolsEndpoints } from "@/endpoints";

export const fetchTools = async () => {
    const response = await fetch(toolsEndpoints.fetchTools, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch tools");
    }

    return data;
};
