import React from "react";
import { Info, Layout, Plus, Settings, Wrench } from "lucide-react";
import { IAssistant } from "@/types";
import { Button, message, Modal, Input, Popover } from "antd";
import AddToolsModal from "./AddToolsModal";
import DetailToolTip from "../DetailToolTip";
import { useAuth } from "@/hooks/auth";

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
    const { token } = useAuth();
    const [isUpdatingPrompt, setIsUpdatingPrompt] = React.useState(false);
    const [messageApi, contextHolder] = message.useMessage();
    const [isModalOpen, setIsModalOpen] = React.useState(false);
    const [instructPrompt, setInstructPrompt] = React.useState<string>(
        selectedAssistant?.instruct_prompt || ""
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
            setIsUpdatingPrompt(true);
            const response = await fetch(
                `${BASE_API_URL}/api/assistant/${selectedAssistant.id}/update`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        instruct_prompt: instructPrompt,
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
                            instruct_prompt: instructPrompt,
                            agent_backstory: agentBackstory,
                        });
                    }
                    setIsModalOpen(false);
                }, 1000);
            }
        } catch (error) {
            console.error(error);
            errorMessage(`Update failed. Error: ${(error as Error).message}`);
            setIsModalOpen(false);
        } finally {
            setIsUpdatingPrompt(false);
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
                        modalTitle={`Chọn tools cho trợ lý: ${selectedAssistant?.name}`}
                        assistantId={selectedAssistant?.id}
                    />
                    <Popover
                        content={<div>{"Cập nhật prompt cho trợ lý !!!"}</div>}
                        className=""
                    >
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
                            <span className="font-medium">
                                {"Cập nhật trợ lý của bạn"}
                            </span>
                        </Button>
                    </Popover>
                    <Modal
                        title={
                            <div className="flex justify-center items-center text-red-500 font-bold mb-4">
                                <span>{"Cập nhật trợ lý của bạn"}</span>
                            </div>
                        }
                        open={isModalOpen}
                        width={"80%"}
                        onOk={handleOk}
                        onCancel={handleCancel}
                        confirmLoading={isUpdatingPrompt}
                    >
                        <div className="flex gap-2 items-center">
                            <label className="block text-sm font-bold text-gray-700 my-3">
                                {"Những lưu ý cho trợ lý khi trả lời:"}
                            </label>
                            <DetailToolTip
                                title="Sẽ được thêm vào system prompt của RAG's final answer."
                                icon={<Info size={16} />}
                            />
                        </div>
                        <TextArea
                            rows={4}
                            value={instructPrompt}
                            placeholder="Nhập vào những lưu ý cho trợ lý khi trả lời trong phạm vi knowledge base này"
                            onChange={(e) => setInstructPrompt(e.target.value)}
                        />
                        <div className="flex gap-2 items-center">
                            <label className="block text-sm font-bold text-gray-700 my-3">
                                {"Nhiệm vụ bạn muốn trợ lý của mình thực hiện:"}
                            </label>
                            <DetailToolTip
                                title="Đây là phần sẽ được đưa vào backstory của crewAI agent."
                                icon={<Info size={16} />}
                            />
                        </div>
                        <TextArea
                            rows={12}
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
