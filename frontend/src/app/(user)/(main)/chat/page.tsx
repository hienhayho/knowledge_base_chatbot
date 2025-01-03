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
import { agentApi, assistantApi } from "@/api";

const ChatMainPage = () => {
    const router = useRouter();
    const [messageApi, contextHolder] = message.useMessage();
    const [assistants, setAssistants] = useState<IAssistant[]>([]);
    const [selectedAssistant, setSelectedAssistant] =
        useState<IAssistant | null>(null);
    const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
    const [agentsChoices, setAgentsChoices] = useState<
        {
            value: string;
            label: string;
        }[]
    >([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const redirectUrl = encodeURIComponent("/chat");

    const fetchAssistants = async () => {
        try {
            const data: IAssistant[] = await assistantApi.fetchAssistants();
            const sortedAssistants = data.sort(
                (a, b) =>
                    new Date(b.created_at).getTime() -
                    new Date(a.created_at).getTime()
            );

            successMessage("Successfully fetched assistants");
            setAssistants(sortedAssistants);
        } catch (err) {
            const errMessage = (err as Error).message;
            errorMessage(errMessage);
            setError(errMessage);
        }
    };

    const fetchAllAgentsChoices = async () => {
        try {
            const data = await agentApi.fetchAllAgentChoices();

            const agents = data.agents;

            setAgentsChoices(
                agents.map((agent: string) => ({
                    value: agent,
                    label: agent,
                }))
            );
            successMessage("Successfully fetched agents");
        } catch (error) {
            const errMessage = (error as Error).message;
            errorMessage(errMessage);
            setError(errMessage);
        }
    };

    useEffect(() => {
        setIsLoading(true);
        fetchAssistants();
        fetchAllAgentsChoices();
        setIsLoading(false);
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
            await assistantApi.deleteAssistant(assistantId);

            successMessage(
                `Assistant: ${assistantId} was deleted successfully!`
            );

            setAssistants((prev) =>
                prev.filter((assistant) => assistant.id !== assistantId)
            );
        } catch (err) {
            const errMessage = (err as Error).message;
            errorMessage(errMessage);
            setError(errMessage);
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
                agentChoices={agentsChoices}
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
                        agentsChoices={agentsChoices}
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
