import React, { useEffect, useRef } from "react";
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
    const chartRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        if (chartRef.current) {
            ChartJS.getChart(chartRef.current)?.destroy();

            new ChartJS(chartRef.current, {
                type: "bar",
                data: {
                    labels: data.map((item) => item.name),
                    datasets: [
                        {
                            label: "Number of Conversations",
                            data: data.map(
                                (item) => item.number_of_conversations
                            ),
                            backgroundColor: "rgba(75, 192, 75, 0.2)",
                            borderColor: "rgba(75, 192, 75, 1)",
                            borderWidth: 1,
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
                            text: "Assistant Statistics",
                        },
                    },
                },
            });
        }
    }, [data]);

    return <canvas ref={chartRef}></canvas>;
};

export default AssistantStatisticsChart;
