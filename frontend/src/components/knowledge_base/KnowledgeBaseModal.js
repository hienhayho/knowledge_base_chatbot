"use client";

import React, { useState } from "react";

const KnowledgeBaseModal = ({ isOpen, onClose, onCreate }) => {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");
    const [useContextualRag, setUseContextualRag] = useState(false); // State for tracking contextual RAG

    if (!isOpen) return null;

    const handleSubmit = (e) => {
        e.preventDefault();
        const formData = {
            name,
            description,
            useContextualRag, // Include the Contextual RAG status in the data
        };
        onCreate(formData);
        setName("");
        setDescription("");
        setUseContextualRag(false); // Reset the RAG state after submission
        onClose();
    };

    const handleToggleRag = () => {
        setUseContextualRag((prev) => !prev); // Toggle the state
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-start pt-16">
            <div className="bg-white rounded-lg shadow-lg w-full max-w-3xl flex flex-col">
                <div className="p-6 flex-grow overflow-y-auto">
                    <h2 className="text-2xl font-bold mb-6">
                        Create New Knowledge Base
                    </h2>
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label
                                htmlFor="kb-name"
                                className="block text-sm font-medium text-gray-700 mb-2"
                            >
                                Knowledge Base Name
                            </label>
                            <input
                                id="kb-name"
                                type="text"
                                value={name}
                                onChange={(e) => setName(e.target.value)}
                                placeholder="Enter knowledge base name"
                                className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                                required
                            />
                        </div>

                        <div>
                            <label
                                htmlFor="kb-desc"
                                className="block text-sm font-medium text-gray-700 mb-2"
                            >
                                Knowledge Base Description
                            </label>
                            <input
                                id="kb-desc"
                                type="text"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Enter knowledge base description"
                                className="w-full p-3 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500"
                                required
                            />
                        </div>

                        {/* Toggle Button for Contextual RAG */}
                        <div className="flex items-center space-x-3">
                            <label className="block text-sm font-medium text-gray-700">
                                Click to choose RAG type:
                            </label>
                            <button
                                type="button"
                                onClick={handleToggleRag}
                                className={`px-4 py-2 text-white rounded-md focus:outline-none ${
                                    useContextualRag
                                        ? "bg-green-600 hover:bg-green-700"
                                        : "bg-gray-600 hover:bg-gray-700"
                                }`}
                            >
                                {useContextualRag
                                    ? "Contextual RAG"
                                    : "Original RAG"}
                            </button>
                        </div>
                    </form>
                </div>
                <div className="p-6 bg-gray-50 rounded-b-lg flex justify-end space-x-3">
                    <button
                        type="button"
                        onClick={onClose}
                        className="px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        onClick={handleSubmit}
                        className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                    >
                        Create
                    </button>
                </div>
            </div>
        </div>
    );
};

export default KnowledgeBaseModal;
