import { Metadata } from "next";
import { Inter } from "next/font/google";
import { AuthProvider } from "@/hooks/auth";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Authentication",
};

export default function AuthenLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="h-full">
            <body className={`${inter.className} flex flex-col h-full`}>
                <AuthProvider>
                    <div className="flex-grow">{children}</div>
                </AuthProvider>
            </body>
        </html>
    );
}
