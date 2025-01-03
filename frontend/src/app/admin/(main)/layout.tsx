import { Montserrat } from "next/font/google";
import Header from "@/components/Header";
import "@/styles/globals.css";
import { Settings } from "lucide-react";
import { adminNavItems } from "@/constants";
import { AuthProvider } from "@/hooks/auth";
import { Metadata } from "next";

const font = Montserrat({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Admin - Knowledge Base Chatbot",
};

export default function UserLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="h-full">
            <body className={`${font.className} flex flex-col h-full`}>
                <AuthProvider>
                    <Header
                        headerContent="Admin"
                        navItems={adminNavItems}
                        icon={<Settings size={32} />}
                        homePath="/admin"
                    />
                    <div className="flex-grow mt-5">{children}</div>
                </AuthProvider>
            </body>
        </html>
    );
}
