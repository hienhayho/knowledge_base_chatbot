import React, { useState, useEffect, useRef } from "react";
import { Send, User, Bot, Loader2, Link } from "lucide-react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import LoadingClipLoader from "@/components/LoadingClipLoader";
import { message, Popover } from "antd";
import { getNow } from "@/utils/formatDate";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_BASE_API_URL || "http://localhost:8000";

interface IMessage {
    sender_type: string;
    content: string;
    media_type?: string;
    created_at: string;
    type?: string;
    metadata?: Record<string, string>;
}

const JsonChatArea = ({
    conversation,
    assistantId,
}: {
    conversation: { id: string };
    assistantId: string;
}) => {
    const [messages, setMessages] = useState<IMessage[]>([]);
    const [inputMessage, setInputMessage] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadingPage, setIsLoadingPage] = useState(false);
    const [messageApi, contextHolder] = message.useMessage();

    const messagesEndRef = useRef<HTMLDivElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        if (conversation) {
            setIsLoadingPage(true);
            fetchConversationHistory();
        }
        if (textareaRef.current) {
            textareaRef.current.focus();
        }
    }, [conversation, assistantId]);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const fetchConversationHistory = async () => {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/assistant/${assistantId}/conversations/${conversation.id}/history`,
                {
                    headers: {
                        "Content-Type": "application/json",
                    },
                    credentials: "include",
                }
            );
            if (!response.ok)
                throw new Error("Failed to fetch conversation history");
            const data = await response.json();
            setMessages(data);
        } catch (error) {
            console.error("Error fetching conversation history:", error);
        } finally {
            setIsLoadingPage(false);
        }
    };

    const sendMessage = async (e: React.FormEvent | React.KeyboardEvent) => {
        e.preventDefault();
        if (!inputMessage.trim()) return;

        const userMessage = {
            sender_type: "user",
            content: inputMessage,
            type: "text",
            created_at: getNow(),
        };
        setMessages((prev) => [...prev, userMessage]);
        setInputMessage("");
        setIsLoading(true);

        try {
            const response = await fetch(
                `${API_BASE_URL}/api/assistant/${assistantId}/conversations/${conversation.id}/messages`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    credentials: "include",
                    body: JSON.stringify({ content: inputMessage }),
                }
            );

            if (!response.ok) throw new Error("Failed to send message");

            const assistantResponse = await response.json();

            setMessages((prev) => [
                ...prev,
                {
                    sender_type: "assistant",
                    content: assistantResponse.assistant_message,
                    type: assistantResponse.type || "text",
                    created_at: assistantResponse.created_at,
                    metadata: assistantResponse.metadata,
                },
            ]);
        } catch (error) {
            console.error("Error sending message:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const scrollToBottom = () => {
        const scrollableDiv = messagesEndRef.current?.parentNode as HTMLElement;
        const isUserNearBottom =
            scrollableDiv.scrollHeight - scrollableDiv.scrollTop <=
            scrollableDiv.clientHeight + 100;

        if (isUserNearBottom) {
            messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    };

    const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
        setInputMessage(e.target.value);
        adjustTextareaHeight();
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            sendMessage(e);
        }
    };

    const adjustTextareaHeight = () => {
        if (textareaRef.current) {
            textareaRef.current.style.height = "auto";
            textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
        }
    };

    const renderMessage = (message: IMessage) => {
        switch (message.type) {
            case "text":
                return (
                    <Markdown
                        remarkPlugins={[remarkGfm]}
                        className="prose prose-sm max-w-none"
                    >
                        {message.content}
                    </Markdown>
                );
            case "video":
                const fullVideoUrl = `${API_BASE_URL}/getfile/${message.content}`;
                return (
                    <video controls className="w-full max-w-lg mt-2">
                        <source src={fullVideoUrl} type="video/mp4" />
                        Your browser does not support the video tag.
                    </video>
                );
            case "image":
                return (
                    <img
                        src={message.content}
                        alt="Assistant generated image"
                        className="w-full max-w-lg mt-2"
                    />
                );
            default:
                return (
                    <Markdown
                        remarkPlugins={[remarkGfm]}
                        className="prose prose-sm max-w-none"
                    >
                        {message.content}
                    </Markdown>
                );
        }
    };

    if (isLoadingPage) {
        return <LoadingClipLoader />;
    }

    return (
        <div className="flex flex-col h-screen bg-white mt-12">
            {contextHolder}
            <div
                className="flex-1 overflow-y-auto p-4"
                style={{ maxHeight: "90vh" }}
            >
                <div className="max-w-4xl mx-auto mt-36">
                    {messages.map((message, index) => (
                        <div
                            key={index}
                            className={`flex ${
                                message.sender_type === "user"
                                    ? "justify-end"
                                    : "justify-start"
                            } mb-4`}
                        >
                            <div
                                className={`${
                                    message.sender_type === "user"
                                        ? "max-w-[60%] bg-blue-600 text-white"
                                        : "max-w-[100%] bg-gray-200 text-gray-800"
                                } p-3 rounded-lg`}
                            >
                                <div className="flex items-center mb-1">
                                    {message.sender_type === "user" ? (
                                        <User size={16} className="mr-2" />
                                    ) : (
                                        <Bot size={16} className="mr-2" />
                                    )}
                                    <span className="font-semibold">
                                        {message.sender_type === "user"
                                            ? "You"
                                            : "Assistant"}
                                    </span>
                                </div>
                                {renderMessage(message)}
                                <div
                                    className={`text-sm mt-2 text-right ${
                                        message.sender_type === "user"
                                            ? "text-gray-200"
                                            : `text-gray-500`
                                    }`}
                                >
                                    {new Date(
                                        message.created_at
                                    ).toLocaleString()}
                                </div>
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex justify-start mb-4">
                            <Loader2 className="w-6 h-6 animate-spin" />
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>
            <div className="sticky bottom-0 w-full bg-white p-2 border-t border-gray-200">
                <form onSubmit={sendMessage} className="p-1">
                    <div className="max-w-4xl mx-auto">
                        <div className="flex items-end bg-white rounded-3xl shadow-lg border border-gray-300 shrink">
                            <textarea
                                ref={textareaRef}
                                value={inputMessage}
                                onChange={handleInputChange}
                                onKeyDown={handleKeyDown}
                                autoFocus
                                placeholder="Message Assistant (Press Enter to send, Shift+Enter for new line)"
                                className="flex-1 bg-transparent border-none rounded-3xl py-4 px-5 focus:outline-none resize-none text-gray-800"
                                rows={1}
                                style={{
                                    maxHeight: "10vh",
                                    overflowY: "auto",
                                }}
                                disabled={isLoading}
                            />
                            <Popover
                                content={<div>{"Nhấn để gửi"}</div>}
                                className=""
                            >
                                <button
                                    type="submit"
                                    className="bg-transparent text-gray-500 p-4 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50 mr-2"
                                    disabled={isLoading}
                                >
                                    <Send size={24} />
                                </button>
                            </Popover>

                            <Popover
                                content={
                                    <div>
                                        {
                                            "Nhấn để sao chép API url cho đoạn chat này"
                                        }
                                    </div>
                                }
                                className=""
                            >
                                <button
                                    type="button"
                                    className="bg-transparent text-gray-500 p-4 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50 mr-2"
                                    onClick={() => {
                                        if (!conversation || !assistantId) {
                                            messageApi.error({
                                                content:
                                                    "Something went wrong !!! Please try refreshing the page",
                                                duration: 1.5,
                                            });
                                            return;
                                        }
                                        navigator.clipboard.writeText(
                                            `${API_BASE_URL}/api/assistant/${assistantId}/conversations/${conversation.id}/production_messages`
                                        );
                                        messageApi.open({
                                            type: "success",
                                            content:
                                                "API chat đã được sao chép vào clipboard !!!",
                                            duration: 1.5,
                                        });
                                    }}
                                >
                                    <Link size={24} />
                                </button>
                            </Popover>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default JsonChatArea;
