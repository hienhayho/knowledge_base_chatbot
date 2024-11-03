"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { setCookie } from "cookies-next";
import { message } from "antd";
import { Button } from "antd";
import { useRouter } from "next/navigation";

const Header = () => {
    const [messageApi, contextHolder] = message.useMessage();
    const router = useRouter();
    const pathname = usePathname();

    const navItems = [
        { name: "Knowledge Base", path: "/knowledge" },
        { name: "Chat", path: "/chat" },
        { name: "File Management", path: "/file-management" },
    ];

    const successMessage = ({
        content,
        duration = 1,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "success",
            content,
            duration,
        });
    };

    const errorMessage = ({
        content,
        duration = 1,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "error",
            content,
            duration,
        });
    };

    const isActive = (path: string) => {
        if (pathname === "/") return false;
        return pathname.startsWith(path);
    };

    const handleLogout = async () => {
        try {
            setCookie("access_token", "", { expires: new Date(0) });
            successMessage({ content: "Logout successfully!" });
            setTimeout(() => {
                router.push("/login");
            }, 1500);
        } catch (error) {
            errorMessage({ content: "Logout failed!" });
            console.error(error);
        }
    };

    return (
        <>
            {contextHolder}
            <header className="bg-white shadow-sm h-16">
                <div className="container mx-auto px-4 h-full flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                        <svg
                            className="w-8 h-8 text-blue-500"
                            viewBox="0 0 24 24"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                        >
                            <path
                                d="M12 2L2 7L12 12L22 7L12 2Z"
                                fill="currentColor"
                            />
                            <path
                                d="M2 17L12 22L22 17"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                            <path
                                d="M2 12L12 17L22 12"
                                stroke="currentColor"
                                strokeWidth="2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            />
                        </svg>
                        <span className="font-bold text-xl">
                            Knowledge Base
                        </span>
                    </div>
                    <nav className="flex space-x-4">
                        {navItems.map((item) => (
                            <Link
                                key={item.path}
                                href={item.path}
                                className={`px-3 py-2 rounded-md ${
                                    isActive(item.path)
                                        ? "bg-blue-500 text-white"
                                        : "text-gray-600 hover:bg-gray-100"
                                }`}
                            >
                                {item.name}
                            </Link>
                        ))}
                    </nav>
                    <div className="flex items-center space-x-10">
                        <select className="block bg-gray-100 rounded-md px-2 py-1">
                            <option>English</option>
                        </select>
                        <Button
                            type="primary"
                            className="bg-red-500 ml-auto"
                            onClick={handleLogout}
                        >
                            Logout
                        </Button>
                    </div>
                </div>
            </header>
        </>
    );
};

export default Header;
