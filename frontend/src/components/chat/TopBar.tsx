import React from "react";
import { getCookie } from "cookies-next";
import { Layout, Plus } from "lucide-react";
import { IAssistant } from "@/app/(user)/chat/page";
import { Button, Modal, Select, message } from "antd";

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
    onCreateAssistant?: () => void;
    selectedAssistant: IAssistant | null;
    setSelectedAssistant: (assistant: IAssistant) => void;
    showSidebarButton?: boolean;
    showCreateAssistantButton?: boolean;
    showUpdateAssistantButton?: boolean;
}) => {
    const token = getCookie("access_token");
    const [messageApi, contextHolder] = message.useMessage();
    const [isModalOpen, setIsModalOpen] = React.useState(false);
    const [interestPrompt, setInterestPrompt] = React.useState<string[]>(
        selectedAssistant?.interested_phrases || []
    );
    const [guardPrompt, setGuardPrompt] = React.useState<string[]>(
        selectedAssistant?.guard_phrases || []
    );

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
                        interested_phrases: interestPrompt,
                        guard_phrases: guardPrompt,
                    }),
                }
            );
            if (response.ok) {
                successMessage("Assistant updated successfully");
                setTimeout(() => {
                    setSelectedAssistant({
                        ...selectedAssistant,
                        interested_phrases: interestPrompt,
                        guard_phrases: guardPrompt,
                    });
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

    const handleInterestPromptChange = (value: string[]) => {
        setInterestPrompt(value);
    };

    const handleGuardPromptChange = (value: string[]) => {
        setGuardPrompt(value);
    };

    return (
        <div className="bg-white shadow-sm p-4 flex items-end justify-end sticky top-0 z-10 w-full">
            {contextHolder}
            {/* <div className="flex items-center space-x-4">
                {showSidebarButton && (
                    <button
                        onClick={() => setIsSideView(!isSideView)}
                        className="p-2 hover:bg-gray-100 rounded"
                    >
                        <Layout size={20} />
                    </button>
                )}
            </div> */}
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
                                "Type anything you want your bot to concentrate on and press Enter"
                            }
                        </label>
                        <Select
                            defaultValue={interestPrompt}
                            mode="tags"
                            style={{ width: "100%" }}
                            placeholder="eg. definition"
                            onChange={handleInterestPromptChange}
                            showSearch={false}
                        />
                        <label className="block text-sm font-medium text-gray-700 my-3">
                            {
                                "Type anything you don't want your bot to talk about and press Enter"
                            }
                        </label>
                        <Select
                            defaultValue={guardPrompt}
                            mode="tags"
                            style={{ width: "100%" }}
                            placeholder="eg. author"
                            onChange={handleGuardPromptChange}
                            showSearch={false}
                        />
                    </Modal>
                </div>
            )}
        </div>
    );
};

export default TopBar;
