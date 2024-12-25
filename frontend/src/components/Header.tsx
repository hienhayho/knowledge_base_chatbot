"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { setCookie } from "cookies-next";
import { message } from "antd";
import { Button } from "antd";
import { useRouter } from "next/navigation";
import { INavItem } from "@/types";

const Header = ({
    icon,
    headerContent,
    navItems,
    homePath,
}: {
    icon: React.ReactNode;
    headerContent: string;
    navItems: INavItem[];
    homePath: string;
}) => {
    const [messageApi, contextHolder] = message.useMessage();
    const router = useRouter();
    const pathname = usePathname();

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
        return pathname == path;
    };

    const handleLogout = async () => {
        try {
            setCookie("CHATBOT_SSO", "", { expires: new Date(0) });
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
                    <div
                        className="flex items-center space-x-4 hover:cursor-pointer"
                        onClick={() => router.push(homePath)}
                    >
                        {icon}
                        <span className="font-bold text-xl">
                            {headerContent}
                        </span>
                    </div>
                    <nav className="flex space-x-4">
                        {navItems.map((item) => (
                            <Link
                                key={item.path}
                                href={item.path}
                                className={`px-3 py-2 relative font-semibold text-sm md:text-lg ${
                                    isActive(item.path)
                                        ? "text-blue-500 font-bold after:content-[''] after:absolute after:bottom-0 after:left-0 after:w-full after:h-[2px] after:bg-blue-500"
                                        : "text-gray-600 hover:bg-blue-500 hover:text-white hover:after:content-[''] hover:after:absolute hover:after:bottom-0 hover:after:left-0 hover:after:w-full hover:after:h-[2px] hover:after:bg-white hover:rounded-lg transition-all duration-300"
                                }`}
                            >
                                {item.name}
                            </Link>
                        ))}
                    </nav>
                    <div className="flex items-center space-x-5">
                        <Button
                            className="ml-auto border-3 text-red-500 shadow-md border-red-300"
                            onClick={handleLogout}
                        >
                            Đăng xuất
                        </Button>
                    </div>
                </div>
            </header>
        </>
    );
};

export default Header;
