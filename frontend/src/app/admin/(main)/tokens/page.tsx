"use client";

import { SearchOutlined, UserOutlined } from "@ant-design/icons";
import { useAuth } from "@/hooks/auth";
import { IToken, ITokenResponse, ITokenFormValues } from "@/types";
import {
    Button,
    Form,
    FormProps,
    Input,
    InputRef,
    message,
    Popconfirm,
    Space,
    Table,
    TableColumnType,
    Tag,
    Tooltip,
} from "antd";
import Highlighter from "react-highlight-words";
import { useEffect, useRef, useState } from "react";
import { FilterDropdownProps } from "antd/es/table/interface";
import LoadingSpinner from "@/components/LoadingSpinner";
import { Plus, Trash2 } from "lucide-react";
import AddModal from "@/components/admin/AddModal";
import ProtectedRoute from "@/components/ProtectedRoute";
import { formatDate } from "@/utils";
import TokenRender from "@/components/admin/TokenRender";

type DataIndex = keyof IToken;

const AdminTokenManagementPage = () => {
    const { token } = useAuth();
    const [loadingPage, setLoadingPage] = useState(true);
    const [tokens, setTokens] = useState<IToken[]>([]);
    const [searchText, setSearchText] = useState("");
    const [searchedColumn, setSearchedColumn] = useState("");
    const searchInput = useRef<InputRef>(null);
    const [messageApi, contextHolder] = message.useMessage();
    const [open, setOpen] = useState<boolean>(false);
    const [loadingRegister, setLoadingRegister] = useState<boolean>(false);
    const [form] = Form.useForm();

    useEffect(() => {
        if (!token) {
            return;
        }
        const fetchAllTokens = async () => {
            try {
                const respone = await fetch(
                    `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/admin/tokens`,
                    {
                        headers: {
                            "Content-Type": "application/json",
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );

                const data = await respone.json();

                if (!respone.ok) {
                    throw new Error(data.detail || "Failed to fetch tokens");
                }

                messageApi.success("Lấy thông tin tokens thành công !");

                setTokens(
                    data.map((token: ITokenResponse) => ({
                        key: token.id,
                        token: token.token,
                        role: token.role,
                        user_id: token.user_id,
                        username: token.username,
                        id: token.id,
                        createdAt: formatDate(token.created_at),
                        updatedAt: formatDate(token.updated_at),
                    }))
                );
            } catch (error) {
                console.error("Lấy thông tin tokens thất bại", error);
                messageApi.error((error as Error).message);
            } finally {
                setLoadingPage(false);
            }
        };
        fetchAllTokens();
    }, [token]);

    const handleSearch = (
        selectedKeys: string[],
        confirm: FilterDropdownProps["confirm"],
        dataIndex: DataIndex
    ) => {
        confirm();
        setSearchText(selectedKeys[0]);
        setSearchedColumn(dataIndex);
    };

    const handleReset = (clearFilters: () => void) => {
        clearFilters();
        setSearchText("");
    };

    const deleteToken = async (id: string) => {
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/admin/delete-token/${id}`,
                {
                    method: "DELETE",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || "Failed to delete token");
            }

            messageApi.success("Xóa token thành công !");
            setTokens((prev) => prev.filter((token) => token.id !== id));
        } catch (error) {
            console.error("Xóa người dùng thất bại", error);
            messageApi.error((error as Error).message);
        }
    };

    const getColumnSearchProps = (
        dataIndex: DataIndex,
        renderFunction?: (text: string) => JSX.Element
    ): TableColumnType<IToken> => ({
        filterDropdown: ({
            setSelectedKeys,
            selectedKeys,
            confirm,
            clearFilters,
            close,
        }) => (
            <div style={{ padding: 8 }} onKeyDown={(e) => e.stopPropagation()}>
                <Input
                    ref={searchInput}
                    placeholder={`Search ${dataIndex}`}
                    value={selectedKeys[0]}
                    onChange={(e) =>
                        setSelectedKeys(e.target.value ? [e.target.value] : [])
                    }
                    onPressEnter={() =>
                        handleSearch(
                            selectedKeys as string[],
                            confirm,
                            dataIndex
                        )
                    }
                    style={{ marginBottom: 8, display: "block" }}
                />
                <Space>
                    <Button
                        type="primary"
                        onClick={() =>
                            handleSearch(
                                selectedKeys as string[],
                                confirm,
                                dataIndex
                            )
                        }
                        icon={<SearchOutlined />}
                        size="small"
                        style={{ width: 90 }}
                    >
                        Search
                    </Button>
                    <Button
                        onClick={() =>
                            clearFilters && handleReset(clearFilters)
                        }
                        size="small"
                        style={{ width: 90 }}
                    >
                        Reset
                    </Button>
                    <Button
                        type="link"
                        size="small"
                        onClick={() => {
                            confirm({ closeDropdown: false });
                            setSearchText((selectedKeys as string[])[0]);
                            setSearchedColumn(dataIndex);
                        }}
                    >
                        Filter
                    </Button>
                    <Button
                        type="link"
                        size="small"
                        onClick={() => {
                            close();
                        }}
                    >
                        close
                    </Button>
                </Space>
            </div>
        ),
        filterIcon: (filtered: boolean) => (
            <SearchOutlined
                style={{ color: filtered ? "#1677ff" : undefined }}
            />
        ),
        onFilter: (value, record) =>
            record[dataIndex]
                ? record[dataIndex]
                      .toString()
                      .toLowerCase()
                      .includes((value as string).toLowerCase())
                : false,

        // @ts-expect-error - Not sure why antd is throwing an error here
        filterDropdownProps: {
            onOpenChange(open: boolean) {
                if (open) {
                    setTimeout(() => searchInput.current?.select(), 100);
                }
            },
        },

        render: (text) => {
            if (dataIndex === "token") {
                const initVisible =
                    searchedColumn === "token" &&
                    searchText !== "" &&
                    text.includes(searchText);

                return (
                    <TokenRender
                        token={text}
                        initVisible={initVisible}
                        searchText={searchText}
                    />
                );
            }
            return searchedColumn === dataIndex ? (
                <Highlighter
                    highlightStyle={{ backgroundColor: "#ffc069", padding: 0 }}
                    searchWords={[searchText]}
                    autoEscape
                    textToHighlight={text ? text.toString() : ""}
                />
            ) : renderFunction ? (
                renderFunction(text)
            ) : (
                text
            );
        },
    });

    const columns = [
        {
            title: "Tên đăng nhập",
            dataIndex: "username",
            key: "username",
            ...getColumnSearchProps("username", (text: string) => (
                <div className="flex items-center ml-2">
                    <span className="text-cyan-500 font-semibold">{text}</span>
                </div>
            )),
        },
        {
            title: "Quyền",
            dataIndex: "role",
            key: "role",
            ...getColumnSearchProps("role", (text: string) => {
                let color;
                if (text === "user") {
                    color = "green";
                } else if (text === "admin") {
                    color = "red";
                }
                return <Tag color={color}>{text.toUpperCase()}</Tag>;
            }),
        },
        {
            title: "Token",
            dataIndex: "token",
            key: "token",
            width: 500,
            ...getColumnSearchProps("token", (text: string) => (
                <TokenRender token={text} />
            )),
        },
        {
            title: "Thời gian tạo",
            dataIndex: "createdAt",
            key: "createdAt",
            render: (text: string) => (
                <div className="flex items-center ml-2">
                    <span className="text-yellow-400 font-semibold">
                        {text}
                    </span>
                </div>
            ),
        },
        {
            title: "Thao tác",
            key: "action",
            render: (text: string, record: IToken) => (
                <Space
                    size="large"
                    className="flex gap-4 justify-center items-center w-full"
                >
                    <div className="cursor-pointer flex flex-row gap-4">
                        <Tooltip title={`Xóa token của: ${record.username}`}>
                            <Popconfirm
                                title="Xóa token ?"
                                description={`Xóa token của: ${record.username} ?`}
                                onConfirm={() =>
                                    new Promise(async (resolve) => {
                                        await deleteToken(record.id);
                                        resolve(null);
                                    })
                                }
                                okText="Xóa"
                                cancelText="Hủy"
                            >
                                <Trash2 size={16} color="red" />
                            </Popconfirm>
                        </Tooltip>
                    </div>
                </Space>
            ),
        },
    ];

    const successMessage = ({
        content,
        duration,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "success",
            content: content,
            duration: duration || 2,
        });
    };

    const errorMessage = ({
        content,
        duration,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "error",
            content: content,
            duration: duration || 2,
        });
    };

    const onFinishFailed: FormProps["onFinishFailed"] = (errorInfo) => {
        console.log("Failed:", errorInfo);
        form.resetFields();
    };

    const onFinish: FormProps["onFinish"] = async (
        values: ITokenFormValues
    ) => {
        const { username } = values;

        try {
            setLoadingRegister(true);
            const result = await fetch(
                `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/admin/create-token`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({
                        username,
                    }),
                }
            );

            const data = await result.json();

            if (!result.ok) {
                errorMessage({
                    content: data?.detail || "An unexpected error occurred",
                });
                return;
            }

            successMessage({
                content: `Tạo token cho ${username} thành công`,
                duration: 1,
            });

            setTokens((prev) => [
                {
                    key: data.id,
                    token: data.token,
                    role: data.role,
                    user_id: data.user_id,
                    username: data.username,
                    id: data.id,
                    createdAt: formatDate(data.created_at),
                    updatedAt: formatDate(data.updated_at),
                },
                ...prev,
            ]);
        } catch (error) {
            console.error(error);
            errorMessage({
                content: (error as string) || "An unexpected error occurred",
            });
        } finally {
            setOpen(false);
            setLoadingRegister(false);
            form.resetFields();
        }
    };

    const formItems = (
        <>
            <Form.Item
                name="username"
                rules={[
                    {
                        required: true,
                        message: "Please input your username!",
                    },
                ]}
                style={{
                    width: "100%",
                }}
            >
                <Input
                    autoFocus
                    prefix={<UserOutlined />}
                    placeholder="Username"
                />
            </Form.Item>
        </>
    );

    if (loadingPage) {
        return <LoadingSpinner />;
    }

    return (
        <div className="w-[90%] border shadow-sm rounded-lg mx-auto">
            {contextHolder}
            <div className="flex justify-around my-5">
                <span className="text-xl text-red-500 font-bold">
                    Quản lý token
                </span>
                <AddModal
                    open={open}
                    setOpen={setOpen}
                    loading={loadingRegister}
                    onFinish={onFinish}
                    form={form}
                    onFinishFailed={onFinishFailed}
                    buttonIcon={<Plus size={16} />}
                    buttonContent="Thêm token"
                    formTitle="Tạo mới token"
                    formItems={formItems}
                    submitButtonContent="Tạo token !!!"
                />
            </div>
            <Table<IToken> dataSource={tokens} columns={columns} />
        </div>
    );
};
export default ProtectedRoute(AdminTokenManagementPage);
