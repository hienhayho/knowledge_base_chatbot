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

const KnowledgeBasePage = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [isModalMergeOpen, setIsModalMergeOpen] = useState(false);
    const [knowledgeBases, setKnowledgeBases] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [messageApi, contextHolder] = message.useMessage();
    const [error, setError] = useState(null);
    const token = getCookie("access_token");
    const redirectURL = encodeURIComponent("/knowledge");
    const router = useRouter();
    const [knowledgeBasesInfo, setKnowledgeBasesInfo] = useState([]);
    const [selectedKnowledgeBases, setSelectedKnowledgeBases] = useState([]);
    const [newKnowledgeBaseName, setNewKnowledgeBaseName] =
        useState("Merged KB");
    const [newKnowledgeBaseDescription, setNewKnowledgeBaseDescription] =
        useState("Merged KB description");

    const showMergeModal = () => {
        setIsModalMergeOpen(true);
    };

    const successMessage = (content) => {
        messageApi.open({
            type: "success",
            content: content,
            duration: 1,
        });
    };

    const errorMessage = (content) => {
        messageApi.open({
            type: "error",
            content: content,
            duration: 1.5,
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

            const data = await response.json();
            console.log(data);

            if (!response.ok) {
                errorMessage(data.detail);
                return;
            }
            successMessage("Successfully merged knowledge bases");
            setKnowledgeBases([
                ...knowledgeBases.filter(
                    (kb) => !selectedKnowledgeBases.includes(kb.id)
                ),
                data,
            ]);
        } catch (err) {
            errorMessage("Failed to merge knowledge bases");
            console.error("Error merging knowledge bases:", err);
        }
    };

    const handleCancelMergeModal = () => {
        setIsModalMergeOpen(false);
    };

    const handleChange = (value) => {
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

                const data = await response.json();
                setKnowledgeBasesInfo(
                    data.map((kb) => {
                        return {
                            label: kb.name,
                            value: kb.id,
                        };
                    })
                );
                setKnowledgeBases(data);
                setIsLoading(false);
            } catch (err) {
                setError(err.message);
                setIsLoading(false);
            }
        };

        fetchKnowledgeBases();
    }, []);

    const handleCreateKnowledgeBase = async (formData) => {
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

            const newKnowledgeBase = await response.json();
            setKnowledgeBases([...knowledgeBases, newKnowledgeBase]);
            router.push(
                `/knowledge/${encodeURIComponent(newKnowledgeBase.id)}`
            );
        } catch (err) {
            console.error("Error creating knowledge base:", err);
            // Here you might want to show an error message to the user
        }
    };

    const handleDeleteKnowledgeBase = async (id) => {
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
                throw new Error("Failed to delete knowledge base");
            }

            setKnowledgeBases(knowledgeBases.filter((kb) => kb.id !== id));
        } catch (err) {
            console.error("Error deleting knowledge base:", err);
        }
    };

    const handleKnowledgeBaseClick = (id) => {
        router.push(`/knowledge/${encodeURIComponent(id)}`);
    };

    const formatDate = (dateString) => {
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
