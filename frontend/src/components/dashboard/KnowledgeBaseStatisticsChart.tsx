import React from "react";
import { Bar } from "react-chartjs-2";
import {
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from "chart.js";

import { Chart as ChartJS } from "chart.js/auto";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

interface KnowledgeBaseStatisticsChartProps {
    data: {
        name: string;
        total_user_messages: number;
    }[];
}

const KnowledgeBaseStatisticsChart: React.FC<
    KnowledgeBaseStatisticsChartProps
> = ({ data }) => {
    const chartData = {
        labels: data.map((item) => item.name),
        datasets: [
            {
                label: "Number of User Messages",
                data: data.map((item) => item.total_user_messages),
                backgroundColor: "rgba(255, 159, 64, 0.2)",
                borderColor: "rgba(255, 159, 64, 1)",
                borderWidth: 1,
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
                text: "Knowledge Base Statistics",
            },
        },
    };

    return <Bar data={chartData} options={options} />;
};

export default KnowledgeBaseStatisticsChart;
