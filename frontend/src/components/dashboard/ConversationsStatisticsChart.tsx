import React, { useEffect, useRef } from "react";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend,
} from "chart.js";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend
);

interface ConversationsStatisticsChartProps {
    data: {
        id: string;
        average_session_chat_time: number;
        average_user_messages: number;
    }[];
}

const ConversationsStatisticsChart: React.FC<
    ConversationsStatisticsChartProps
> = ({ data }) => {
    const chartRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        if (chartRef.current) {
            // Xóa biểu đồ cũ (nếu có) để tránh lỗi ghi đè
            ChartJS.getChart(chartRef.current)?.destroy();

            // Tạo biểu đồ mới
            new ChartJS(chartRef.current, {
                type: "bar",
                data: {
                    labels: data.map((item) => item.id),
                    datasets: [
                        {
                            type: "bar" as const,
                            label: "Average Session Chat Time",
                            data: data.map(
                                (item) => item.average_session_chat_time
                            ),
                            backgroundColor: "rgba(75, 192, 192, 0.2)",
                            borderColor: "rgba(75, 192, 192, 1)",
                            borderWidth: 1,
                        },
                        {
                            type: "line" as const,
                            label: "Average User Messages",
                            data: data.map(
                                (item) => item.average_user_messages
                            ),
                            backgroundColor: "rgba(153, 102, 255, 0.2)",
                            borderColor: "rgba(153, 102, 255, 1)",
                            borderWidth: 1,
                            fill: false,
                        },
                    ],
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: "top",
                        },
                        title: {
                            display: true,
                            text: "Conversations Statistics",
                        },
                    },
                },
            });
        }
    }, [data]);

    return <canvas ref={chartRef} />;
};

export default ConversationsStatisticsChart;
