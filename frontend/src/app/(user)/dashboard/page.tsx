"use client";
import React, { useEffect, useState } from "react";
import { getCookie } from "cookies-next";
import { useRouter } from "next/navigation";
import AssistantStatisticsChart from "@/components/dashboard/AssistantStatisticsChart";
import KnowledgeBaseStatisticsChart from "@/components/dashboard/KnowledgeBaseStatisticsChart";
import ConversationsStatisticsChart from "@/components/dashboard/ConversationsStatisticsChart";

const BASE_API_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

interface IDashBoardResponse {
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
}

const DashBoardPage = () => {
    const router = useRouter();
    const token = getCookie("access_token");
    const redirectUrl = encodeURIComponent("/dashboard");
    const [dashboardData, setDashboardData] =
        useState<IDashBoardResponse | null>(null);

    useEffect(() => {
        if (!token) {
            router.push(`/login?redirect=${redirectUrl}`);
            return;
        }
        const fetchDashboardData = async () => {
            try {
                const response = await fetch(`${BASE_API_URL}/api/dashboard`, {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                });
                const data: IDashBoardResponse = await response.json();
                setDashboardData(data);
            } catch (error) {
                console.error(error);
            }
        };
        fetchDashboardData();
    }, [token, router, redirectUrl]);

    return (
        <div className="container mt-10 mx-auto flex flex-col">
            <div className="relative mr-2 flex flex-row gap-4 max-h-[50%]">
                <div className="grid grid-rows-2 gap-4 w-[20%]">
                    <div className="p-2 border-2 border-blue-500 flex flex-col h-24 justify-between shadow-lg rounded-lg">
                        <span className="self-start font-bold">
                            Tổng số cuộc trò chuyện
                        </span>
                        <span className="self-end text-3xl text-blue-500">
                            {dashboardData?.total_conversations}
                        </span>
                    </div>
                    <div className="p-2 border-2 border-blue-500 flex flex-col h-24 justify-between shadow-lg rounded-lg">
                        <span className="self-start font-bold">
                            Thời gian phản hồi trung bình
                        </span>
                        <span className="self-end text-3xl text-blue-500">
                            {dashboardData?.average_assistant_response_time}
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

export default DashBoardPage;
