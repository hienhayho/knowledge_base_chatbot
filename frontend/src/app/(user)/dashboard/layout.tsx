import { Inter } from "next/font/google";
import Header from "@/components/dashboard/Header";
import "@/styles/globals.css";
import { AuthProvider } from "@/hooks/auth";

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
