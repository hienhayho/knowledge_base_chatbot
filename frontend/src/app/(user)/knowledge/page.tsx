"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, Plus, Combine } from "lucide-react";
import KnowledgeBaseCard from "@/components/knowledge_base/KnowledgeBaseCard";
import KnowledgeBaseModal from "@/components/knowledge_base/KnowledgeBaseModal";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorComponent from "@/components/Error";
import { getCookie } from "cookies-next";
import { message, Button, Modal, Space, Select, Input } from "antd";

const API_BASE_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

interface IKnowledgeBase {
    id: string;
    name: string;
    description: string;
    document_count: number;
    last_updated: string;
}

interface ICreateKnowledgeBase {
    name: string;
    description: string;
    useContextualRag: boolean;
}

interface IApiResponseError {
    detail: string;
}

const KnowledgeBasePage: React.FC = () => {
    const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
    const [isModalMergeOpen, setIsModalMergeOpen] = useState<boolean>(false);
    const [knowledgeBases, setKnowledgeBases] = useState<IKnowledgeBase[]>([]);
    const [isLoading, setIsLoading] = useState<boolean>(true);
    const [messageApi, contextHolder] = message.useMessage();
    const [error, setError] = useState<string | null>(null);
    const redirectURL = encodeURIComponent("/knowledge");
    const [knowledgeBasesInfo, setKnowledgeBasesInfo] = useState<
        { label: string; value: string }[]
    >([]);
    const [selectedKnowledgeBases, setSelectedKnowledgeBases] = useState<
        string[]
    >([]);
    const [newKnowledgeBaseName, setNewKnowledgeBaseName] =
        useState<string>("Merged KB");
    const [newKnowledgeBaseDescription, setNewKnowledgeBaseDescription] =
        useState<string>("Merged KB description");

    const router = useRouter();
    const token = getCookie("access_token");

    const showMergeModal = () => {
        setIsModalMergeOpen(true);
    };

    const successMessage = ({
        content,
        duration,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "success",
            content: content,
            duration: duration || 2,
        });
    };

    const errorMessage = ({
        content,
        duration,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "error",
            content: content,
            duration: duration || 2,
        });
    };

    const handleOkMergeModal = async () => {
        try {
            setIsModalMergeOpen(false);
            const response = await fetch(`${API_BASE_URL}/api/kb/merge`, {
                method: "PATCH",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    knowledge_base_ids: selectedKnowledgeBases,
                    name: newKnowledgeBaseName,
                    description: newKnowledgeBaseDescription,
                }),
            });

            const data: IKnowledgeBase | IApiResponseError =
                await response.json();

            if (!response.ok) {
                errorMessage({
                    content: (data as IApiResponseError).detail,
                });
                return;
            }

            successMessage({
                content: "Knowledge bases merged successfully",
            });
            setKnowledgeBases([
                ...knowledgeBases.filter(
                    (kb) => !selectedKnowledgeBases.includes(kb.id)
                ),
                data as IKnowledgeBase,
            ]);
        } catch (err) {
            errorMessage({
                content: "Failed to merge knowledge bases",
            });
            console.error("Error merging knowledge bases:", err);
        }
    };

    const handleCancelMergeModal = () => {
        setIsModalMergeOpen(false);
    };

    const handleChange = (value: string[]) => {
        setSelectedKnowledgeBases(value);
    };

    useEffect(() => {
        const fetchKnowledgeBases = async () => {
            try {
                if (!token) {
                    router.push(`/login?redirect=${redirectURL}`);
                    return;
                }

                const response = await fetch(`${API_BASE_URL}/api/kb/get_all`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });

                if (!response.ok) {
                    throw new Error("Failed to fetch knowledge bases");
                }

                const data: IKnowledgeBase[] = await response.json();
                setKnowledgeBasesInfo(
                    data.map((kb) => ({
                        label: kb.name,
                        value: kb.id,
                    }))
                );
                setKnowledgeBases(data);
                setIsLoading(false);
            } catch (err) {
                setError((err as Error).message);
                setIsLoading(false);
            }
        };

        fetchKnowledgeBases();
    }, [token, redirectURL, router]);

    const handleCreateKnowledgeBase = async (
        formData: ICreateKnowledgeBase
    ) => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/kb/create`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${getCookie("access_token")}`,
                },
                body: JSON.stringify({
                    name: formData.name,
                    description: formData.description,
                    is_contextual_rag: formData.useContextualRag,
                }),
            });

            if (!response.ok) {
                throw new Error("Failed to create knowledge base");
            }

            const newKnowledgeBase: IKnowledgeBase = await response.json();

            successMessage({
                content: "Knowledge base created successfully",
            });

            setKnowledgeBases([...knowledgeBases, newKnowledgeBase]);
        } catch (err) {
            console.error("Error creating knowledge base:", err);
            errorMessage({
                content: "Failed to create knowledge base",
            });
        }
    };

    const handleDeleteKnowledgeBase = async (id: string) => {
        try {
            messageApi.open({
                type: "loading",
                content: "Deleting ...",
                duration: 0,
            });

            const response = await fetch(
                `${API_BASE_URL}/api/kb/delete_kb/${id}`,
                {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${getCookie("access_token")}`,
                    },
                }
            );

            messageApi.destroy();

            if (!response.ok) {
                errorMessage({
                    content: "Failed to delete knowledge base",
                });
                return;
            }

            setKnowledgeBases(knowledgeBases.filter((kb) => kb.id !== id));

            successMessage({
                content: "Deleted successfully",
            });
        } catch (err) {
            console.error("Error deleting knowledge base:", err);
            errorMessage({
                content: "Failed to delete knowledge base",
            });
        }
    };

    const handleKnowledgeBaseClick = (id: string) => {
        router.push(`/knowledge/${encodeURIComponent(id)}`);
    };

    const formatDate = (dateString: string) => {
        const date = new Date(dateString);
        return date
            .toLocaleString("en-GB", {
                day: "2-digit",
                month: "2-digit",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
                second: "2-digit",
            })
            .replace(",", "");
    };

    if (isLoading) {
        return <LoadingSpinner />;
    }

    if (error) {
        return <ErrorComponent message={error} />;
    }

    return (
        <div className="min-h-full w-full p-4 sm:p-6 lg:p-8 max-w-screen-2xl mx-auto">
            {contextHolder}
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-2 lg:mb-4">
                Welcome back
            </h1>
            <p className="text-gray-600 text-base sm:text-lg mb-6 sm:mb-8 lg:mb-10">
                Which knowledge base are we going to use today?
            </p>

            <div className="flex flex-col sm:flex-row justify-between items-center mb-6 sm:mb-8 lg:mb-10">
                <div className="relative mb-4 sm:mb-0 w-full sm:w-64 md:w-72 lg:w-96 xl:w-[32rem]">
                    <input
                        type="text"
                        placeholder="Search"
                        className="pl-10 pr-4 py-2 sm:py-3 border rounded-md w-full text-base sm:text-lg"
                    />
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 sm:w-6 sm:h-6 text-gray-400" />
                </div>
                <Button
                    type="primary"
                    onClick={showMergeModal}
                    className="flex items-center justify-center text-base sm:text-lg px-4 py-2 sm:py-3 rounded-md"
                    style={{
                        height: "100%",
                        paddingTop: "calc(0.625rem)",
                    }}
                >
                    <Combine className="w-5 h-5 sm:w-6 sm:h-6 mr-2" />
                    Merge knowledge bases
                </Button>
                <Modal
                    title=""
                    open={isModalMergeOpen}
                    onOk={handleOkMergeModal}
                    onCancel={handleCancelMergeModal}
                >
                    <strong>Choose knowledge bases: </strong>
                    <Space
                        style={{ width: "100%", marginTop: "0.5rem" }}
                        direction="vertical"
                    >
                        <Select
                            mode="multiple"
                            allowClear
                            style={{ width: "100%" }}
                            placeholder="Please select"
                            defaultValue={[]}
                            onChange={handleChange}
                            options={knowledgeBasesInfo}
                        />
                    </Space>
                    <div
                        style={{
                            marginTop: "2rem",
                        }}
                    >
                        <strong>Name:</strong>
                        <Input
                            defaultValue="Merged KB"
                            onChange={(e) =>
                                setNewKnowledgeBaseName(e.target.value)
                            }
                        />
                    </div>

                    <div
                        style={{
                            marginTop: "2rem",
                        }}
                    >
                        <strong>Description:</strong>
                        <Input
                            defaultValue="Merged KB description"
                            onChange={(e) =>
                                setNewKnowledgeBaseDescription(e.target.value)
                            }
                        />
                    </div>
                </Modal>
                <button
                    onClick={() => setIsModalOpen(true)}
                    className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 sm:py-3 rounded-md flex items-center justify-center w-full sm:w-auto text-base sm:text-lg transition duration-300"
                >
                    <Plus className="w-5 h-5 sm:w-6 sm:h-6 mr-2" />
                    Create knowledge base
                </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6 lg:gap-8">
                {knowledgeBases.map((kb) => (
                    <KnowledgeBaseCard
                        key={kb.id}
                        title={kb.name}
                        description={kb.description}
                        docCount={kb.document_count}
                        lastUpdated={formatDate(kb.last_updated)}
                        onClick={() => handleKnowledgeBaseClick(kb.id)}
                        onDelete={() => handleDeleteKnowledgeBase(kb.id)}
                    />
                ))}
            </div>

            <KnowledgeBaseModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onCreate={handleCreateKnowledgeBase}
            />
        </div>
    );
};

export default KnowledgeBasePage;
