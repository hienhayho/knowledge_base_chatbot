import React from "react";
import { Bar } from "react-chartjs-2";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
} from "chart.js";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend
);

interface AssistantStatisticsChartProps {
    data: {
        name: string;
        number_of_conversations: number;
    }[];
}

const AssistantStatisticsChart: React.FC<AssistantStatisticsChartProps> = ({
    data,
}) => {
    const chartData = {
        labels: data.map((item) => item.name),
        datasets: [
            {
                label: "Number of Conversations",
                data: data.map((item) => item.number_of_conversations),
                backgroundColor: "rgba(75, 192, 75, 0.2)",
                borderColor: "rgba(75, 192, 75, 1)",
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
                text: "Assistant Statistics",
            },
        },
    };

    return <Bar data={chartData} options={options} />;
};

export default AssistantStatisticsChart;
