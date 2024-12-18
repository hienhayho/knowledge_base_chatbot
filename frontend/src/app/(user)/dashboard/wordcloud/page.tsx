"use client";

import { useState } from "react";
import { Select, Button, message } from "antd";
import { Download, Rocket } from "lucide-react";
import ProtectedRoute from "@/components/ProtectedRoute";
import { useAuth } from "@/hooks/auth";
import Image from "next/image";

interface SelectOption {
    value: string;
    label: string;
}

type WordCloudSource = "Knowledge Base" | "Assistant" | "Conversation" | "";

const BASE_API_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

const WordcloudPage = () => {
    const [loading, setLoading] = useState<boolean>(false);
    const [messageApi, contextHolder] = message.useMessage();
    const { token } = useAuth();

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
            const response = await fetch(
                `${BASE_API_URL}/api/dashboard/${wordCloudSourceMap[source]}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            const data = await response.json();
            if (!response.ok) {
                errorMessage({
                    content: data?.detail || "Something wrong happened !!!",
                });
                return;
            }

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
            if (source === "") {
                errorMessage({
                    content: "Please choose base.",
                    duration: 1,
                });
                return;
            }
            if (selectedOption.value === "") {
                errorMessage({
                    content: "Please choose source.",
                    duration: 1,
                });
                return;
            }

            setLoading(true);

            const userWordCloudUrl = `${BASE_API_URL}/api/dashboard/wordcloud/${createWordCloudMap[source]}/${selectedOption.value}?is_user=true`;
            const assistantWordCloudUrl = `${BASE_API_URL}/api/dashboard/wordcloud/${createWordCloudMap[source]}/${selectedOption.value}?is_user=false`;

            const userResponse = await fetch(userWordCloudUrl, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!userResponse.ok) {
                const userData = await userResponse.json();
                throw new Error(
                    userData?.detail ||
                        "Failed to fetch user's word cloud image"
                );
            }

            const userBlob = await userResponse.blob();

            const assistantResponse = await fetch(assistantWordCloudUrl, {
                headers: {
                    Authorization: `Bearer ${token}`,
                },
            });

            if (!assistantResponse.ok) {
                const assistantData = await assistantResponse.json();
                throw new Error(
                    assistantData?.detail ||
                        "Failed to fetch assistant's word cloud image"
                );
            }
            const assistantBlob = await assistantResponse.blob();

            successMessage({
                content: "Generate Wordcloud successfully !!!",
                duration: 1,
            });

            setUserUrl(URL.createObjectURL(userBlob));
            setAssistantUrl(URL.createObjectURL(assistantBlob));
        } catch (error) {
            errorMessage({ content: (error as Error).message, duration: 2 });
            console.error(error);
        } finally {
            setLoading(false);
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
        <div className="flex items-center justify-center h-[80%]">
            {contextHolder}
            <div className="w-[90%] h-[80%] mx-auto flex border-2 border-blue-400 rounded-lg shadow-lg p-2">
                <div className="w-[30%] p-4 border-r-2 border-gray-300">
                    <span className="text-red-500 font-bold">Choose base:</span>
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
                                    handleFetchOption(
                                        source as WordCloudSource
                                    );
                                }}
                            >
                                {source}
                            </button>
                        ))}
                    </div>
                    <div className="mt-10">
                        <span className="text-red-500 font-bold">
                            Choose source:
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
                            loading={loading}
                            onClick={() => {
                                handleGetWordCloud(wordCloudSourceSelected);
                            }}
                        >
                            Generate Wordcloud
                        </Button>
                    </div>
                </div>
                <div className="w-[35%] p-4">
                    <span className="flex justify-center text-red-500 font-bold">
                        User&apos;s Wordcloud
                    </span>
                    {userUrl && (
                        <div>
                            <div className="relative w-full h-[400px]">
                                <Image
                                    src={userUrl}
                                    alt="User's Wordcloud"
                                    fill
                                    style={{ objectFit: "contain" }}
                                    unoptimized // Since we're using blob URLs
                                />
                            </div>
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
                            <div className="relative w-full h-[400px]">
                                <Image
                                    src={assistantUrl}
                                    alt="Assistant's Wordcloud"
                                    fill
                                    style={{ objectFit: "contain" }}
                                    unoptimized // Since we're using blob URLs
                                />
                            </div>
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
        </div>
    );
};

export default ProtectedRoute(WordcloudPage);
