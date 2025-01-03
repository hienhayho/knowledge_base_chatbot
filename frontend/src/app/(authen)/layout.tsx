import { Metadata } from "next";
import { Montserrat } from "next/font/google";
import { AuthProvider } from "@/hooks/auth";

const font = Montserrat({ subsets: ["latin"] });

export const metadata: Metadata = {
    title: "Authentication - Knowledge Base Chatbot",
};

export default function AuthenLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="h-full">
            <body className={`${font.className} flex flex-col h-full`}>
                <AuthProvider>
                    <div className="flex-grow">{children}</div>
                </AuthProvider>
            </body>
        </html>
    );
}
