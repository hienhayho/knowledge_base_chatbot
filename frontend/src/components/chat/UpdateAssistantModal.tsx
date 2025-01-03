import { Button, Input, message, Modal, Popover, Select } from "antd";
import DetailToolTip from "../DetailToolTip";
import { Info, Pencil } from "lucide-react";
import { useEffect, useState } from "react";
import { IAssistant } from "@/types";
import { assistantApi } from "@/api";

const { TextArea } = Input;

const UpdateAssistantModal = ({
    selectedAssistant,
    setSelectedAssistant,
    agentChoices,
}: {
    selectedAssistant: IAssistant | null;
    setSelectedAssistant?: (assistant: IAssistant) => void;
    agentChoices?: { value: string; label: string }[];
}) => {
    const [isUpdatingPrompt, setIsUpdatingPrompt] = useState(false);
    const [messageApi, contextHolder] = message.useMessage();
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [instructPrompt, setInstructPrompt] = useState<string>("");
    const [agentBackstory, setAgentBackstory] = useState<string>("");
    const [selectedAgent, setSelectedAgent] = useState<string>("");

    useEffect(() => {
        setInstructPrompt(selectedAssistant?.instruct_prompt || "");
        setAgentBackstory(selectedAssistant?.agent_backstory || "");
        setSelectedAgent(selectedAssistant?.agent_type || "");
    }, [selectedAssistant]);

    const showModal = () => {
        setIsModalOpen(true);
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

    const handleOk = async () => {
        try {
            if (!selectedAssistant) {
                errorMessage("No assistant selected");
                setIsModalOpen(false);
                return;
            }
            setIsUpdatingPrompt(true);

            await assistantApi.updateAssistant(
                selectedAssistant.id,
                instructPrompt,
                agentBackstory,
                selectedAgent
            );

            successMessage("Updated assistant successfully");

            if (setSelectedAssistant) {
                setSelectedAssistant({
                    ...selectedAssistant,
                    instruct_prompt: instructPrompt,
                    agent_backstory: agentBackstory,
                    agent_type: selectedAgent,
                });
            }
            setIsModalOpen(false);
        } catch (error) {
            const errMessage = (error as Error).message;
            console.error(error);
            errorMessage(errMessage);
            setIsModalOpen(false);
        } finally {
            setIsUpdatingPrompt(false);
        }
    };

    const handleCancel = () => {
        setIsModalOpen(false);
    };

    const handleSelectAgent = (value: string) => {
        setSelectedAgent(value);
    };

    return (
        <div onClick={(e) => e.stopPropagation()}>
            {contextHolder}
            <Popover
                content={<div>{"Cập nhật cho trợ lý !!!"}</div>}
                className=""
            >
                <Button
                    onClick={(e) => {
                        e.stopPropagation();
                        showModal();
                    }}
                    icon={<Pencil size={16} />}
                    style={{
                        width: "100%",
                        display: "flex",
                        justifyContent: "center",
                        alignItems: "center",
                        borderColor: "gray",
                    }}
                >
                    <span className="font-medium truncate">
                        {"Cập nhật trợ lý của bạn"}
                    </span>
                </Button>
            </Popover>
            <Modal
                title={
                    <div className="flex justify-center items-center text-red-500 font-bold mb-4 truncate">
                        <span>{"Cập nhật trợ lý của bạn"}</span>
                    </div>
                }
                open={isModalOpen}
                width={"80%"}
                onOk={(e) => {
                    e.stopPropagation();
                    handleOk();
                }}
                onCancel={(e) => {
                    e.stopPropagation();
                    handleCancel();
                }}
                confirmLoading={isUpdatingPrompt}
            >
                <div className="flex gap-2 items-center">
                    <label className="block text-sm font-bold text-gray-700 my-3">
                        {"Chọn loại agent:"}
                    </label>
                    <Select
                        showSearch
                        defaultValue={selectedAgent}
                        style={{ width: "30%" }}
                        onChange={handleSelectAgent}
                        options={agentChoices}
                    />
                </div>

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
                    onClick={(e) => e.stopPropagation()}
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
                    onClick={(e) => e.stopPropagation()}
                    value={agentBackstory}
                    placeholder="Nhập vào nhiệm vụ bạn muốn trợ lý của mình thực hiện"
                    onChange={(e) => setAgentBackstory(e.target.value)}
                />
            </Modal>
        </div>
    );
};

export default UpdateAssistantModal;
