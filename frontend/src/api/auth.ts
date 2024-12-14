import { authEndpoints } from "@/endpoints";
import { IUser, SignUpFormValues } from "@/types";

export const login = async (body: URLSearchParams) => {
    const response = await fetch(authEndpoints.login, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body: body.toString(),
    });

    const data = await response.json();

    if (!response.ok) {
        console.debug("Login failed: ", data.detail || "Something wrong !");
        throw new Error(data.detail || "Something wrong !");
    }

    return data;
};

export const register = async (body: SignUpFormValues) => {
    const result = await fetch(authEndpoints.register, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify(body),
    });

    const data = await result.json();

    return {
        success: result.ok,
        data: {
            username: data.username,
        },
        detail: data?.detail || "Done",
    };
};

export const me = async (token: string) => {
    const response = await fetch(authEndpoints.me, {
        method: "GET",
        headers: {
            "Content-type": "application/json",
            Authorization: `Bearer ${token}`,
        },
    });

    const data = await response.json();

    if (!response.ok) {
        console.error("Get user failed: ", data.detail || "Something wrong");
        throw new Error(data.detail || "Something wrong");
    }

    const user: IUser = {
        id: data.id,
        username: data.username,
        role: data.role,
        createdAt: data.created_at,
        updatedAt: data.updated_at,
    };

    return user;
};
