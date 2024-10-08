import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { X, Upload, Info } from "lucide-react";
import { getCookie } from "cookies-next";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const CreateAssistantModal = ({ isOpen, onClose, onCreateSuccess }) => {
    const router = useRouter();
    const [assistantName, setAssistantName] = useState("");
    const [description, setDescription] = useState("");
    const [systemPrompt, setSystemPrompt] = useState(
        "You are a helpful assistant."
    );
    const [knowledgeBases, setKnowledgeBases] = useState([]);
    const [selectedKnowledgeBase, setSelectedKnowledgeBase] = useState("");
    const [model, setModel] = useState("gpt-4o-mini");

    useEffect(() => {
        if (isOpen) {
            fetchKnowledgeBases();
        }
    }, [isOpen]);

    const fetchKnowledgeBases = async () => {
        const token = getCookie("access_token");
        if (!token) {
            router.push("/login?redirect=/chat");
            return;
        }
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

    const handleSubmit = async () => {
        const token = getCookie("access_token");

        if (!token) {
            router.push("/login?redirect=/chat");
            return;
        }
        console.log(selectedKnowledgeBase);

        const payload = {
            name: assistantName,
            description: description,
            system_prompt: systemPrompt,
            knowledge_base_id: selectedKnowledgeBase,
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

            if (response.ok) {
                const data = await response.json();
                onClose();
                onCreateSuccess(); // Call this to update the assistants list in the parent component
                router.push(`/chat/${data.id}`); // Navigate to the new assistant's page
            } else {
                console.error("Failed to create assistant");
                // You might want to show an error message to the user here
            }
        } catch (error) {
            console.error("Error creating assistant:", error);
            // You might want to show an error message to the user here
        }
    };
    console.log(systemPrompt);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-start pt-16 z-50">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl">
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
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        <X size={24} />
                    </button>
                </div>

                <div className="p-6 space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Assistant name{" "}
                            <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            value={assistantName}
                            onChange={(e) => setAssistantName(e.target.value)}
                            placeholder="e.g. Resume Jarvis"
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 p-2"
                        />
                    </div>

                    <div>
                        <label className="block text-sm font-medium text-gray-700">
                            Description{" "}
                            <Info className="inline-block w-4 h-4 text-gray-400" />
                        </label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={3}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 p-2"
                        />
                        <label className="block text-sm font-medium text-gray-700">
                            System Prompt
                            <Info className="inline-block w-4 h-4 text-gray-400" />
                        </label>
                        <textarea
                            value={systemPrompt}
                            onChange={(e) => setSystemPrompt(e.target.value)}
                            rows={3}
                            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-300 focus:ring focus:ring-blue-200 focus:ring-opacity-50 p-2"
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
                            {/* Add more options here for future extensions */}
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
                            <option value="">Please select</option>
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
                        onClick={onClose}
                        className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleSubmit}
                        className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Create Assistant
                    </button>
                </div>
            </div>
        </div>
    );
};

export default CreateAssistantModal;
