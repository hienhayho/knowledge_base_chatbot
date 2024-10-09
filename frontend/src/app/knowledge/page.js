"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Search, Plus } from "lucide-react";
import KnowledgeBaseCard from "@/components/knowledge_base/KnowledgeBaseCard";
import KnowledgeBaseModal from "@/components/knowledge_base/KnowledgeBaseModal";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorComponent from "@/components/Error";
import { getCookie } from "cookies-next";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_BASE_API_URL || "http://localhost:8000";

const KnowledgeBasePage = () => {
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [knowledgeBases, setKnowledgeBases] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const router = useRouter();

    useEffect(() => {
        const fetchKnowledgeBases = async () => {
            try {
                const token = getCookie("access_token");
                if (!token) {
                    window.location.href = "/login?redirect=/knowledge";
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
            console.log(formData);
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
