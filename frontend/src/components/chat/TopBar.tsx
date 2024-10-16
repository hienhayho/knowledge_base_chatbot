import React from "react";
import { Layout, Plus } from "lucide-react";
import { IAssistant } from "@/app/(user)/chat/page";

const TopBar = ({
    isSideView,
    setIsSideView,
    onCreateAssistant,
    showSidebarButton = true,
    showCreateAssistantButton = true,
}: {
    isSideView?: boolean;
    setIsSideView?: (isSideView: boolean) => void;
    onCreateAssistant: () => void;
    selectedAssistant: IAssistant | null;
    showSidebarButton?: boolean;
    showCreateAssistantButton?: boolean;
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
        </div>
    );
};

export default TopBar;
