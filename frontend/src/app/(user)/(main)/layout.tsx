import { Inter } from "next/font/google";
import Header from "@/components/Header";
import { AuthProvider } from "@/hooks/auth";
import "@/styles/globals.css";

const inter = Inter({ subsets: ["latin"] });

export default function UserLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <html lang="en" className="h-full">
            <body className={`${inter.className} flex flex-col h-full`}>
                <Header />
                <AuthProvider>
                    <div className="flex-grow">{children}</div>
                </AuthProvider>
            </body>
        </html>
    );
}
