import { getCookie } from "cookies-next";
import { message } from "antd";
import { Plus, HelpCircle } from "lucide-react";
import React, { useCallback, useRef, useState, useEffect } from "react";

import { IAssistant } from "@/app/(user)/(main)/chat/page";
import { IConversation } from "@/app/(user)/(main)/chat/page";
import ConversationCard from "./ConversationCard";

const Sidebar = ({
    isVisible,
    width,
    setWidth,
    conversations,
    setConversations,
    selectedConversation,
    onConversationSelect,
    onCreateConversation,
    selectedAssistant,
}: {
    isVisible: boolean;
    width: number;
    setWidth: (width: number) => void;
    conversations: IConversation[];
    setConversations: (conversations: IConversation[]) => void;
    selectedConversation: IConversation | null;
    onConversationSelect: (conversation: IConversation | null) => void;
    onCreateConversation: () => void;
    selectedAssistant: IAssistant | null;
    setSelectedAssistant: (assistant: IAssistant) => void;
}) => {
    const token = getCookie("access_token");
    const sidebarRef = useRef<HTMLDivElement>(null);
    const [isResizing, setIsResizing] = useState<boolean>(false);
    const [messageApi, contextHolder] = message.useMessage();

    const startResizing = useCallback(
        (mouseDownEvent: React.MouseEvent<HTMLDivElement>) => {
            mouseDownEvent.preventDefault();
            setIsResizing(true);
        },
        []
    );

    const stopResizing = useCallback(() => {
        setIsResizing(false);
    }, []);

    const resize = useCallback(
        (mouseMoveEvent: MouseEvent) => {
            if (isResizing) {
                const newWidth =
                    mouseMoveEvent.clientX -
                    sidebarRef.current!.getBoundingClientRect().left;
                if (newWidth > 150 && newWidth < 480) {
                    setWidth(newWidth);
                }
            }
        },
        [isResizing, setWidth]
    );

    const errorMessage = (content: string, duration: number = 1) => {
        messageApi.open({
            type: "error",
            content: content,
            duration: duration,
        });
    };

    useEffect(() => {
        if (!token) {
            errorMessage("Session expired. Please login again.");
            return;
        }
        window.addEventListener("mousemove", resize);
        window.addEventListener("mouseup", stopResizing);
        return () => {
            window.removeEventListener("mousemove", resize);
            window.removeEventListener("mouseup", stopResizing);
        };
    }, [resize, stopResizing]);

    if (!isVisible) return null;

    return (
        <>
            {contextHolder}
            <aside
                ref={sidebarRef}
                className="bg-white shadow-md relative flex flex-col"
                style={{ width: `${width}px`, height: "100vh" }}
            >
                <h2 className="flex justify-center text-lg font-semibold px-4 py-2 flex-shrink-0">
                    Conversations
                </h2>
                <div className="flex-grow overflow-y-auto px-4">
                    {!selectedAssistant ? (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500">
                            <HelpCircle size={48} className="mb-2" />
                            <p className="text-center px-4">
                                Choose an Assistant to continue
                            </p>
                        </div>
                    ) : conversations.length > 0 ? (
                        conversations.map((conversation) => (
                            <ConversationCard
                                key={conversation.id}
                                conversation={conversation}
                                conversations={conversations}
                                selectedAssistant={selectedAssistant}
                                selectedConversation={selectedConversation}
                                onConversationSelect={onConversationSelect}
                                setConversations={setConversations}
                            />
                        ))
                    ) : (
                        <p className="text-sm text-gray-500">
                            No conversations yet.
                        </p>
                    )}
                </div>
                <div className="flex-shrink-0 sticky bottom-0 z-10 p-4 bg-white">
                    <button
                        onClick={onCreateConversation}
                        className={`w-full p-3 rounded-lg flex items-center justify-center transition-colors duration-200 ${
                            selectedAssistant
                                ? "bg-blue-500 text-white hover:bg-blue-600"
                                : "bg-gray-300 text-gray-500 cursor-not-allowed"
                        }`}
                        disabled={!selectedAssistant}
                    >
                        <Plus size={16} className="mr-2" />
                        New Conversation
                    </button>
                </div>
            </aside>
            <div
                className="w-1 cursor-col-resize bg-gray-300 hover:bg-gray-400 transition-colors duration-200"
                onMouseDown={startResizing}
            />
        </>
    );
};

export default Sidebar;
