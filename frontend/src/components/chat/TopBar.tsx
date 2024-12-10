import React from "react";
import { Layout, Plus, Settings, Wrench } from "lucide-react";
import { IAssistant } from "@/app/(user)/(main)/chat/page";
import { Button, message, Modal, Input } from "antd";
import { getCookie } from "cookies-next";
import AddToolsModal from "./AddToolsModal";

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
    const [agentBackstory, setAgentBackstory] = React.useState<string>(
        selectedAssistant?.agent_backstory || ""
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
                        agent_backstory: agentBackstory,
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
                <div className="flex flex-row item-center justify-around flex-shrink-0 gap-10 p-4">
                    <AddToolsModal
                        token={token as string}
                        icon={<Wrench size={16} />}
                        buttonTitle="Chỉnh tools"
                        assistantId={selectedAssistant?.id}
                    />
                    <Button
                        onClick={showModal}
                        icon={<Settings size={16} />}
                        style={{
                            width: "100%",
                            display: "flex",
                            justifyContent: "center",
                            alignItems: "center",
                            borderColor: "gray",
                        }}
                    >
                        Cập nhật trợ lý của bạn
                    </Button>
                    <Modal
                        title={
                            <div className="flex justify-center items-center text-red-500 font-bold mb-4">
                                <span>Cập nhật trợ lý của bạn</span>
                            </div>
                        }
                        open={isModalOpen}
                        width={"80%"}
                        onOk={handleOk}
                        onCancel={handleCancel}
                    >
                        <label className="block text-sm font-bold text-gray-700 my-3">
                            {"Bạn muốn trợ lý của mình tập trung vào điều gì:"}
                        </label>
                        <TextArea
                            rows={3}
                            value={interestPrompt}
                            placeholder="Nhập vào điều bạn muốn trợ lý của mình tập trung vào"
                            onChange={(e) => setInterestPrompt(e.target.value)}
                        />
                        <label className="block text-sm font-bold text-gray-700 my-3">
                            {
                                "Những cái bạn không muốn trợ lý của mình đề cập đến:"
                            }
                        </label>
                        <TextArea
                            rows={3}
                            value={guardPrompt}
                            placeholder="Nhập vào những cái bạn không muốn trợ lý của mình đề cập đến"
                            onChange={(e) => setGuardPrompt(e.target.value)}
                        />
                        <label className="block text-sm font-bold text-gray-700 my-3">
                            {"Nhiệm vụ bạn muốn trợ lý của mình thực hiện:"}
                        </label>
                        <TextArea
                            rows={9}
                            value={agentBackstory}
                            placeholder="Nhập vào nhiệm vụ bạn muốn trợ lý của mình thực hiện"
                            onChange={(e) => setAgentBackstory(e.target.value)}
                        />
                    </Modal>
                </div>
            )}
        </div>
    );
};

export default TopBar;
