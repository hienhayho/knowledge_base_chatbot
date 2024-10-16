import { getCookie } from "cookies-next";
import { Button, Modal, Select, message, Popover } from "antd";
import { Plus, MessageSquare, HelpCircle, Trash2 } from "lucide-react";
import React, { useCallback, useRef, useState, useEffect } from "react";

import { IAssistant } from "@/app/(user)/chat/page";

interface IConversation {
    id: string;
    assistant_id: string;
    created_at: string;
    updated_at: string;
}

const BASE_API_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

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
    setSelectedAssistant,
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
    const [isResizing, setIsResizing] = useState(false);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [interestPrompt, setInterestPrompt] = useState<string[]>(
        selectedAssistant?.interested_phrases || []
    );
    const [guardPrompt, setGuardPrompt] = useState<string[]>(
        selectedAssistant?.guard_phrases || []
    );
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

    useEffect(() => {
        window.addEventListener("mousemove", resize);
        window.addEventListener("mouseup", stopResizing);
        return () => {
            window.removeEventListener("mousemove", resize);
            window.removeEventListener("mouseup", stopResizing);
        };
    }, [resize, stopResizing]);

    const showModal = () => {
        setIsModalOpen(true);
    };

    const handleOk = async () => {
        try {
            if (!selectedAssistant) {
                errorMessage("No assistant selected");
                setIsModalOpen(false);
                return;
            }
            const response = await fetch(
                `${BASE_API_URL}/api/assistant/${selectedAssistant.id}/update`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        interested_phrases: interestPrompt,
                        guard_phrases: guardPrompt,
                    }),
                }
            );
            if (response.ok) {
                successMessage("Assistant updated successfully");
                setTimeout(() => {
                    setSelectedAssistant({
                        ...selectedAssistant,
                        interested_phrases: interestPrompt,
                        guard_phrases: guardPrompt,
                    });
                    setIsModalOpen(false);
                }, 1000);
            }
        } catch (error) {
            console.error(error);
            errorMessage(`Update failed. Error: ${(error as Error).message}`);
            setIsModalOpen(false);
        }
    };

    const handleCancel = () => {
        setIsModalOpen(false);
    };

    const successMessage = (content: string, duration: number = 1) => {
        messageApi.open({
            type: "success",
            content: content,
            duration: duration,
        });
    };

    const errorMessage = (content: string, duration: number = 1) => {
        messageApi.open({
            type: "error",
            content: content,
            duration: duration,
        });
    };

    const handleInterestPromptChange = (value: string[]) => {
        setInterestPrompt(value);
    };

    const handleGuardPromptChange = (value: string[]) => {
        setGuardPrompt(value);
    };

    const handleDeleteConversation = (conversationId: string) => async () => {
        try {
            console.log("Deleting conversation", conversationId);
            const response = await fetch(
                `${BASE_API_URL}/api/assistant/${selectedAssistant?.id}/conversations/${conversationId}`,
                {
                    method: "DELETE",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            if (response.ok) {
                successMessage("Conversation deleted successfully");
                setTimeout(() => {
                    setConversations(
                        conversations.filter(
                            (conversation) => conversation.id !== conversationId
                        )
                    );
                    if (
                        selectedConversation &&
                        selectedConversation.id === conversationId
                    ) {
                        onConversationSelect(null);
                    }
                }, 1000);
            }
        } catch (error) {
            console.error(error);
            errorMessage(`Delete failed. Error: ${(error as Error).message}`);
        }
    };

    if (!isVisible) return null;

    return (
        <>
            {contextHolder}
            <aside
                ref={sidebarRef}
                className="bg-white shadow-md relative flex flex-col"
                style={{ width: `${width}px`, height: "100vh" }}
            >
                <div className="flex-shrink-0 p-4">
                    <Button
                        type="primary"
                        onClick={showModal}
                        style={{
                            width: "100%",
                            display: "flex",
                            justifyContent: "center",
                            alignItems: "center",
                        }}
                    >
                        Update Assistant
                    </Button>
                </div>
                <h2 className="text-lg font-semibold px-4 py-2 flex-shrink-0">
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
                            <div
                                key={conversation.id}
                                className={`mb-2 p-3 rounded-lg cursor-pointer transition-colors duration-200 ${
                                    selectedConversation &&
                                    selectedConversation.id === conversation.id
                                        ? "bg-blue-100"
                                        : "bg-gray-50 hover:bg-gray-100"
                                }`}
                            >
                                <div className="flex items-center">
                                    <div
                                        className="flex items-center"
                                        onClick={() =>
                                            onConversationSelect(conversation)
                                        }
                                    >
                                        <MessageSquare
                                            size={18}
                                            className="mr-2 text-gray-600"
                                        />
                                        <p className="text-sm text-gray-800">
                                            Conversation {conversation.id}
                                        </p>
                                    </div>
                                    <Popover
                                        placement="rightTop"
                                        title={
                                            <span className="text-red-600">
                                                Delete this conversation?
                                            </span>
                                        }
                                        content={
                                            <Button
                                                style={{
                                                    display: "flex",
                                                    justifyContent: "center",
                                                    alignItems: "center",
                                                    marginLeft: "auto",
                                                }}
                                                type="primary"
                                                onClick={handleDeleteConversation(
                                                    conversation.id
                                                )}
                                            >
                                                Yes
                                            </Button>
                                        }
                                    >
                                        <Trash2 size={32} className="ml-auto" />
                                    </Popover>
                                </div>
                            </div>
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
            <Modal
                title="Update Your Assistant"
                open={isModalOpen}
                onOk={handleOk}
                onCancel={handleCancel}
            >
                <label className="block text-sm font-medium text-gray-700 my-3">
                    Type anything you want your bot to concentrate on and press
                    Enter ...
                </label>
                <Select
                    defaultValue={interestPrompt}
                    mode="tags"
                    style={{ width: "100%" }}
                    placeholder="eg. definition"
                    onChange={handleInterestPromptChange}
                    showSearch={false}
                />
                <label className="block text-sm font-medium text-gray-700 my-3">
                    Type anything you don't want your bot to talk about and
                    press Enter ...
                </label>
                <Select
                    defaultValue={guardPrompt}
                    mode="tags"
                    style={{ width: "100%" }}
                    placeholder="eg. author"
                    onChange={handleGuardPromptChange}
                    showSearch={false}
                />
            </Modal>
        </>
    );
};

export default Sidebar;
