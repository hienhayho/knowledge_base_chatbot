import { Tooltip } from "antd";
import { useEffect, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import Highlighter from "react-highlight-words";

const TokenRender = ({
    token,
    initVisible,
    searchText,
}: {
    token: string;
    initVisible?: boolean;
    searchText?: string;
}) => {
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        setIsVisible(initVisible || false);
    }, [initVisible]);

    return (
        <div className="flex items-center justify-around max-w-[80%]">
            <div className="w-[80%]">
                <span className="text-blue-400 font-semibold break-all whitespace">
                    {isVisible ? (
                        searchText ? (
                            <Highlighter
                                highlightStyle={{
                                    backgroundColor: "#ffc069",
                                    padding: 0,
                                }}
                                searchWords={[searchText]}
                                autoEscape
                                textToHighlight={token ? token.toString() : ""}
                            />
                        ) : (
                            token
                        )
                    ) : (
                        "••••••••••••••••"
                    )}
                </span>
            </div>
            <Tooltip title={isVisible ? "Ẩn token" : "Hiển thị token"}>
                <div
                    onClick={() => setIsVisible(!isVisible)}
                    className="cursor-pointer"
                >
                    {isVisible ? (
                        <EyeOff size={16} color="gray" />
                    ) : (
                        <Eye size={16} color="blue" />
                    )}
                </div>
            </Tooltip>
        </div>
    );
};

export default TokenRender;
