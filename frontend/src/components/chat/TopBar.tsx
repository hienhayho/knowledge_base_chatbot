import React from "react";
import { Layout, Plus, Wrench } from "lucide-react";
import { IAssistant } from "@/types";
import AddToolsModal from "./AddToolsModal";
import UpdateAssistantModal from "./UpdateAssistantModal";

const TopBar = ({
    isSideView,
    setIsSideView,
    onCreateAssistant,
    selectedAssistant,
    agentChoices,
    setSelectedAssistant,
    showSidebarButton = true,
    showCreateAssistantButton = true,
    showUpdateAssistantButton = false,
}: {
    isSideView?: boolean;
    setIsSideView?: (isSideView: boolean) => void;
    onCreateAssistant: () => void;
    selectedAssistant: IAssistant | null;
    agentChoices?: { value: string; label: string }[];
    setSelectedAssistant?: (assistant: IAssistant) => void;
    showSidebarButton?: boolean;
    showCreateAssistantButton?: boolean;
    showUpdateAssistantButton?: boolean;
}) => {
    return (
        <div className="bg-white shadow-sm p-4 flex items-center justify-between sticky top-0 z-10">
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
                        icon={<Wrench size={16} />}
                        buttonTitle="Chỉnh tools"
                        modalTitle={`Chọn tools cho trợ lý: ${selectedAssistant?.name}`}
                        assistantId={selectedAssistant?.id}
                    />
                    <UpdateAssistantModal
                        selectedAssistant={selectedAssistant}
                        setSelectedAssistant={setSelectedAssistant}
                        agentChoices={agentChoices}
                    />
                </div>
            )}
        </div>
    );
};

export default TopBar;
