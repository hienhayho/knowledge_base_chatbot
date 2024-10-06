"use client";
import React, { useMemo, useState, useEffect, useRef } from "react";
import { Cpu, Book, MoreVertical, Trash2 } from "lucide-react";
import { getCookie } from "cookies-next";
import { useRouter } from "next/router";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const getRandomGradient = () => {
    const colors = ["#FCA5A5", "#FBBF24", "#34D399", "#60A5FA", "#A78BFA"];
    const color1 = colors[Math.floor(Math.random() * colors.length)];
    const color2 = colors[Math.floor(Math.random() * colors.length)];
    const angle = Math.floor(Math.random() * 360);
    return `linear-gradient(${angle}deg, ${color1}, ${color2})`;
};

const getBadgeText = (createdAt, updatedAt) => {
    const now = new Date();
    const created = new Date(createdAt);
    const updated = new Date(updatedAt);
    const daysSinceCreation = (now - created) / (1000 * 60 * 60 * 24);
    const daysSinceUpdate = (now - updated) / (1000 * 60 * 60 * 24);

    if (daysSinceCreation <= 7) {
        return "New";
    } else if (daysSinceUpdate <= 7) {
        return "Recently updated";
    }
    return null;
};

const AssistantCard = ({ assistant, onSelect, onDelete }) => {
    const [knowledgeBase, setKnowledgeBase] = useState(null);
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const menuRef = useRef(null);
    const randomGradient = useMemo(() => getRandomGradient(), []);
    const badgeText = getBadgeText(assistant.created_at, assistant.updated_at);

    useEffect(() => {
        const token = getCookie("access_token");
        if (!token) {
            window.location.href = "/login?redirect=/chat";
            return;
        }
        const fetchKnowledgeBase = async () => {
            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/kb/${assistant.knowledge_base_id}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                if (!response.ok) {
                    throw new Error("Failed to fetch knowledge base");
                }
                const data = await response.json();
                setKnowledgeBase(data);
            } catch (error) {
                console.error("Error fetching knowledge base:", error);
            }
        };

        fetchKnowledgeBase();
    }, [assistant.knowledge_base_id]);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setIsMenuOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [menuRef]);

    const handleMenuToggle = (e) => {
        e.stopPropagation();
        setIsMenuOpen(!isMenuOpen);
    };

    const handleDelete = (e) => {
        e.stopPropagation();
        setIsMenuOpen(false);
        if (window.confirm("Are you sure you want to delete this assistant?")) {
            onDelete(assistant.id);
        }
    };

    return (
        <div
            className="bg-white shadow-lg rounded-2xl overflow-hidden cursor-pointer hover:shadow-xl transition-shadow relative"
            onClick={() => onSelect(assistant)}
        >
            <div className="relative">
                <div
                    className="w-full h-32 rounded-t-2xl"
                    style={{ background: randomGradient }}
                ></div>
                {badgeText && (
                    <div className="absolute top-2 right-2 bg-indigo-500 text-white px-2 py-1 rounded-full text-sm font-semibold">
                        {badgeText}
                    </div>
                )}
            </div>
            <div className="p-4">
                <div className="font-bold text-xl mb-2 text-gray-800 truncate">
                    {assistant.name}
                </div>
                <p className="text-gray-600 text-sm h-12 overflow-hidden">
                    {assistant.description}
                </p>
            </div>
            <div className="px-4 pt-2 pb-4">
                <span className="inline-block bg-gray-200 rounded-full px-3 py-1 text-sm font-semibold text-gray-700 mr-2 mb-2">
                    <Cpu size={16} className="inline mr-1" />
                    {assistant.configuration.model}
                </span>
                <div className="flex items-center text-gray-700 text-sm mt-2">
                    <Book size={16} className="mr-2" />
                    <span className="truncate">
                        KB: {knowledgeBase ? knowledgeBase.name : "Loading..."}
                    </span>
                </div>
            </div>
            <div className="absolute bottom-2 right-2" ref={menuRef}>
                <button
                    onClick={handleMenuToggle}
                    className="p-1 rounded-full hover:bg-gray-200 transition-colors"
                >
                    <MoreVertical size={20} />
                </button>
                {isMenuOpen && (
                    <div className="absolute bottom-8 right-0 bg-white shadow-lg rounded-lg py-2 w-32">
                        <button
                            onClick={handleDelete}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center text-red-600"
                        >
                            <Trash2 size={16} className="mr-2" />
                            Delete
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

const AssistantCards = ({ assistants, onSelect, onDelete }) => {
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {assistants.map((assistant) => (
                <AssistantCard
                    key={assistant.id}
                    assistant={assistant}
                    onSelect={onSelect}
                    onDelete={onDelete}
                />
            ))}
        </div>
    );
};

export default AssistantCards;
