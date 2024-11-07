"use client";

import { useState } from "react";
import { Select, Button } from "antd";
import { getCookie } from "cookies-next";
import { useRouter } from "next/navigation";
import { Download, Rocket } from "lucide-react";

interface SelectOption {
    value: string;
    label: string;
}

type WordCloudSource = "Knowledge Base" | "Assistant" | "Conversation" | "";

const BASE_API_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

const WordcloudPage = () => {
    const router = useRouter();

    const redirectURL = encodeURIComponent("/dashboard/wordcloud");

    const token = getCookie("access_token");
    const wordCloudSource = ["Knowledge Base", "Assistant", "Conversation"];
    const wordCloudSourceMap: Record<WordCloudSource, string> = {
        "Knowledge Base": "kbs",
        Assistant: "assistants",
        Conversation: "conversations",
        "": "",
    };
    const createWordCloudMap: Record<WordCloudSource, string> = {
        "Knowledge Base": "kb",
        Assistant: "assistant",
        Conversation: "conversation",
        "": "",
    };

    const [wordCloudSourceSelected, setWordCloudSourceSelected] =
        useState<WordCloudSource>("");

    const [options, setOptions] = useState<SelectOption[]>([]);

    const [selectedOption, setSelectedOption] = useState<SelectOption>({
        value: "",
        label: "",
    });

    const [userUrl, setUserUrl] = useState<string>("");
    const [assistantUrl, setAssistantUrl] = useState<string>("");

    const handleFetchOption = async (source: WordCloudSource) => {
        try {
            if (!token) {
                router.push(`/login?redirect=${redirectURL}`);
            }
            const response = await fetch(
                `${BASE_API_URL}/api/dashboard/${wordCloudSourceMap[source]}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            if (!response.ok) {
                throw new Error("Failed to fetch data");
            }

            const data = await response.json();
            setOptions(
                data.map((item: { id: string; name: string }) => ({
                    value: item.id,
                    label: item.name,
                }))
            );
            setSelectedOption({
                value: "",
                label: "",
            });
            setUserUrl("");
            setAssistantUrl("");
        } catch (error) {
            console.error(error);
        }
    };

    const handleGetWordCloud = async (source: WordCloudSource) => {
        try {
            if (!token) {
                throw new Error("You are not authenticated");
            }

            // Define URLs for the user and assistant word clouds
            const userWordCloudUrl = `${BASE_API_URL}/api/dashboard/wordcloud/${createWordCloudMap[source]}/${selectedOption.value}?is_user=true`;
            const assistantWordCloudUrl = `${BASE_API_URL}/api/dashboard/wordcloud/${createWordCloudMap[source]}/${selectedOption.value}?is_user=false`;

            // Fetch the user word cloud as a blob
            const userResponse = await fetch(userWordCloudUrl, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!userResponse.ok) {
                throw new Error("Failed to fetch user's word cloud image");
            }

            const userBlob = await userResponse.blob();

            // Fetch the assistant word cloud as a blob
            const assistantResponse = await fetch(assistantWordCloudUrl, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!assistantResponse.ok) {
                throw new Error("Failed to fetch assistant's word cloud image");
            }
            const assistantBlob = await assistantResponse.blob();

            setUserUrl(URL.createObjectURL(userBlob));
            setAssistantUrl(URL.createObjectURL(assistantBlob));
        } catch (error) {
            console.error(error);
        }
    };

    const onChange = (value: string) => {
        setUserUrl("");
        setAssistantUrl("");
        setSelectedOption({
            value: value,
            label:
                options.find((option) => option.value === value)?.label || "",
        });
    };

    const onSearch = (value: string) => {
        setUserUrl("");
        setAssistantUrl("");
        const matchedOptions = options.filter((option) =>
            option.label.toLowerCase().includes(value.toLowerCase())
        );
        if (matchedOptions.length === 1) {
            setSelectedOption(matchedOptions[0]);
        }
    };

    return (
        <div className="container mt-10 w-[90%] mx-auto flex">
            <div className="w-[30%] p-4 border-r-2 border-gray-300">
                <span className="text-red-500 font-bold">
                    Bạn muốn tạo wordcloud từ nguồn nào ?
                </span>
                <div className="flex justify-around mt-2">
                    {wordCloudSource.map((source) => (
                        <button
                            key={source}
                            className={`p-2 rounded-lg text-sm ${
                                wordCloudSourceSelected === source
                                    ? "bg-green-500 text-white"
                                    : "bg-gray-200 text-gray-700"
                            }`}
                            onClick={() => {
                                setWordCloudSourceSelected(
                                    source as WordCloudSource
                                );
                                handleFetchOption(source as WordCloudSource);
                            }}
                        >
                            {source}
                        </button>
                    ))}
                </div>
                <div className="mt-10">
                    <span className="text-red-500 font-bold">
                        Chọn nguồn dữ liệu
                    </span>
                    <Select
                        showSearch
                        value={selectedOption.value}
                        placeholder="Please select ..."
                        className="w-full"
                        optionFilterProp="label"
                        onChange={onChange}
                        onSearch={onSearch}
                        options={options}
                    />
                </div>

                <div className="mt-10 flex justify-end">
                    <Button
                        icon={<Rocket size={16} />}
                        onClick={() => {
                            handleGetWordCloud(wordCloudSourceSelected);
                        }}
                    >
                        Tạo Wordcloud
                    </Button>
                </div>
            </div>
            <div className="w-[35%] p-4">
                <span className="flex justify-center text-red-500 font-bold">
                    User&apos;s Wordcloud
                </span>
                {userUrl && (
                    <div>
                        <img
                            src={userUrl}
                            alt="User's Wordcloud"
                            width={800}
                            height={400}
                        />
                        <div className="flex justify-center mt-2">
                            <Button icon={<Download size={16} />}>
                                <a href={userUrl} download>
                                    Download
                                </a>
                            </Button>
                        </div>
                    </div>
                )}
            </div>
            <div className="w-[35%] p-4">
                <span className="text-red-500 font-bold flex justify-center">
                    Assistant&apos;s Wordcloud
                </span>
                {assistantUrl && (
                    <div>
                        <img
                            src={assistantUrl}
                            alt="Assistant's Wordcloud"
                            width={800}
                            height={400}
                        />
                        <div className="flex justify-center mt-2">
                            <Button icon={<Download size={16} />}>
                                <a href={assistantUrl} download>
                                    Download
                                </a>
                            </Button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default WordcloudPage;
