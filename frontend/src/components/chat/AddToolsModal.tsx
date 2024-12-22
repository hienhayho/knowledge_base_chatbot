"use client";
import { useState, useEffect, ChangeEvent } from "react";
import { DownOutlined } from "@ant-design/icons";
import {
    Button,
    Checkbox,
    Divider,
    Dropdown,
    Modal,
    Popover,
    Tooltip,
    message,
} from "antd";
import { v4 as uuidv4 } from "uuid";
import { Rocket, MoveRight, Info } from "lucide-react";
import DetailToolTip from "../DetailToolTip";

interface Item {
    id: string;
    name: string;
    description: string;
    return_as_answer: boolean;
}

interface Tool {
    id: string;
    name: string;
}

const AddToolsModal = ({
    token,
    icon,
    buttonTitle,
    modalTitle,
    alreadyChoosenTools,
    assistantId,
}: {
    token: string;
    icon?: React.ReactNode;
    buttonTitle?: string;
    modalTitle?: string;
    alreadyChoosenTools?: Item[];
    assistantId?: string;
}) => {
    const [isModalOpen, setIsModalOpen] = useState<boolean>(false);
    const [existTools, setExistTools] = useState<Tool[]>([]);
    const [choosenTools, setChoosenTools] = useState<Item[]>(
        alreadyChoosenTools || []
    );
    const [choosableTools, setChoosableTools] = useState<string[]>([]);
    const [initChoosenTools, setInitChoosenTools] = useState<Item[]>(
        alreadyChoosenTools || []
    );
    const [messageApi, contextHolder] = message.useMessage();
    const [isUpdatingTools, setIsUpdatingTools] = useState<boolean>(false);

    useEffect(() => {
        const fetchTools = async () => {
            try {
                const response = await fetch(
                    `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/tools`,
                    {
                        method: "GET",
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                if (!response.ok) {
                    throw new Error("Failed to fetch tools");
                }
                const data = await response.json();
                const tools: Tool[] = data.tools.map((tool: string) => ({
                    id: uuidv4(),
                    name: tool,
                }));

                const choosenTools: Item[] = [];
                if (assistantId) {
                    const response = await fetch(
                        `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/assistant/${assistantId}`,
                        {
                            method: "GET",
                            headers: {
                                "Content-Type": "application/json",
                                Authorization: `Bearer ${token}`,
                            },
                        }
                    );
                    if (!response.ok) {
                        throw new Error("Failed to fetch assistant tools");
                    }
                    const dataAssistant = await response.json();
                    // Get all keys from dataAssistant.tools
                    const toolsName = Object.keys(dataAssistant.tools);
                    toolsName.forEach((tool: string) => {
                        choosenTools.push({
                            id:
                                tools.find((t) => t.name === tool)?.id ||
                                uuidv4(),
                            name: tool,
                            description:
                                dataAssistant.tools[tool]["description"],
                            return_as_answer:
                                dataAssistant.tools[tool]["return_as_answer"],
                        });
                    });
                }
                console.log(choosenTools);
                const choosableTools = tools.map((tool) => {
                    if (choosenTools.some((t) => t.name === tool.name)) {
                        return null;
                    }
                    return tool.name;
                });

                setChoosableTools(
                    choosableTools.filter((tool) => tool !== null)
                );
                setInitChoosenTools(choosenTools);
                setChoosenTools(choosenTools);
                setExistTools(tools);
            } catch (error) {
                console.error(error);
            }
        };
        fetchTools();
    }, [token]);

    const addItem = (name: string) => {
        const addItemId = existTools.find((tool) => tool.name === name)?.id;

        const newItem: Item = {
            id: addItemId || uuidv4(),
            name,
            description: "",
            return_as_answer: false,
        };

        const updatedChoosenTools = [...choosenTools, newItem];
        const updatedChoosableTools = existTools
            .filter(
                (tool) => !updatedChoosenTools.some((t) => t.name === tool.name)
            )
            .map((tool) => tool.name);

        setChoosenTools(updatedChoosenTools);
        setChoosableTools(updatedChoosableTools);
    };

    const removeItem = (name: string) => {
        const newChoosenTools = choosenTools.filter(
            (tool) => tool.name !== name
        );
        const newChoosableTools = existTools.map((tool) => {
            if (newChoosenTools.some((t) => t.name === tool.name)) {
                return null;
            }
            return tool.name;
        });

        setChoosableTools(newChoosableTools.filter((tool) => tool !== null));
        setChoosenTools(newChoosenTools);
    };

    const updateItem = (
        id: string,
        field: keyof Item,
        value: string | boolean
    ) => {
        setChoosenTools((prevChoosenTools) =>
            prevChoosenTools.map((tool) =>
                tool.id === id ? { ...tool, [field]: value } : tool
            )
        );
    };

    const handleTextAreaChange = (
        e: ChangeEvent<HTMLTextAreaElement>,
        id: string
    ) => {
        updateItem(id, "description", e.target.value);
    };

    const handleUpdateTools = async (choosenTools: Item[]) => {
        const updatedTools = choosenTools.map((tool) => {
            return {
                name: tool.name,
                description: tool.description,
                return_as_answer: tool.return_as_answer,
            };
        });
        try {
            setIsUpdatingTools(true);
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/assistant/${assistantId}/tools`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        tools: updatedTools,
                    }),
                }
            );

            if (!response.ok) {
                throw new Error("Failed to update tools");
            }
            messageApi.success({
                content: "Updated tools successfully",
                duration: 0.5,
            });
            setInitChoosenTools(choosenTools);
        } catch (error) {
            messageApi.error({
                content: "Failed to update tools",
                duration: 0.5,
            });
            setChoosenTools(initChoosenTools);
            console.error(error);
        } finally {
            setIsModalOpen(false);
            setIsUpdatingTools(false);
        }
    };

    return (
        <div onClick={(e) => e.stopPropagation()}>
            {contextHolder}
            <Popover
                content={<div>{"Chỉnh tool cho trợ lý"}</div>}
                className=""
            >
                <Button
                    onClick={(e) => {
                        e.stopPropagation();
                        setIsModalOpen(true);
                    }}
                    icon={icon}
                    style={{
                        borderColor: "gray",
                    }}
                >
                    <span className="font-medium">
                        {buttonTitle || "Thêm tools"}
                    </span>
                </Button>
            </Popover>
            <Modal
                title={
                    <div className="flex justify-center items-center text-red-500 font-bold mb-4">
                        <span>{modalTitle || "Chọn tools"}</span>
                    </div>
                }
                open={isModalOpen}
                width={"85%"}
                footer={null}
                onCancel={(e) => {
                    e.stopPropagation();
                    setIsModalOpen(false);
                }}
            >
                <div className="w-full mx-auto p-5">
                    <div className="flex justify-around gap-4 mb-5">
                        <Dropdown
                            menu={{
                                items: choosableTools.map((tool) => ({
                                    key: tool,
                                    label: (
                                        <div
                                            className="cursor-pointer w-full px-4 py-2 hover:bg-gray-100 hover:text-red-500"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                addItem(tool);
                                            }}
                                        >
                                            {tool}
                                        </div>
                                    ),
                                })),
                            }}
                        >
                            <Button onClick={(e) => e.stopPropagation()}>
                                Tool
                                <DownOutlined />
                            </Button>
                        </Dropdown>
                        <Button
                            loading={isUpdatingTools}
                            icon={<Rocket size={16} />}
                            onClick={(e) => {
                                e.stopPropagation();
                                handleUpdateTools(choosenTools);
                            }}
                        >
                            Cập nhật tool
                        </Button>
                    </div>

                    <div className="flex flex-col gap-4">
                        {choosenTools.map((item) => {
                            return (
                                <div
                                    key={item.id}
                                    className="flex items-center gap-4 p-4 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors duration-200 bg-white"
                                >
                                    <Tooltip title="Tên tool">
                                        <input
                                            type="text"
                                            disabled={true}
                                            value={item.name}
                                            placeholder="Name"
                                            className="text-red-500 font-medium text-center px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent truncate"
                                        />
                                    </Tooltip>
                                    <Divider
                                        type="vertical"
                                        style={{ borderColor: "#7cb305" }}
                                    />
                                    <div className="flex gap-1 items-center">
                                        <Checkbox
                                            onChange={(e) => {
                                                e.stopPropagation();
                                                updateItem(
                                                    item.id,
                                                    "return_as_answer",
                                                    e.target.checked
                                                );
                                            }}
                                            defaultChecked={
                                                item.return_as_answer
                                            }
                                        >
                                            Return Direct ?
                                        </Checkbox>
                                        <DetailToolTip
                                            title="Nếu chọn, kết quả từ tool sẽ được trả về trực tiếp mà không được rewrite lại."
                                            icon={<Info size={16} />}
                                        />
                                    </div>
                                    <Divider
                                        type="vertical"
                                        style={{ borderColor: "#7cb305" }}
                                    />
                                    <MoveRight size={24} />
                                    <textarea
                                        value={item.description}
                                        onChange={(e) => {
                                            e.stopPropagation();
                                            handleTextAreaChange(e, item.id);
                                        }}
                                        onClick={(e) => e.stopPropagation()}
                                        placeholder="Description"
                                        className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent resize-none h-20 overflow-y-auto"
                                        rows={4}
                                    />
                                    <Tooltip title="Xóa tool này">
                                        <button
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                removeItem(item.name);
                                            }}
                                            className="w-8 h-8 flex items-center justify-center bg-red-500 hover:bg-red-600 text-white rounded-md transition-colors duration-200"
                                            type="button"
                                            aria-label="Remove item"
                                        >
                                            ×
                                        </button>
                                    </Tooltip>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </Modal>
        </div>
    );
};

export default AddToolsModal;
