"use client";
import React, { useState, useEffect } from "react";
import AssistantCards from "@/components/chat/AssistantCards";
import TopBar from "@/components/chat/TopBar";
import CreateAssistantModal from "@/components/chat/CreateAssistantModal";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorComponent from "@/components/Error";
import { useRouter } from "next/navigation";
import { message } from "antd";
import ProtectedRoute from "@/components/ProtectedRoute";
import { IAssistant } from "@/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

const ChatMainPage = () => {
    const router = useRouter();
    const [messageApi, contextHolder] = message.useMessage();
    const [assistants, setAssistants] = useState<IAssistant[]>([]);
    const [selectedAssistant, setSelectedAssistant] =
        useState<IAssistant | null>(null);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const redirectUrl = encodeURIComponent("/chat");

    const fetchAssistants = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/assistant`, {
                headers: {
                    "Content-Type": "application/json",
                },
                credentials: "include",
            });
            if (!response.ok) {
                throw new Error("Failed to fetch assistants");
            }
            const data: IAssistant[] = await response.json();
            const sortedAssistants = data.sort(
                (a, b) =>
                    new Date(b.created_at).getTime() -
                    new Date(a.created_at).getTime()
            );

            successMessage("Successfully fetched assistants");
            setAssistants(sortedAssistants);
            setIsLoading(false);
        } catch (err) {
            errorMessage("Failed to fetch assistants");
            setError(err instanceof Error ? err.message : "An error occurred");
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchAssistants();
    }, [redirectUrl, router]);

    const successMessage = (content: string) => {
        messageApi.open({
            type: "success",
            content: content,
            duration: 1,
        });
    };

    const errorMessage = (content: string) => {
        messageApi.open({
            type: "error",
            content: content,
            duration: 2,
        });
    };

    const handleCreateAssistant = () => {
        setIsCreateModalOpen(true);
    };

    const handleAssistantSelect = (assistant: IAssistant) => {
        setSelectedAssistant(assistant);
        router.push(`/chat/${assistant.id}`);
    };

    const handleDeleteAssistant = async (assistantId: string) => {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/assistant/${assistantId}`,
                {
                    method: "DELETE",
                    credentials: "include",
                }
            );

            if (!response.ok) {
                errorMessage(`Failed to delete assistant: ${assistantId}`);
                throw new Error("Failed to delete assistant");
            }

            successMessage(
                `Assistant: ${assistantId} was deleted successfully!`
            );

            setAssistants((prev) =>
                prev.filter((assistant) => assistant.id !== assistantId)
            );
        } catch (err) {
            setError(err instanceof Error ? err.message : "An error occurred");
        }
    };

    if (isLoading) {
        return (
            <div>
                <LoadingSpinner />
            </div>
        );
    }
    if (error) return <ErrorComponent message={error} />;

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)] bg-gray-100">
            {contextHolder}
            <TopBar
                selectedAssistant={selectedAssistant}
                onCreateAssistant={handleCreateAssistant}
                showSidebarButton={false}
            />
            <main className="flex-1 overflow-auto p-6">
                <div className="max-w-7xl mx-auto">
                    <h1 className="text-3xl font-bold text-gray-800 mb-6">
                        Your Assistants
                    </h1>
                    <AssistantCards
                        assistants={assistants}
                        onSelect={handleAssistantSelect}
                        onDelete={handleDeleteAssistant}
                    />
                </div>
            </main>
            <CreateAssistantModal
                isOpen={isCreateModalOpen}
                onClose={() => setIsCreateModalOpen(false)}
                onCreateSuccess={fetchAssistants}
            />
        </div>
    );
};

export default ProtectedRoute(ChatMainPage);
