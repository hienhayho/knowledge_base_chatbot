"use client";
import React, { useState, useRef, useEffect } from "react";
import { FileText, MoreVertical, Trash2, Combine } from "lucide-react";
import { Modal, Select, message } from "antd";
import { getCookie } from "cookies-next";

interface IMergeableKnowledgeBase {
    id: string;
    name: string;
}

interface IMergeableKnowledgeBaseResponse {
    inheritable_knowledge_bases: IMergeableKnowledgeBase[];
    parents: string[];
    children: string[];
    detail?: string;
}

const KnowledgeBaseCard = ({
    title,
    kb_id,
    description,
    docCount,
    lastUpdated,
    onClick,
    onDelete,
}: {
    title: string;
    kb_id: string;
    description: string;
    docCount: number;
    lastUpdated: string;
    onClick: () => void;
    onDelete: () => void;
}) => {
    const token = getCookie("access_token");
    const [messageApi, contextHolder] = message.useMessage();
    const menuRef = useRef<HTMLDivElement>(null);
    const buttonRef = useRef<HTMLButtonElement>(null);
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [inheritable_knowledge_bases, setInheritableKnowledgeBases] =
        useState<IMergeableKnowledgeBase[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedKbId, setSelectedKbId] = useState<string | null>(null);
    const [isHasParent, setIsHasParent] = useState<boolean>(false);

    const successMessage = ({
        content,
        duration = 1,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "success",
            content: content,
            duration: duration,
        });
    };

    const errorMessage = ({
        content,
        duration = 2,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "error",
            content: content,
            duration: duration,
        });
    };

    const fetchKnowledgeBases = async (kb_id: string) => {
        setLoading(true);
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/kb/get_kb/${kb_id}`,
                {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            const data: IMergeableKnowledgeBaseResponse = await response.json();

            if (!response.ok) {
                errorMessage({
                    content:
                        data.detail ||
                        "Failed to fetch mergeable knowledge bases",
                });
                console.error("Failed to fetch mergeable knowledge bases");
                return;
            }
            setIsHasParent(data.parents.length > 0);
            setInheritableKnowledgeBases(data.inheritable_knowledge_bases);
        } catch (error) {
            errorMessage({
                content: "Failed to fetch mergeable knowledge bases",
            });
            console.error("Failed to fetch mergeable knowledge bases", error);
        }
        setLoading(false);
    };

    const handleInheritKnowledgeBase = async () => {
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/kb/inherit_kb`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        source_knowledge_base_id: selectedKbId,
                        target_knowledge_base_id: kb_id,
                    }),
                }
            );

            const data = await response.json();

            if (!response.ok) {
                errorMessage({
                    content: data.detail || "Failed to inherit knowledge base",
                });
                console.error("Failed to inherit knowledge base");
                return;
            }

            successMessage({
                content: "Knowledge base inherited successfully",
                duration: 2,
            });
        } catch (error) {
            errorMessage({
                content: "Failed to inherit knowledge base",
            });
            console.error("Failed to inherit knowledge base", error);
        }
    };

    const handleMenuToggle = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsMenuOpen(!isMenuOpen);
    };

    const showModal = () => {
        fetchKnowledgeBases(kb_id);
        setIsModalOpen(true);
    };

    const handleOk = () => {
        if (inheritable_knowledge_bases.length === 0) {
            setIsModalOpen(false);
            return;
        }
        handleInheritKnowledgeBase();
        setTimeout(() => {
            setIsModalOpen(false);
        }, 2000);
    };

    const handleCancel = () => {
        setSelectedKbId(null);
        setIsModalOpen(false);
    };

    const onChange = (value: string) => {
        setSelectedKbId(value);
    };

    const onSearch = (value: string) => {
        const filteredOptions = inheritable_knowledge_bases.map(
            (kb) => kb.name
        );
        if (filteredOptions.includes(value)) {
            setSelectedKbId(value);
        }
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
            className="bg-white rounded-lg shadow-md p-4 sm:p-6 hover:shadow-lg transition-shadow duration-300 w-full h-full relative cursor-pointer"
            onClick={onClick}
        >
            {contextHolder}
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
                        className={`absolute top-8 right-0 bg-white shadow-lg rounded-lg py-2 w-32 transform transition-all duration-200 ease-out z-10 ${
                            isMenuOpen
                                ? "opacity-100 scale-100"
                                : "opacity-0 scale-95 pointer-events-none"
                        }`}
                    >
                        <button
                            onClick={(e) => {
                                e.stopPropagation();
                                showModal();
                            }}
                            className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center text-red-600"
                        >
                            <Combine size={16} className="mr-2" />
                            Inherit
                        </button>
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
                <div onClick={(e) => e.stopPropagation()}>
                    <Modal
                        title={
                            <div className="text-lg font-bold flex justify-center text-red-500">
                                Inherit knowledge base
                            </div>
                        }
                        open={isModalOpen}
                        onOk={handleOk}
                        loading={loading}
                        onCancel={handleCancel}
                    >
                        {inheritable_knowledge_bases.length > 0 ? (
                            <>
                                <label className="block mb-1">
                                    <strong>
                                        Choose KB you want to inherit:
                                    </strong>
                                </label>
                                <Select
                                    showSearch
                                    placeholder="Select knowledge base"
                                    optionFilterProp="label"
                                    onChange={onChange}
                                    onSearch={onSearch}
                                    options={(
                                        inheritable_knowledge_bases || []
                                    ).map((kb) => ({
                                        value: kb.id,
                                        label: kb.name,
                                    }))}
                                    style={{ width: "100%" }}
                                />
                            </>
                        ) : (
                            <label className="block mb-1">
                                <strong>
                                    {isHasParent
                                        ? "This knowledge base is inheriting another knowledge base"
                                        : "No knowledge bases can be inherited"}
                                </strong>
                            </label>
                        )}
                    </Modal>
                </div>
            </div>
        </div>
    );
};

export default KnowledgeBaseCard;
