import { useAuth } from "@/hooks/auth";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, ComponentType } from "react";
import LoadingSpinner from "./LoadingSpinner";

export default function ProtectedRoute<P extends object>(
    WrappedComponent: ComponentType<P>
) {
    return function WithProtectedRoute(props: P) {
        const { isAuthenticated, loading, user } = useAuth();
        const router = useRouter();
        const pathname = usePathname();

        useEffect(() => {
            if (user) {
                if (pathname.startsWith("/admin") && user.role !== "admin") {
                    router.push("/");
                }
            }
            if (!loading) {
                if (!isAuthenticated && pathname !== "/login") {
                    router.push("/login");
                } else if (isAuthenticated && pathname === "/login") {
                    router.push("/");
                }
            }
        }, [loading, isAuthenticated, router, pathname, user]);

        if (loading) {
            return <LoadingSpinner />;
        }

        return <WrappedComponent {...props} />;
    };
}