"use client";
import React, { useEffect, useState } from "react";
import { Button, Divider, message } from "antd";
import AssistantStatisticsChart from "@/components/dashboard/AssistantStatisticsChart";
import KnowledgeBaseStatisticsChart from "@/components/dashboard/KnowledgeBaseStatisticsChart";
import ConversationsStatisticsChart from "@/components/dashboard/ConversationsStatisticsChart";
import ProtectedRoute from "@/components/ProtectedRoute";

const BASE_API_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

interface IDashBoardResponse {
    file_name: string;
    file_conversation_name: string;
    total_conversations: number;
    average_assistant_response_time: number;

    assistant_statistics: {
        id: string;
        name: string;
        number_of_conversations: number;
    }[];
    conversations_statistics: {
        id: string;
        average_session_chat_time: number;
        average_user_messages: number;
    }[];
    knowledge_base_statistics: {
        id: string;
        name: string;
        total_user_messages: number;
    }[];

    detail?: string;
}

const DashBoardPage = () => {
    const [messageApi, contextHolder] = message.useMessage();
    const [dashboardData, setDashboardData] =
        useState<IDashBoardResponse | null>(null);

    const successMessage = ({
        content,
        duration = 1,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "success",
            content,
            duration,
        });
    };

    const errorMessage = ({
        content,
        duration = 1,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "error",
            content,
            duration,
        });
    };

    useEffect(() => {
        const fetchDashboardData = async () => {
            try {
                const response = await fetch(`${BASE_API_URL}/api/dashboard`, {
                    headers: {
                        "Content-Type": "application/json",
                    },
                    credentials: "include",
                });
                const data: IDashBoardResponse = await response.json();
                if (!response.ok) {
                    console.error(data?.detail || "Something wrong happened");
                    return;
                }
                successMessage({
                    content: "Get statistic successfully !!!",
                });
                setDashboardData(data);
            } catch (error) {
                errorMessage({
                    content:
                        (error as string) || "Something wrong happened !!!",
                });
                console.error(error);
            }
        };
        // Fetch data on first load
        fetchDashboardData();

        // Fetch data each 30 minutes
        const intervalId = setInterval(fetchDashboardData, 30 * 60 * 1000);

        return () => {
            clearInterval(intervalId);
        };
    }, []);

    const handleExport = async (file_name: string) => {
        try {
            const response = await fetch(
                `${BASE_API_URL}/api/dashboard/export/${file_name}`,
                {
                    credentials: "include",
                }
            );
            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${file_name}.xlsx` || "export.xlsx";
                a.click();
                window.URL.revokeObjectURL(url);
                successMessage({
                    content: "Export successfully !!!",
                });
            }
        } catch (error) {
            errorMessage({
                content: (error as string) || "Something wrong happened !!!",
            });
            console.error(error);
        }
    };

    return (
        <div className="container mt-10 mx-auto flex flex-col">
            {contextHolder}
            <div className="flex justify-around items-center">
                <Button
                    type="primary"
                    onClick={() => {
                        handleExport(dashboardData?.file_name || "");
                    }}
                >
                    Export dashboard
                </Button>
                <Button
                    type="primary"
                    onClick={() => {
                        handleExport(
                            dashboardData?.file_conversation_name || ""
                        );
                    }}
                >
                    Export conversations
                </Button>
            </div>
            <Divider
                variant="dashed"
                style={{ borderColor: "#7cb305" }}
                dashed
            ></Divider>
            <br />
            <div className="relative mr-2 flex flex-row gap-4 max-h-[50%]">
                <div className="grid grid-rows-2 gap-4 w-[20%]">
                    <div className="p-2 border-2 border-blue-500 flex flex-col h-24 justify-between shadow-lg rounded-lg">
                        <span className="self-start font-bold">
                            Total Conversations:
                        </span>
                        <span className="self-end text-3xl text-blue-500">
                            {dashboardData?.total_conversations || "???"}
                        </span>
                    </div>
                    <div className="p-2 border-2 border-blue-500 flex flex-col h-24 justify-between shadow-lg rounded-lg">
                        <span className="self-start font-bold">
                            Average Response Time:
                        </span>
                        <span className="self-end text-3xl text-blue-500">
                            {dashboardData?.average_assistant_response_time ||
                                "???"}
                        </span>
                    </div>
                </div>
                <div className="w-full flex-1 grid grid-cols-2 gap-2">
                    <div>
                        {dashboardData && (
                            <AssistantStatisticsChart
                                data={dashboardData.assistant_statistics}
                            />
                        )}
                    </div>
                    <div>
                        {dashboardData && (
                            <KnowledgeBaseStatisticsChart
                                data={dashboardData.knowledge_base_statistics}
                            />
                        )}
                    </div>
                </div>
            </div>
            <div className="mt-4 flex justify-center h-[40%] p-2">
                {dashboardData && (
                    <ConversationsStatisticsChart
                        data={dashboardData.conversations_statistics}
                    />
                )}
            </div>
        </div>
    );
};

export default ProtectedRoute(DashBoardPage);
