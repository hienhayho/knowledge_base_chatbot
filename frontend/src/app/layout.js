import { Inter } from "next/font/google";
import Header from "@/components/Header";
import "@/styles/globals.css";

const inter = Inter({ subsets: ["latin"] });

export default function RootLayout({ children }) {
    return (
        <html lang="en" className="h-full">
            <body className={`${inter.className} flex flex-col h-full`}>
                <Header />
                <div className="flex-grow">{children}</div>
            </body>
        </html>
    );
}
