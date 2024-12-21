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
import { useAuth } from "@/hooks/auth";
import JsonChatArea from "@/components/chat/JsonChatArea";

const API_BASE_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

const ChatAssistantPage = () => {
    const router = useRouter();
    const params = useParams();

    const searchParams = useSearchParams();

    const assistant_id = params.assistant_id;
    const conversation_id = searchParams.get("conversation");

    const [isSideView, setIsSideView] = useState(true);
    const [messageApi, contextHolder] = message.useMessage();
    const [selectedAssistant, setSelectedAssistant] =
        useState<IAssistant | null>(null);
    const [selectedConversation, setSelectedConversation] =
        useState<IConversation | null>(null);
    const [sidebarWidth, setSidebarWidth] = useState(256);
    const [conversations, setConversations] = useState<IConversation[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const { token } = useAuth();
    const redirectUrl = encodeURIComponent(`/chat/${assistant_id}`);

    const useWebsocket = process.env.NEXT_PUBLIC_USE_WEB_SOCKET === "true";

    useEffect(() => {
        if (conversation_id && conversations.length > 0) {
            const conv = conversations.find((c) => c.id === conversation_id);
            if (conv) {
                setSelectedConversation(conv);
            }
        }
    }, [conversation_id, conversations, redirectUrl, router, token]);

    useEffect(() => {
        const fetchAssistant = async () => {
            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/assistant/${assistant_id}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                if (!response.ok) {
                    throw new Error("Failed to fetch assistant");
                }
                const data = await response.json();
                setSelectedAssistant(data);
                setIsLoading(false);
            } catch (err) {
                setError((err as Error).message);
                setIsLoading(false);
            }
        };

        const fetchConversations = async () => {
            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/assistant/${assistant_id}/conversations`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                if (!response.ok) {
                    throw new Error("Failed to fetch conversations");
                }
                const data = await response.json();
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

        fetchAssistant();
        fetchConversations();
    }, [assistant_id, token]);

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
            const response = await fetch(
                `${API_BASE_URL}/api/assistant/${assistant_id}/conversations`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                throw new Error("Failed to create conversation");
            }

            const newConversation = await response.json();
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
