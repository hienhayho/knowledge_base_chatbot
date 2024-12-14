import { adminEndpoints } from "@/endpoints";
import { IAdminSwitchUserResponse, IApiResponse, IUser } from "@/types";

export const getUsers = async (token: string) => {
    const response = await fetch(adminEndpoints.getUsers, {
        method: "GET",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
    });

    const data: IApiResponse<IUser[]> = await response.json();

    if (!response.ok) {
        console.debug(
            "Admin getUsers failed: ",
            (data as { detail: string })?.detail || "Something wrong happened!"
        );
        throw new Error(
            (data as { detail: string })?.detail || "Something wrong happened!"
        );
    }

    return data;
};

export const switchUser = async (token: string, username: string) => {
    const response = await fetch(adminEndpoints.switchUser, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
        },
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
