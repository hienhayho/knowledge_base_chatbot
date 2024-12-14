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
    changeUser: (user: IUser | null, token: string) => void;
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
            try {
                const user_access_token = getCookie("access_token") as string;
                if (!user_access_token) {
                    setUser(null);
                    setIsAuthenticated(false);
                    setIsLoggedOut(true);
                    return;
                }
                // Optionally, call an endpoint to verify the token's validity
                const userData = await authApi.me(user_access_token);
                setUser(userData);
                setToken(user_access_token);
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
    }, [router, pathname, token]);

    useEffect(() => {
        if (
            isLoggedOut &&
            pathname !== "/login" &&
            pathname !== "/register" &&
            pathname !== "/admin/register"
        ) {
            router.push(`/login?redirect=${redirectURL}`);
            setIsLoggedOut(true);
        }
    }, [isLoggedOut, pathname, router, redirectURL]);

    const changeUser = (user: IUser | null, token: string) => {
        setUser(user);
        setToken(token);
        setIsAuthenticated(!!user);
        setIsLoggedOut(false);
    };

    useEffect(() => {
        async function loadUserFromToken() {
            try {
                const user_access_token = getCookie("access_token") as string;

                if (!user_access_token) {
                    setIsAuthenticated(false);
                    setUser(null);
                    setIsLoggedOut(true);
                    setLoading(false);
                    return;
                }

                const userData = await authApi.me(user_access_token);

                setToken(user_access_token);
                setUser(userData);
                setIsAuthenticated(true);
                setIsLoggedOut(false);
            } catch (error) {
                console.error("Failed to verify token:", error);
                setIsAuthenticated(false);
                setUser(null);
                setToken("");
                setIsLoggedOut(true);
            }
            setLoading(false);
        }
        loadUserFromToken();
    }, [token]);

    const login = async (body: URLSearchParams) => {
        try {
            const data = await authApi.login(body);

            setCookie("access_token", data.access_token, {
                maxAge: 30 * 60,
                path: "/",
            });

            const userData = await authApi.me(data.access_token);

            setUser(userData);
            setToken(data.access_token);
            setIsAuthenticated(true);
            setLoading(false);
            setIsLoggedOut(false);

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
                changeUser,
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
