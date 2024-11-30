"use client";
import { authApi } from "@/api";
import { IUser, SignUpFormValues, SignUpResponse } from "@/types";
import { getCookie, setCookie } from "cookies-next";
import { usePathname, useRouter } from "next/navigation";
import {
    useState,
    useEffect,
    useContext,
    createContext,
    ReactNode,
} from "react";

interface AuthContextType {
    user: IUser | null;
    token: string;
    login: (body: URLSearchParams) => Promise<{
        access_token: string;
        type?: string;
    }>;
    logout: () => void;
    register: (body: SignUpFormValues) => Promise<{
        success: boolean;
        data: SignUpResponse | null;
        detail?: string;
    }>;
    loading: boolean;
    isAuthenticated: boolean;
}

export const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
    const [user, setUser] = useState<IUser | null>(null);
    const [loading, setLoading] = useState(true);
    const [token, setToken] = useState("");
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoggedOut, setIsLoggedOut] = useState(false);
    const router = useRouter();
    const pathname = usePathname();
    const redirectURL = encodeURIComponent(pathname);

    useEffect(() => {
        const verifyToken = async () => {
            console.log("run");
            try {
                const user_access_token = getCookie("access_token");
                if (!user_access_token) {
                    throw new Error("Token not found");
                }

                // Optionally, call an endpoint to verify the token's validity
                const userData = await authApi.me();
                setUser(userData);
                setToken(user_access_token as string);
                setIsAuthenticated(true);
            } catch (error) {
                console.error("Token verification failed:", error);
                setUser(null);
                setToken("");
                setIsAuthenticated(false);
                setIsLoggedOut(true);
            }
        };

        const intervalId = setInterval(() => {
            verifyToken();
        }, 30000);

        return () => {
            clearInterval(intervalId);
        };
    }, [router, pathname]);

    useEffect(() => {
        if (isLoggedOut && pathname !== "/login") {
            router.push(`/login?redirect=${redirectURL}`);
            setIsLoggedOut(false);
        }
    }, [isLoggedOut, pathname, router, redirectURL]);

    useEffect(() => {
        async function loadUserFromToken() {
            try {
                const user_access_token = getCookie("access_token");
                const userData = await authApi.me();
                setToken(user_access_token || "");
                setUser(userData);
                setIsAuthenticated(true);
            } catch (error) {
                console.error("Failed to verify token:", error);
                setIsAuthenticated(false);
            }
            setLoading(false);
        }
        loadUserFromToken();
    }, []);

    const login = async (body: URLSearchParams) => {
        try {
            const data = await authApi.login(body);

            setCookie("access_token", data.access_token, {
                maxAge: 30 * 60,
                path: "/",
            });

            const userData = await authApi.me();

            setUser(userData);
            setToken(data.access_token);
            setIsAuthenticated(true);

            return data;
        } catch (err) {
            console.error("Error in login: ", err);
            throw new Error("Something wrong happened");
        }
    };

    const logout = () => {
        setUser(null);
        setToken("");
        setIsAuthenticated(false);
        setIsLoggedOut(true);
        setCookie("access_token", "", { maxAge: -1, path: "/" });
    };

    const register = async (body: SignUpFormValues) => {
        try {
            const result = await authApi.register(body);
            return result;
        } catch (err) {
            console.error(
                "Register failed: ",
                err || "Something wrong happened !!!"
            );
            return {
                success: false,
                data: null,
            };
        }
    };

    return (
        <AuthContext.Provider
            value={{
                user,
                token,
                login,
                logout,
                register,
                loading,
                isAuthenticated,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = (): AuthContextType => {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within an AuthProvider");
    }
    return context;
};
