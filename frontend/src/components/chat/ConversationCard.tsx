import { useState } from "react";
import { getCookie } from "cookies-next";
import { useRouter } from "next/navigation";
import { FolderPen, Trash2, MessageSquare, Download } from "lucide-react";
import { Popover, Row, Col, message, Input, Button } from "antd";
import { IAssistant, IConversation } from "@/app/(user)/(main)/chat/page";

const BASE_API_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

const ConversationCard = ({
    conversation,
    conversations,
    selectedAssistant,
    selectedConversation,
    onConversationSelect,
    setConversations,
}: {
    conversation: IConversation;
    conversations: IConversation[];
    selectedAssistant: IAssistant;
    selectedConversation: IConversation | null;
    onConversationSelect: (conversation: IConversation | null) => void;
    setConversations: (conversations: IConversation[]) => void;
}) => {
    const token = getCookie("access_token");
    const [newName, setNewName] = useState<string>(
        conversation.name || conversation.id
    );
    const [openRenamePopover, setOpenRenamePopover] = useState<boolean>(false);
    const [messageApi, contextHolder] = message.useMessage();
    const router = useRouter();
    const redirectUrl = encodeURIComponent(
        `/chat/${selectedAssistant.id}?conversation=${conversation.id}`
    );

    const handleOpenRenamePopoverChange = (newOpen: boolean) => {
        setOpenRenamePopover(newOpen);
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

    const handleRenameConversation = (conversationId: string) => async () => {
        try {
            if (!token) {
                errorMessage("You are not authenticated");
                setTimeout(() => {
                    router.push(`/login?redirect=${redirectUrl}`);
                });
            }
            const response = await fetch(
                `${BASE_API_URL}/api/assistant/${selectedAssistant?.id}/conversations/${conversationId}/rename`,
                {
                    method: "PATCH",
                    headers: {
                        Authorization: `Bearer ${token}`,
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ name: newName }),
                }
            );
            if (response.ok) {
                successMessage("Conversation renamed successfully");
                setTimeout(() => {
                    setConversations(
                        conversations.map((conversation) =>
                            conversation.id === conversationId
                                ? { ...conversation, name: newName }
                                : conversation
                        )
                    );
                }, 1000);
            }
        } catch (error) {
            console.error(error);
            errorMessage(`Rename failed. Error: ${(error as Error).message}`);
        }
    };

    const handleClickEnterToRename = (
        e: React.KeyboardEvent<HTMLInputElement>
    ) => {
        if (e.key === "Enter") {
            handleRenameConversation(conversation.id)();
            setOpenRenamePopover(false);
        }
    };

    const handleDeleteConversation = (conversationId: string) => async () => {
        try {
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
                    if (conversation && conversation.id === conversationId) {
                        onConversationSelect(null);
                    }
                }, 1000);
            }
        } catch (error) {
            console.error(error);
            errorMessage(`Delete failed. Error: ${(error as Error).message}`);
        }
    };

    const handleExportConversation = (conversationId: string) => async () => {
        try {
            const response = await fetch(
                `${BASE_API_URL}/api/assistant/${selectedAssistant?.id}/export/${conversationId}`,
                {
                    method: "GET",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${conversationId}.json`;
                a.click();
                window.URL.revokeObjectURL(url);

                successMessage("Conversation exported successfully");
            }
        } catch (error) {
            console.error(error);
            errorMessage(`Export failed. Error: ${(error as Error).message}`);
        }
    };

    return (
        <>
            {contextHolder}
            <div
                key={conversation.id}
                className={`mb-2 p-3 rounded-lg cursor-pointer transition-colors duration-200 ${
                    selectedConversation &&
                    selectedConversation.id === conversation.id
                        ? "bg-blue-100"
                        : "bg-gray-50 hover:bg-gray-100"
                }`}
            >
                <Row>
                    <Col span={15}>
                        <div
                            className="flex items-center"
                            onClick={() => onConversationSelect(conversation)}
                        >
                            <MessageSquare
                                size={18}
                                className="mr-2 text-gray-600 flex-shrink-0"
                            />
                            <p className="text-sm text-gray-800 max-w-full">
                                {conversation.name || conversation.id}
                            </p>
                        </div>
                    </Col>
                    <Col span={9}>
                        <div className="flex items-center justify-center">
                            <Popover
                                placement="rightTop"
                                title={
                                    <span className="text-green-600">
                                        Export this conversation?
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
                                        onClick={handleExportConversation(
                                            conversation.id
                                        )}
                                    >
                                        Yes
                                    </Button>
                                }
                            >
                                <Download
                                    size={16}
                                    className="ml-auto"
                                    style={{
                                        marginRight: "0.5rem",
                                    }}
                                />
                            </Popover>
                            <Popover
                                open={openRenamePopover}
                                placement="rightTop"
                                title={
                                    <span className="text-blue-300">
                                        Rename this conversation?
                                    </span>
                                }
                                onOpenChange={handleOpenRenamePopoverChange}
                                content={
                                    <div>
                                        <label>New name:</label>
                                        <Input
                                            placeholder="e.g Algebra"
                                            value={newName}
                                            onChange={(e) =>
                                                setNewName(e.target.value)
                                            }
                                            onKeyDown={handleClickEnterToRename}
                                        />
                                        <Button
                                            size="small"
                                            style={{
                                                display: "flex",
                                                justifyContent: "center",
                                                alignItems: "center",
                                                marginLeft: "auto",
                                                marginTop: "0.5rem",
                                            }}
                                            type="primary"
                                            onClick={handleRenameConversation(
                                                conversation.id
                                            )}
                                        >
                                            Rename
                                        </Button>
                                    </div>
                                }
                            >
                                <FolderPen
                                    style={{
                                        marginRight: "0.5rem",
                                    }}
                                    size={16}
                                    className="ml-auto"
                                />
                            </Popover>
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
                                <Trash2 size={16} className="ml-auto" />
                            </Popover>
                        </div>
                    </Col>
                </Row>
            </div>
        </>
    );
};

export default ConversationCard;
