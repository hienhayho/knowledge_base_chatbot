import React, { useEffect, useRef } from "react";
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    BarController,
    Title,
    Tooltip,
    Legend,
    LineController,
} from "chart.js";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    BarController,
    LineController,
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
                            label: "Number of User Messages",
                            data: data.map((item) => item.total_user_messages),
                            backgroundColor: "rgba(255, 159, 64, 0.2)",
                            borderColor: "rgba(255, 159, 64, 1)",
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
                            text: "Knowledge Base Statistics",
                        },
                    },
                },
            });
        }
    }, [data]);

    return <canvas ref={chartRef}></canvas>;
};

export default KnowledgeBaseStatisticsChart;
