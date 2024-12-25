"use client";
import { authApi } from "@/api";
import { IUser, SignUpFormValues, SignUpResponse } from "@/types";
import { setCookie } from "cookies-next";
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
    login: (body: URLSearchParams) => Promise<IUser>;
    logout: () => void;
    register: (body: SignUpFormValues) => Promise<{
        success: boolean;
        data: SignUpResponse | null;
        detail?: string;
    }>;
    loading: boolean;
    isAuthenticated: boolean;
    changeUser: (user: IUser | null) => void;
}

export const AuthContext = createContext<AuthContextType | null>(null);

// Verify token interval in minutes - default 30 minutes
const VERIFY_INTERVAL_MINUTES = parseInt(
    process.env.NEXT_PUBLIC_VERIFY_INTERVAL_MINUTES || "30"
);

interface AuthProviderProps {
    children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
    const [user, setUser] = useState<IUser | null>(null);
    const [loading, setLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [isLoggedOut, setIsLoggedOut] = useState(false);
    const router = useRouter();
    const pathname = usePathname();
    const redirectURL = encodeURIComponent(pathname);

    useEffect(() => {
        const verify = async () => {
            try {
                const userData = await authApi.me();
                setUser(userData);
                setIsAuthenticated(true);
            } catch (error) {
                console.error("Failed to verify token:", error);
                setUser(null);
                setIsAuthenticated(false);
                setIsLoggedOut(true);
            }
        };

        const intervalId = setInterval(() => {
            verify();
        }, VERIFY_INTERVAL_MINUTES * 60 * 1000);

        return () => {
            clearInterval(intervalId);
        };
    }, [router, pathname]);

    useEffect(() => {
        if (
            isLoggedOut &&
            pathname !== "/login" &&
            pathname !== "/register" &&
            pathname !== "/admin/register"
        ) {
            console.log("pathname", pathname);
            router.push(`/login?redirect=${redirectURL}`);
            setIsLoggedOut(true);
        }
    }, [isLoggedOut, pathname, router, redirectURL]);

    const changeUser = (user: IUser | null) => {
        setUser(user);
        setIsAuthenticated(!!user);
        setIsLoggedOut(false);
    };

    useEffect(() => {
        async function loadUser() {
            try {
                const userData = await authApi.me();

                setUser(userData);
                setIsAuthenticated(true);
                setIsLoggedOut(false);
            } catch (error) {
                console.error("Failed to verify token:", error);
                setIsAuthenticated(false);
                setUser(null);
                setIsLoggedOut(true);
            }
            setLoading(false);
        }
        loadUser();
    }, [isAuthenticated]);

    const login = async (body: URLSearchParams) => {
        try {
            const data = await authApi.login(body);

            setCookie("CHATBOT_SSO", data.access_token, {
                expires: new Date(data.expires),
                path: "/",
            });

            const userData = await authApi.me();

            setUser(userData);
            setIsAuthenticated(true);
            setLoading(false);
            setIsLoggedOut(false);

            return userData;
        } catch (err) {
            console.error("Error in login: ", err);
            throw new Error(
                (err as Error).message || "Something wrong happened !!!"
            );
        }
    };

    const logout = () => {
        setUser(null);
        setIsAuthenticated(false);
        setIsLoggedOut(true);
        setCookie("CHATBOT_SSO", "", { maxAge: -1, path: "/" });
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
