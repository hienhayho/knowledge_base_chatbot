"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const Header = () => {
    const pathname = usePathname();

    const navItems = [
        { name: "Knowledge Base", path: "/knowledge" },
        { name: "Chat", path: "/chat" },
        // { name: "Graph", path: "/graph" },
        { name: "File Management", path: "/file-management" },
    ];

    const isActive = (path: string) => {
        // If the current path is just "/", it won't match any nav item
        if (pathname === "/") return false;

        // Check if the current pathname starts with the nav item's path
        return pathname.startsWith(path);
    };

    return (
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
                    <span className="font-bold text-xl">Knowledge Base</span>
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
                <div className="flex items-center space-x-4">
                    <select className="bg-gray-100 rounded-md px-2 py-1">
                        <option>English</option>
                    </select>
                </div>
            </div>
        </header>
    );
};

export default Header;
