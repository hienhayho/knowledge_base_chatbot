"use client";
import React, { useMemo, useState, useEffect, useRef } from "react";
import {
    Cpu,
    Book,
    MoreVertical,
    Trash2,
    // LoaderCircle,
    Download,
    IdCard,
} from "lucide-react";
import { useRouter } from "next/navigation";
import { IAssistant, IKnowledgeBase } from "@/types";
import AddToolsModal from "./AddToolsModal";
import { Settings } from "lucide-react";
import { Button, Popover, Tooltip, message } from "antd";

const API_BASE_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

const getRandomGradient = () => {
    const colors = ["#FCA5A5", "#FBBF24", "#34D399", "#60A5FA", "#A78BFA"];
    const color1 = colors[Math.floor(Math.random() * colors.length)];
    const color2 = colors[Math.floor(Math.random() * colors.length)];
    const angle = Math.floor(Math.random() * 360);
    return `linear-gradient(${angle}deg, ${color1}, ${color2})`;
};

const getBadgeText = (createdAt: string, updatedAt: string) => {
    const now = new Date();
    const created = new Date(createdAt);
    const updated = new Date(updatedAt);
    if (isNaN(created.getTime()) || isNaN(updated.getTime())) {
        throw new Error("Invalid date provided");
    }

    const daysSinceCreation =
        (now.getTime() - created.getTime()) / (1000 * 60 * 60 * 24);
    const daysSinceUpdate =
        (now.getTime() - updated.getTime()) / (1000 * 60 * 60 * 24);

    if (daysSinceCreation <= 7) {
        return "New";
    } else if (daysSinceUpdate <= 7) {
        return "Recently updated";
    }
    return null;
};

const AssistantCard = ({
    token,
    assistant,
    onSelect,
    onDelete,
}: {
    token: string;
    assistant: IAssistant;
    onSelect: (assistant: IAssistant) => void;
    onDelete: (assistantId: string) => void;
}) => {
    const router = useRouter();
    const menuRef = useRef<HTMLDivElement>(null);
    const [knowledgeBase, setKnowledgeBase] = useState<IKnowledgeBase | null>(
        null
    );
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [messageApi, contextHolder] = message.useMessage();
    // const [cost, setCost] = useState<number | null>(null);
    const randomGradient = useMemo(() => getRandomGradient(), []);
    const redirectUrl = encodeURIComponent("/chat");
    const badgeText = getBadgeText(assistant.created_at, assistant.updated_at);

    useEffect(() => {
        if (!token) {
            router.push(`/login?redirect=${redirectUrl}`);
            return;
        }
        const fetchKnowledgeBase = async () => {
            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/kb/get_kb/${assistant.knowledge_base_id}`,
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
        if (!token) {
            router.push(`/login?redirect=${redirectUrl}`);
            return;
        }
        const handleClickOutside = (event: MouseEvent) => {
            if (
                menuRef.current &&
                !menuRef.current.contains(event.target as Node)
            ) {
                setIsMenuOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, [menuRef]);

    const handleMenuToggle = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsMenuOpen(!isMenuOpen);
    };

    const handleDelete = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsMenuOpen(false);
        if (window.confirm("Are you sure you want to delete this assistant?")) {
            onDelete(assistant.id);
        }
    };

    // const handleGetTotalCost = async (e: React.MouseEvent) => {
    //     e.stopPropagation();
    //     if (isLoading) return;

    //     setIsLoading(true);
    //     try {
    //         const response = await fetch(
    //             `${API_BASE_URL}/api/assistant/${assistant.id}/total_cost`,
    //             {
    //                 headers: {
    //                     Authorization: `Bearer ${token}`,
    //                 },
    //             }
    //         );
    //         if (!response.ok) {
    //             throw new Error("Failed to fetch total cost");
    //         }
    //         const data = await response.json();
    //         setCost(data.total_cost);
    //     } catch (error) {
    //         console.error("Error fetching total cost:", error);
    //     } finally {
    //         setIsLoading(false);
    //     }
    // };

    const handleExportConversations = async (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsMenuOpen(false);
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/assistant/${assistant.id}/export_conversations`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            if (!response.ok) {
                throw new Error("Failed to export conversations");
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `assistant_${assistant.id}.xlsx`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Error exporting conversations:", error);
        }
    };

    return (
        <div
            className="bg-white shadow-lg rounded-2xl overflow-hidden cursor-pointer hover:shadow-xl transition-shadow relative"
            onClick={() => onSelect(assistant)}
        >
            {contextHolder}
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
            <div className="p-4 flex justify-around items-center border gap-4">
                <div className="border-2 p-3 rounded-lg border-green-200 w-full h-full">
                    <Tooltip title="Tên trợ lý">
                        <h3 className="font-semibold text-lg text-gray-800 truncate">
                            {assistant.name}
                        </h3>
                    </Tooltip>
                    <Tooltip title="Mô tả về trợ lý">
                        <p className="text-gray-600 text-sm mt-1 truncate">
                            {assistant.description}
                        </p>
                    </Tooltip>
                </div>
                <div className="flex items-center flex-col text-gray-700 text-sm mt-2 gap-4">
                    <Popover
                        content={<div>{"Sao chép AssistantID"}</div>}
                        className=""
                    >
                        <Button
                            className="w-full border-gray-500"
                            onClick={(e) => {
                                e.stopPropagation();
                                navigator.clipboard.writeText(assistant.id);
                                messageApi.success({
                                    content: "Copied AssistantID",
                                    duration: 1,
                                });
                            }}
                            icon={<IdCard size={16} />}
                        >
                            <span className="font-medium">{"AssistantID"}</span>
                        </Button>
                    </Popover>

                    <div>
                        <AddToolsModal
                            token={token}
                            icon={<Settings size={16} />}
                            buttonTitle="Chỉnh tools"
                            modalTitle={`Chọn tools cho trợ lý: ${assistant.name}`}
                            assistantId={assistant.id}
                        />
                    </div>
                </div>
            </div>
            <div className="px-4 pt-2 pb-4">
                <span className="inline-block bg-gray-200 rounded-full px-3 py-1 text-sm font-semibold text-gray-700 mr-2 mb-2">
                    <Cpu size={16} className="inline mr-1" />
                    {assistant.configuration
                        ? assistant.configuration.model
                        : "No Info..."}
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
                    <div className="flex flex-col justify-center">
                        <div className="absolute bottom-20 right-0 bg-white shadow-lg rounded-lg py-2 w-32">
                            <button
                                onClick={handleExportConversations}
                                className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center text-green-600"
                            >
                                <Download size={16} className="mr-2" />
                                Export
                            </button>
                        </div>
                        <div className="absolute bottom-8 right-0 bg-white shadow-lg rounded-lg py-2 w-32">
                            <button
                                onClick={handleDelete}
                                className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center text-red-600"
                            >
                                <Trash2 size={16} className="mr-2" />
                                Delete
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

const AssistantCards = ({
    token,
    assistants,
    onSelect,
    onDelete,
}: {
    token: string;
    assistants: IAssistant[];
    onSelect: (assistant: IAssistant) => void;
    onDelete: (assistantId: string) => void;
}) => {
    return (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {assistants.map((assistant) => (
                <AssistantCard
                    token={token}
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
