"use client";

import React, { useState } from "react";

const KnowledgeBaseModal = ({
    isOpen,
    onClose,
    onCreate,
}: {
    isOpen: boolean;
    onClose: () => void;
    onCreate: (formData: {
        name: string;
        description: string;
        useContextualRag: boolean;
    }) => void;
}) => {
    const [name, setName] = useState("");
    const [description, setDescription] = useState("");

    if (!isOpen) return null;

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const formData = {
            name,
            description,
            useContextualRag: true,
        };
        onCreate(formData);
        setName("");
        setDescription("");
        onClose();
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
