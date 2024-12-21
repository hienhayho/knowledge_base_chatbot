import { Inter } from "next/font/google";
import { AuthProvider } from "@/hooks/auth";
import "@/styles/globals.css";
import Header from "@/components/Header";
import { userNavItems } from "@/constants";
import { UserRound } from "lucide-react";
import { Metadata } from "next";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "User",
};

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
                    navItems={userNavItems}
                    icon={<UserRound size={32} />}
                    homePath="/knowledge"
                />
                <AuthProvider>
                    <div className="flex-grow">{children}</div>
                </AuthProvider>
            </body>
        </html>
    );
}
