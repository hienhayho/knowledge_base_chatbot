import { dashboardEndpoints } from "@/endpoints";

export const fetchDashboardData = async () => {
    const response = await fetch(dashboardEndpoints.fetchDashboardData, {
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
    });
    const data = await response.json();
    if (!response.ok) {
        console.error(data?.detail || "Something wrong happened");
        return;
    }

    return data;
};

export const exportFile = async (file_name: string) => {
    const response = await fetch(dashboardEndpoints.exportFile(file_name), {
        credentials: "include",
    });

    if (!response.ok) {
        throw new Error("Failed to export file");
    }

    const blob = await response.blob();

    return blob;
};

export const fetchOptions = async (source: string) => {
    const response = await fetch(dashboardEndpoints.fetchOptions(source), {
        credentials: "include",
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to fetch options");
    }
    return data;
};
