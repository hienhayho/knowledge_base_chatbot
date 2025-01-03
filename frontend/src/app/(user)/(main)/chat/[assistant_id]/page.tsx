"use client";

import React, { useState, useEffect } from "react";
import { message } from "antd";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import Sidebar from "@/components/chat/SideBar";
import WebSocketChatArea from "@/components/chat/WebSocketChatArea";
import TopBar from "@/components/chat/TopBar";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorComponent from "@/components/Error";
import ProtectedRoute from "@/components/ProtectedRoute";
import { IAssistant, IConversation } from "@/types";
import JsonChatArea from "@/components/chat/JsonChatArea";
import { agentApi, assistantApi } from "@/api";

const ChatAssistantPage = () => {
    const router = useRouter();
    const params = useParams();

    const searchParams = useSearchParams();

    const assistant_id = params.assistant_id as string;
    const conversation_id = searchParams.get("conversation");

    const [isSideView, setIsSideView] = useState(true);
    const [messageApi, contextHolder] = message.useMessage();
    const [selectedAssistant, setSelectedAssistant] =
        useState<IAssistant | null>(null);
    const [selectedConversation, setSelectedConversation] =
        useState<IConversation | null>(null);
    const [agentsChoices, setAgentsChoices] = useState<
        {
            value: string;
            label: string;
        }[]
    >([]);
    const [sidebarWidth, setSidebarWidth] = useState(256);
    const [conversations, setConversations] = useState<IConversation[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const redirectUrl = encodeURIComponent(`/chat/${assistant_id}`);

    const useWebsocket = process.env.NEXT_PUBLIC_USE_WEB_SOCKET === "true";

    useEffect(() => {
        if (conversation_id && conversations.length > 0) {
            const conv = conversations.find((c) => c.id === conversation_id);
            if (conv) {
                setSelectedConversation(conv);
            }
        }
    }, [conversation_id, conversations, redirectUrl, router]);

    useEffect(() => {
        const fetchAssistant = async () => {
            try {
                const data = await assistantApi.fetchAssistant(assistant_id);
                messageApi.success({
                    content: "Assistant loaded",
                    duration: 1,
                });
                setSelectedAssistant(data);
                setIsLoading(false);
            } catch (err) {
                setError((err as Error).message);
                setIsLoading(false);
            }
        };

        const fetchConversations = async () => {
            try {
                const data = await assistantApi.fetchAssistantConversations(
                    assistant_id
                );
                messageApi.success({
                    content: "Conversations loaded",
                    duration: 1,
                });
                setConversations(data);
            } catch (err) {
                messageApi.error({
                    content:
                        (err as Error).message ||
                        "Failed to fetch conversations",
                    duration: 1,
                });
                setError((err as Error).message);
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

                messageApi.success({
                    content: "Successfully fetched agents",
                    duration: 1,
                });
            } catch (error) {
                messageApi.error({
                    content:
                        (error as Error).message ||
                        "Failed to fetch agents choices",
                    duration: 1,
                });
                setError((error as Error).message);
            }
        };

        Promise.all([
            fetchAssistant(),
            fetchConversations(),
            fetchAllAgentsChoices(),
        ]);
    }, [assistant_id, redirectUrl, router]);

    const handleConversationSelect = (conversation: IConversation | null) => {
        setSelectedConversation(conversation);
        if (conversation)
            router.push(
                `/chat/${assistant_id}?conversation=${conversation.id}`
            );
        else router.push(`/chat/${assistant_id}`);
    };

    const handleCreateConversation = async () => {
        try {
            const newConversation = await assistantApi.createConversation(
                assistant_id
            );
            messageApi.success({
                content: "Conversation created successfully !",
                duration: 1,
            });
            setConversations([newConversation, ...conversations]);
            setSelectedConversation(newConversation);
            router.push(
                `/chat/${assistant_id}?conversation=${newConversation.id}`
            );
        } catch (err) {
            messageApi.error({
                content:
                    (err as Error).message || "Failed to create conversation",
                duration: 1,
            });
            setError((err as Error).message);
        }
    };

    if (isLoading) return <LoadingSpinner />;
    if (error) return <ErrorComponent message={error} />;

    return (
        <div className="flex h-[calc(100vh-4rem)] bg-gray-100">
            {contextHolder}
            <Sidebar
                isVisible={isSideView}
                width={sidebarWidth}
                setWidth={setSidebarWidth}
                conversations={conversations}
                setConversations={setConversations}
                selectedConversation={selectedConversation}
                onConversationSelect={handleConversationSelect}
                onCreateConversation={handleCreateConversation}
                selectedAssistant={selectedAssistant}
                setSelectedAssistant={setSelectedAssistant}
            />
            <main className="flex-1 flex flex-col overflow-hidden">
                <div>
                    <TopBar
                        isSideView={isSideView}
                        setIsSideView={setIsSideView}
                        selectedAssistant={selectedAssistant}
                        onCreateAssistant={() => {}}
                        showSidebarButton={true}
                        showCreateAssistantButton={false}
                        showUpdateAssistantButton={true}
                        agentChoices={agentsChoices}
                    />
                    {selectedConversation && selectedAssistant ? (
                        useWebsocket ? (
                            <WebSocketChatArea
                                conversation={selectedConversation}
                                assistantId={selectedAssistant.id}
                            />
                        ) : (
                            <JsonChatArea
                                conversation={selectedConversation}
                                assistantId={selectedAssistant.id}
                            />
                        )
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-gray-500">
                            {"Chọn cuộc hội thoại có sẵn hoặc tạo mới."}
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default ProtectedRoute(ChatAssistantPage);
