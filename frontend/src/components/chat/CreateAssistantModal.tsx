import React, { useState, useEffect } from "react";
import { X, Info } from "lucide-react";
import { message, Input } from "antd";
import { useAuth } from "@/hooks/auth";

const { TextArea } = Input;

const API_BASE_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

interface IKnowledgeBase {
    id: string;
    name: string;
}

const CreateAssistantModal = ({
    isOpen,
    onClose,
    onCreateSuccess,
}: {
    isOpen: boolean;
    onClose: () => void;
    onCreateSuccess: () => void;
}) => {
    const [isVisible, setIsVisible] = useState<boolean>(false);
    const [assistantName, setAssistantName] = useState<string>("");
    const [description, setDescription] = useState<string>("");
    const [instructionPrompt, setInstructionPrompt] = useState<string>("");
    const [agentBackstory, setAgentBackstory] = useState<string>("");
    const [knowledgeBases, setKnowledgeBases] = useState<IKnowledgeBase[]>([]);
    const [selectedKnowledgeBase, setSelectedKnowledgeBase] =
        useState<string>("");
    const [model, setModel] = useState<string>("gpt-4o-mini");
    const [messageApi, contextHolder] = message.useMessage();

    const { token } = useAuth();

    useEffect(() => {
        if (isOpen) {
            setIsVisible(true);
            fetchKnowledgeBases();
        } else {
            setIsVisible(false);
        }
    }, [isOpen, token]);

    const successMessage = (content: string) => {
        messageApi.open({
            type: "success",
            content: content,
        });
    };

    const errorMessage = (content: string) => {
        messageApi.open({
            type: "error",
            content: content,
        });
    };

    const fetchKnowledgeBases = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/api/kb/get_all`, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });
            if (response.ok) {
                const data = await response.json();
                setKnowledgeBases(data);
            } else {
                console.error("Failed to fetch knowledge bases");
            }
        } catch (error) {
            console.error("Error fetching knowledge bases:", error);
        }
    };

    const handleClose = () => {
        setIsVisible(false);
        setTimeout(() => {
            onClose();
        }, 300);
    };

    const handleSubmit = async () => {
        const payload = {
            name: assistantName,
            description: description,
            instruct_prompt: instructionPrompt,
            knowledge_base_id: selectedKnowledgeBase,
            agent_backstory: agentBackstory,
            configuration: {
                model: model,
                service: "openai",
                temperature: "0.8",
            },
        };
        try {
            const response = await fetch(`${API_BASE_URL}/api/assistant/`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify(payload),
            });

            const data = await response.json();
            if (response.ok) {
                successMessage(
                    `Assistant "${data.name}" created successfully!`
                );
                setTimeout(() => {
                    onClose();
                    onCreateSuccess();
                    // router.push(`/chat/${data.id}`);
                }, 1500);
            } else {
                errorMessage(data.detail);
                console.error("Failed to create assistant");
            }
        } catch (error) {
            errorMessage(
                `Error creating assistant: ${(error as Error).message}`
            );
            console.error("Error creating assistant:", error);
        }
    };

    if (!isOpen) return null;

    return (
        <div
            className={`fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center pt-6 z-50 transition-all duration-300 ease-in-out ${
                isVisible ? "opacity-100" : "opacity-0 pointer-events-none"
            }`}
        >
            {contextHolder}
            <div
                className={`bg-white rounded-lg shadow-xl w-full max-w-2xl transform transition-all duration-300 ease-in-out ${
                    isVisible
                        ? "translate-y-0 opacity-100"
                        : "-translate-y-4 opacity-0"
                }`}
            >
                <div className="flex justify-between items-center p-6 border-b">
                    <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-gray-200 rounded-lg flex items-center justify-center">
                            <span className="text-2xl">🤖</span>
                        </div>
                        <div>
                            <h2 className="text-xl font-semibold">
                                Chat Configuration
                            </h2>
                            <p className="text-sm text-gray-500">
                                Here, dress up a dedicated assistant for your
                                special knowledge bases! 💕
                            </p>
                        </div>
                    </div>
                    <button
                        onClick={handleClose}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        <X size={24} />
                    </button>
                </div>

                <div className="p-6 space-y-2">
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Assistant name{" "}
                            <span className="text-red-500">*</span>
                        </label>
                        <Input
                            placeholder="e.g Math tutor"
                            value={assistantName}
                            onChange={(e) => setAssistantName(e.target.value)}
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700 my-2">
                            Description{" "}
                        </label>
                        <TextArea
                            rows={2}
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="e.g A helpful assistant for math problem"
                        />
                        <label className="block text-sm font-medium text-gray-700 my-2">
                            {
                                "Nhập vào những lưu ý cho trợ lý khi trả lời trong phạm vi knowledge base này"
                            }
                        </label>
                        <TextArea
                            rows={2}
                            value={instructionPrompt}
                            onChange={(e) =>
                                setInstructionPrompt(e.target.value)
                            }
                            placeholder="e.g. I don't want you to talk about my personal life"
                        />
                        <label className="block text-sm font-medium text-gray-700 my-2">
                            {"Nhiệm vụ bạn muốn trợ lý của mình thực hiện:"}
                        </label>
                        <TextArea
                            rows={2}
                            value={agentBackstory}
                            onChange={(e) => setAgentBackstory(e.target.value)}
                            placeholder="e.g. I am a math tutor assistant with 5 years of experience."
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Model <span className="text-red-500">*</span>
                        </label>
                        <select
                            value={model}
                            onChange={(e) => setModel(e.target.value)}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 p-2"
                        >
                            <option value="gpt-4o-mini">GPT-4o mini</option>
                        </select>
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Knowledgebases{" "}
                            <span className="text-red-500">*</span>{" "}
                            <Info className="inline-block w-4 h-4 text-gray-400" />
                        </label>
                        <select
                            value={selectedKnowledgeBase}
                            onChange={(e) =>
                                setSelectedKnowledgeBase(e.target.value)
                            }
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 p-2"
                        >
                            <option value="">Chọn knowledge base</option>
                            {knowledgeBases.map((kb) => (
                                <option key={kb.id} value={kb.id}>
                                    {kb.name}
                                </option>
                            ))}
                        </select>
                    </div>
                </div>

                <div className="flex justify-end space-x-2 p-6 border-t">
                    <button
                        onClick={handleClose}
                        className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Hủy
                    </button>
                    <button
                        onClick={handleSubmit}
                        className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Tạo trợ lý
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CreateAssistantModal;
