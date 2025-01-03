import { Montserrat } from "next/font/google";
import "@/styles/globals.css";
import { AuthProvider } from "@/hooks/auth";
import { UserRound } from "lucide-react";
import { dashboardNavItems } from "@/constants";
import Header from "@/components/Header";
import { Metadata } from "next";

const font = Montserrat({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Dashboard - Knowledge Base Chatbot",
};

export default function UserLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="h-full">
            <body className={`${font.className} flex flex-col h-full`}>
                <Header
                    headerContent="User"
                    navItems={dashboardNavItems}
                    icon={<UserRound size={32} />}
                    homePath="/dashboard"
                />
                <AuthProvider>
                    <div className="flex-grow">{children}</div>
                </AuthProvider>
            </body>
        </html>
    );
}
