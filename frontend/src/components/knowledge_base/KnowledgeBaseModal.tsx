"use client";

import React, { useState } from "react";
import { Modal, Input } from "antd";
const { TextArea } = Input;

const KnowledgeBaseModal = ({
    isOpen,
    setIsOpen,
    onClose,
    onCreate,
}: {
    isOpen: boolean;
    setIsOpen: (isOpen: boolean) => void;
    onClose: () => void;
    onCreate: (formData: {
        name: string;
        description: string;
        useContextualRag: boolean;
    }) => void;
}) => {
    const [name, setName] = useState<string>("");
    const [description, setDescription] = useState<string>("");

    if (!isOpen) return null;

    const handleOk = () => {
        const formData = {
            name,
            description,
            useContextualRag: true,
        };
        onCreate(formData);
        setName("");
        setDescription("");
        onClose();
        setIsOpen(false);
    };

    const handleCancel = () => {
        setIsOpen(false);
    };

    return (
        <Modal
            title={
                <div className="text-lg font-bold flex justify-center text-red-500">
                    Create a new knowledge base
                </div>
            }
            open={isOpen}
            onCancel={handleCancel}
            onOk={handleOk}
        >
            <div className="mt-3">
                <label className="block mb-1">
                    <strong>Name:</strong>
                </label>
                <Input
                    placeholder="e.g Math kb"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                />
            </div>
            <div className="mt-3">
                <label className="block mb-1">
                    <strong>{"Description (Optional):"}</strong>
                </label>
                <TextArea
                    rows={4}
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="e.g This knowledge base contains math related documents"
                />
            </div>
        </Modal>
    );
};

export default KnowledgeBaseModal;
