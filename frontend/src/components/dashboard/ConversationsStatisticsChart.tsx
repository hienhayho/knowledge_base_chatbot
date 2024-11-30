import React from "react";
import { Chart } from "react-chartjs-2";
import {
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend,
} from "chart.js";

import { Chart as ChartJS } from "chart.js/auto";

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
    const chartData = {
        labels: data.map((item) => item.id),
        datasets: [
            {
                type: "bar" as const,
                label: "Average Session Chat Time",
                data: data.map((item) => item.average_session_chat_time),
                backgroundColor: "rgba(75, 192, 192, 0.2)",
                borderColor: "rgba(75, 192, 192, 1)",
                borderWidth: 1,
            },
            {
                type: "line" as const,
                label: "Average User Messages",
                data: data.map((item) => item.average_user_messages),
                backgroundColor: "rgba(153, 102, 255, 0.2)",
                borderColor: "rgba(153, 102, 255, 1)",
                borderWidth: 1,
                fill: false,
            },
        ],
    };

    const options = {
        responsive: true,
        plugins: {
            legend: {
                position: "top" as const,
            },
            title: {
                display: true,
                text: "Conversations Statistics",
            },
        },
    };

    return <Chart type="bar" data={chartData} options={options} />;
};

export default ConversationsStatisticsChart;
