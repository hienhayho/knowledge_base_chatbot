import React from "react";
import { ChevronDown, Layout, Plus } from "lucide-react";
import { useRouter } from "next/navigation";
import { IAssistant } from "@/app/(user)/chat/page";

const TopBar = ({
    isSideView,
    setIsSideView,
    selectedAssistant,
    setSelectedAssistant,
    assistants,
    onCreateAssistant,
    showSidebarButton = true,
    showAssistantSelect = true,
}: {
    isSideView?: boolean;
    setIsSideView?: (isSideView: boolean) => void;
    selectedAssistant: IAssistant | null;
    setSelectedAssistant: (assistant: IAssistant | null) => void;
    assistants: IAssistant[];
    onCreateAssistant: () => void;
    showSidebarButton?: boolean;
    showAssistantSelect?: boolean;
}) => {
    const router = useRouter();

    const handleAssistantChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const assistantId = e.target.value;
        const assistant = assistants.find((a) => a.id === assistantId);
        setSelectedAssistant(assistant || null);
        if (assistant) {
            router.push(`/chat/${assistantId}`);
        }
    };

    return (
        <div className="bg-white shadow-sm p-4 flex items-center justify-between">
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
                {showAssistantSelect && (
                    <div className="relative">
                        <select
                            value={
                                selectedAssistant ? selectedAssistant.id : ""
                            }
                            onChange={handleAssistantChange}
                            className="appearance-none bg-gray-100 border border-gray-300 rounded-md py-2 pl-3 pr-10 text-sm leading-5 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            <option value="">Select an assistant</option>
                            {assistants.map((assistant) => (
                                <option key={assistant.id} value={assistant.id}>
                                    {assistant.name}
                                </option>
                            ))}
                        </select>
                        <ChevronDown
                            size={20}
                            className="absolute right-2 top-1/2 transform -translate-y-1/2 text-gray-400 pointer-events-none"
                        />
                    </div>
                )}
            </div>
            <button
                onClick={onCreateAssistant}
                className="bg-blue-500 text-white px-3 py-2 rounded-md flex items-center text-sm"
            >
                <Plus size={16} className="mr-2" />
                Create Assistant
            </button>
        </div>
    );
};

export default TopBar;
