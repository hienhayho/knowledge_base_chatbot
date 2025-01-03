import { adminEndpoints } from "@/endpoints";
import { IAdminSwitchUserResponse, IApiResponse } from "@/types";

export const getUsers = async () => {
    const respone = await fetch(adminEndpoints.fetchUsers, {
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
    });

    const data = await respone.json();

    if (!respone.ok) {
        throw new Error(data.detail || "Failed to fetch users");
    }

    return data;
};

export const updateUser = async (userId: string, organization: string) => {
    const response = await fetch(adminEndpoints.editUser(userId), {
        method: "PUT",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
            organization,
        }),
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.detail || "Failed to update user");
    }

    return data;
};

export const fetchTokens = async () => {
    const respose = await fetch(adminEndpoints.fetchTokens, {
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
    });

    const data = await respose.json();

    if (!respose.ok) {
        throw new Error(data.detail || "Failed to fetch tokens");
    }

    return data;
};

export const deleteToken = async (id: string) => {
    const response = await fetch(adminEndpoints.deleteToken(id), {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
    });

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to delete token");
    }

    return data;
};

export const createToken = async (username: string) => {
    const result = await fetch(adminEndpoints.createToken, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({
            username,
        }),
    });

    const data = await result.json();

    if (!result.ok) {
        throw new Error(data.detail || "Failed to create token");
    }

    return data;
};

export const switchUser = async (username: string) => {
    const response = await fetch(adminEndpoints.switchUser, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
        body: JSON.stringify({ username_to_switch: username }),
    });

    const data: IApiResponse<IAdminSwitchUserResponse> = await response.json();

    if (!response.ok) {
        console.debug(
            "Admin switchUser failed: ",
            (data as { detail: string })?.detail || "Something wrong happened!"
        );
        throw new Error(
            (data as { detail: string })?.detail || "Something wrong happened!"
        );
    }

    return data;
};

export const deleteUser = async (id: string) => {
    const response = await fetch(adminEndpoints.deleteUser(id), {
        method: "DELETE",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "include",
    });

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || "Failed to delete user");
    }

    return data;
};
