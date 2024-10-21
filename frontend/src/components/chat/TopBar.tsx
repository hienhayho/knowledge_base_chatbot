import React from "react";
import { Layout, Plus } from "lucide-react";
import { IAssistant } from "@/app/(user)/chat/page";
import { Button, message, Modal, Input } from "antd";
import { getCookie } from "cookies-next";

const { TextArea } = Input;

const BASE_API_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

const TopBar = ({
    isSideView,
    setIsSideView,
    onCreateAssistant,
    selectedAssistant,
    setSelectedAssistant,
    showSidebarButton = true,
    showCreateAssistantButton = true,
    showUpdateAssistantButton = false,
}: {
    isSideView?: boolean;
    setIsSideView?: (isSideView: boolean) => void;
    onCreateAssistant: () => void;
    selectedAssistant: IAssistant | null;
    setSelectedAssistant?: (assistant: IAssistant) => void;
    showSidebarButton?: boolean;
    showCreateAssistantButton?: boolean;
    showUpdateAssistantButton?: boolean;
}) => {
    const token = getCookie("access_token");
    const [messageApi, contextHolder] = message.useMessage();
    const [isModalOpen, setIsModalOpen] = React.useState(false);
    const [interestPrompt, setInterestPrompt] = React.useState<string>(
        selectedAssistant?.interested_prompt || ""
    );
    const [guardPrompt, setGuardPrompt] = React.useState<string>(
        selectedAssistant?.guard_prompt || ""
    );

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
                        interested_prompt: interestPrompt,
                        guard_prompt: guardPrompt,
                    }),
                }
            );
            if (response.ok) {
                if (!selectedAssistant) {
                    errorMessage("No assistant selected");
                    setIsModalOpen(false);
                    return;
                }
                successMessage("Updated assistant successfully");
                setTimeout(() => {
                    if (setSelectedAssistant) {
                        setSelectedAssistant({
                            ...selectedAssistant,
                            interested_prompt: interestPrompt,
                            guard_prompt: guardPrompt,
                        });
                    }
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

    return (
        <div className="bg-white shadow-sm p-4 flex items-center justify-between sticky top-0 z-10">
            {contextHolder}
            <div className="flex items-center space-x-4">
                {showSidebarButton && (
                    <button
                        onClick={() =>
                            setIsSideView && setIsSideView(!isSideView)
                        }
                        className="p-2 hover:bg-gray-100 rounded"
                    >
                        <Layout size={20} />
                    </button>
                )}
            </div>
            {showCreateAssistantButton && (
                <button
                    onClick={onCreateAssistant}
                    className="bg-blue-500 text-white px-3 py-2 rounded-md flex items-center text-sm"
                >
                    <Plus size={16} className="mr-2" />
                    Create Assistant
                </button>
            )}
            {showUpdateAssistantButton && (
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
                    <Modal
                        title="Update Your Assistant"
                        open={isModalOpen}
                        onOk={handleOk}
                        onCancel={handleCancel}
                    >
                        <label className="block text-sm font-medium text-gray-700 my-3">
                            {
                                "Type anything you want your bot to concentrate on:"
                            }
                        </label>
                        <TextArea
                            rows={3}
                            value={interestPrompt}
                            onChange={(e) => setInterestPrompt(e.target.value)}
                        />
                        <label className="block text-sm font-medium text-gray-700 my-3">
                            {
                                "Type anything you don't want your bot to talk about:"
                            }
                        </label>
                        <TextArea
                            rows={3}
                            value={guardPrompt}
                            onChange={(e) => setGuardPrompt(e.target.value)}
                        />
                    </Modal>
                </div>
            )}
        </div>
    );
};

export default TopBar;
