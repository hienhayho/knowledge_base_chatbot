"use client";
import React, { useState, useEffect } from "react";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import Sidebar from "@/components/chat/SideBar";
import ChatArea from "@/components/chat/ChatArea";
import TopBar from "@/components/chat/TopBar";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorComponent from "@/components/Error";
import { getCookie } from "cookies-next";
import { IAssistant } from "@/app/(user)/chat/page";
import { IConversation } from "@/app/(user)/chat/page";

const API_BASE_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

const ChatAssistantPage = () => {
    const router = useRouter();
    const params = useParams();

    const searchParams = useSearchParams();

    const assistant_id = params.assistant_id;
    const conversation_id = searchParams.get("conversation");

    const [isSideView, setIsSideView] = useState(true);
    const [selectedAssistant, setSelectedAssistant] =
        useState<IAssistant | null>(null);
    const [selectedConversation, setSelectedConversation] =
        useState<IConversation | null>(null);
    const [sidebarWidth, setSidebarWidth] = useState(256);
    const [conversations, setConversations] = useState<IConversation[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const token = getCookie("access_token");
    const redirectUrl = encodeURIComponent(`/chat/${params.assistant_id}`);

    useEffect(() => {
        if (!token) {
            router.push(`/login?redirect=${redirectUrl}`);
            return;
        }
        if (conversation_id && conversations.length > 0) {
            const conv = conversations.find((c) => c.id === conversation_id);
            if (conv) {
                setSelectedConversation(conv);
            }
        }
    }, [conversation_id, conversations]);

    useEffect(() => {
        fetchAssistant();
        fetchConversations();
    }, [assistant_id]);

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
            setConversations(data);
        } catch (err) {
            setError((err as Error).message);
        }
    };

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
            console.log(assistant_id);
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
            setConversations([...conversations, newConversation]);
            setSelectedConversation(newConversation);
            router.push(
                `/chat/${assistant_id}?conversation=${newConversation.id}`
            );
        } catch (err) {
            setError((err as Error).message);
        }
    };

    if (isLoading) return <LoadingSpinner />;
    if (error) return <ErrorComponent message={error} />;

    return (
        <div className="flex h-[calc(100vh-4rem)] bg-gray-100">
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
                        <ChatArea
                            conversation={selectedConversation}
                            assistantId={selectedAssistant.id}
                        />
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-gray-500">
                            Select a conversation or create a new one to start
                            chatting.
                        </div>
                    )}
                </div>
            </main>
        </div>
    );
};

export default ChatAssistantPage;
