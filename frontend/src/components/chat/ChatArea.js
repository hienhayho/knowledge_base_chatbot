import React, { useState, useEffect, useRef, useCallback } from "react";
import { Send, User, Bot, Loader2 } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { getCookie } from "cookies-next";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const ChatArea = ({ conversation, assistantId }) => {
    const token = getCookie("access_token");
    const [messages, setMessages] = useState([]);
    const [inputMessage, setInputMessage] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [streamingMessage, setStreamingMessage] = useState("");
    const [isAssistantTyping, setIsAssistantTyping] = useState(false);

    const messagesEndRef = useRef(null);
    const textareaRef = useRef(null);
    const websocketRef = useRef(null);

    const connectWebSocket = useCallback(() => {
        if (websocketRef.current) {
            websocketRef.current.close();
        }

        const ws = new WebSocket(
            `ws://${API_BASE_URL.replace(
                /^https?:\/\//,
                ""
            )}/api/assistant/${assistantId}/conversations/${
                conversation.id
            }/${token}/ws`
        );

        ws.onopen = () => console.log("WebSocket connected");

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            switch (data.type) {
                case "message":
                    setIsAssistantTyping(false);
                    if (data.media_type === "text") {
                        setStreamingMessage((prev) => ({
                            ...prev,
                            content: (prev?.content || "") + data.content,
                            type: "text",
                        }));
                    } else if (data.media_type === "video") {
                        setStreamingMessage({
                            type: "video",
                            content: data.content, // This should be the video URL
                            metadata: data.metadata,
                        });
                    }
                    break;
                case "status":
                    console.log("Status update:", data.content);
                    break;
                case "error":
                    console.error("Error:", data.content);
                    break;
                case "end":
                    setIsAssistantTyping(false);
                    console.log("END MESSAGE");

                    let newMessage = {
                        sender_type: "assistant",
                        media_type: "",
                        content: "",
                        metadata: {},
                    };
                    setStreamingMessage((prev) => {
                        newMessage.type = prev.type;
                        newMessage.content = prev.content;
                        newMessage.metadata = prev.metadata;
                        return null;
                    });

                    setMessages((prevMessages) => [
                        ...prevMessages,
                        newMessage,
                    ]);

                    break;
                default:
                    console.log("Unknown message type:", data.type);
            }
        };

        ws.onclose = () => console.log("WebSocket disconnected");

        websocketRef.current = ws;
    }, [assistantId, conversation.id]);

    useEffect(() => {
        if (conversation) {
            fetchConversationHistory();
            connectWebSocket();
        }

        return () => {
            if (websocketRef.current) {
                websocketRef.current.close();
            }
        };
    }, [conversation, assistantId, connectWebSocket]);

    useEffect(() => {
        scrollToBottom();
    }, [messages, streamingMessage]);

    const fetchConversationHistory = async () => {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/assistant/${assistantId}/conversations/${conversation.id}/history`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            if (!response.ok)
                throw new Error("Failed to fetch conversation history");
            const data = await response.json();
            setMessages(data);
        } catch (error) {
            console.error("Error fetching conversation history:", error);
        }
    };

    const sendMessage = async (e) => {
        e.preventDefault();
        if (!inputMessage.trim()) return;

        const newMessage = {
            sender_type: "user",
            content: inputMessage,
            type: "text",
        };
        setMessages((prevMessages) => [...prevMessages, newMessage]);
        setInputMessage("");
        setIsLoading(true);
        setIsAssistantTyping(true);

        try {
            if (websocketRef.current?.readyState === WebSocket.OPEN) {
                websocketRef.current.send(
                    JSON.stringify({ content: inputMessage })
                );
            } else {
                throw new Error("WebSocket is not connected");
            }
        } catch (error) {
            console.error("Error sending message:", error);
        } finally {
            setIsLoading(false);
        }
    };

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    const handleInputChange = (e) => {
        setInputMessage(e.target.value);
        adjustTextareaHeight();
    };

    const handleKeyDown = (e) => {
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

    const renderMessage = (message) => {
        switch (message.type) {
            case "text":
                return (
                    <ReactMarkdown className="prose prose-sm max-w-none">
                        {message.content}
                    </ReactMarkdown>
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
                    <ReactMarkdown className="prose prose-sm max-w-none">
                        {message.content}
                    </ReactMarkdown>
                );
        }
    };

    return (
        <div className="flex flex-col h-full bg-white">
            <div className="flex-1 overflow-y-auto p-4">
                <div className="max-w-4xl mx-auto">
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
                            </div>
                        </div>
                    ))}
                    {isAssistantTyping && (
                        <Loader2 className="w-6 h-6 animate-spin" />
                    )}
                    {streamingMessage && (
                        <div className="flex justify-start mb-4">
                            <div className="max-w-[100%] p-3 rounded-lg bg-gray-200 text-gray-800">
                                <div className="flex items-center mb-1">
                                    <Bot size={16} className="mr-2" />
                                    <span className="font-semibold">
                                        Assistant
                                    </span>
                                </div>
                                {renderMessage(streamingMessage)}
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>
            <form
                onSubmit={sendMessage}
                className="p-4 border-t border-gray-200"
            >
                <div className="max-w-4xl mx-auto">
                    <div className="flex items-end bg-white rounded-3xl shadow-lg border border-gray-300">
                        <textarea
                            ref={textareaRef}
                            value={inputMessage}
                            onChange={handleInputChange}
                            onKeyDown={handleKeyDown}
                            placeholder="Message Assistant (Press Enter to send, Shift+Enter for new line)"
                            className="flex-1 bg-transparent border-none rounded-3xl py-4 px-5 focus:outline-none resize-none text-gray-800 min-h-[60px]"
                            rows={1}
                            disabled={isLoading}
                        />
                        <button
                            type="submit"
                            className="bg-transparent text-gray-500 p-4 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50 mr-2"
                            disabled={isLoading}
                        >
                            <Send size={24} />
                        </button>
                    </div>
                </div>
            </form>
        </div>
    );
};

export default ChatArea;
