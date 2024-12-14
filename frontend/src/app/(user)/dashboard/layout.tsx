import { Inter } from "next/font/google";
import "@/styles/globals.css";
import { AuthProvider } from "@/hooks/auth";
import { UserRound } from "lucide-react";
import { dashboardNavItems } from "@/constants";
import Header from "@/components/Header";

const inter = Inter({ subsets: ["latin"] });

export default function UserLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="h-full">
            <body className={`${inter.className} flex flex-col h-full`}>
                <Header
                    headerContent="User"
                    navItems={dashboardNavItems}
                    icon={<UserRound size={32} />}
                />
                <AuthProvider>
                    <div className="flex-grow">{children}</div>
                </AuthProvider>
            </body>
        </html>
    );
}
