"use client";

import React, { useState, useRef } from "react";
import { Modal, Input, InputRef } from "antd";
import { ICreateKnowledgeBase } from "@/types";
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
    onCreate: (body: ICreateKnowledgeBase) => void;
}) => {
    const [name, setName] = useState<string>("");
    const [description, setDescription] = useState<string>("");
    const inputRef = useRef<InputRef>(null);

    if (!isOpen) return null;

    const handleOk = () => {
        const formData = {
            name,
            description,
            useContextualRag: true,
            is_contextual_rag: true,
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
            afterOpenChange={(open) => {
                if (open && inputRef.current) {
                    setTimeout(() => {
                        inputRef.current?.focus();
                    }, 100);
                }
            }}
        >
            <div className="mt-3">
                <label className="block mb-1">
                    <strong>Name:</strong>
                </label>
                <Input
                    ref={inputRef}
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
