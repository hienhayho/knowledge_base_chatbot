"use client";
import React, { useState, useRef, useEffect } from "react";
import { FileText, MoreVertical, Trash2 } from "lucide-react";

const KnowledgeBaseCard = ({
    title,
    description,
    docCount,
    lastUpdated,
    onClick,
    onDelete,
}: {
    title: string;
    description: string;
    docCount: number;
    lastUpdated: string;
    onClick: () => void;
    onDelete: () => void;
}) => {
    const menuRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const [isMenuOpen, setIsMenuOpen] = useState(false);

    const handleMenuToggle = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsMenuOpen(!isMenuOpen);
    };

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                menuRef.current &&
                !menuRef.current.contains(event.target as Node) &&
                buttonRef.current &&
                !buttonRef.current.contains(event.target as Node)
            ) {
                setIsMenuOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    return (
        <div
            className="bg-white rounded-lg shadow-md p-4 sm:p-6 hover:shadow-lg transition-shadow duration-300 w-full h-full relative"
            onClick={onClick}
        >
            <div className="flex justify-start items-start mb-4">
                <div className="w-10 h-10 sm:w-12 sm:h-12 bg-blue-100 rounded-full flex items-center justify-center">
                    <FileText className="w-5 h-5 sm:w-6 sm:h-6 text-blue-500" />
                </div>
            </div>
            <h2 className="text-lg sm:text-xl font-semibold mb-2 sm:mb-3 text-gray-800">
                {title}
            </h2>
            <p className="text-gray-600 mb-4 text-sm sm:text-base line-clamp-2">
                {description}
            </p>
            <div className="flex items-center text-sm text-gray-500 mb-2">
                <FileText className="w-4 h-4 mr-2" />
                {docCount} {docCount === 1 ? "Document" : "Documents"}
            </div>
            <div className="text-sm text-gray-500">
                Last updated: {lastUpdated}
            </div>

            <div className="absolute bottom-4 right-4">
                <div className="relative">
                    <button
                        ref={buttonRef}
                        className="text-gray-400 hover:text-gray-600"
                        onClick={handleMenuToggle}
                    >
                        <MoreVertical className="w-5 h-5" />
                    </button>

                    <div
                        ref={menuRef}
                        className={`absolute top-8 right-0 bg-white shadow-lg rounded-lg py-2 w-32 transform transition-all duration-200 ease-out ${
                            isMenuOpen
                                ? "opacity-100 scale-100"
                                : "opacity-0 scale-95 pointer-events-none"
                        }`}
                    >
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                onDelete();
                            }}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center text-red-600"
                        >
                            <Trash2 size={16} className="mr-2" />
                            Delete
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default KnowledgeBaseCard;
