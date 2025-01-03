"use client";

import {
    IToken,
    ITokenResponse,
    ITokenFormValues,
    IAdminUserSelect,
    IUserResponse,
} from "@/types";
import {
    Form,
    FormProps,
    Input,
    message,
    Popconfirm,
    Select,
    Space,
    Table,
    Tag,
    Tooltip,
} from "antd";
import { useEffect, useState } from "react";
import LoadingSpinner from "@/components/LoadingSpinner";
import { Copy, Plus, Trash2 } from "lucide-react";
import AddModal from "@/components/admin/AddModal";
import ProtectedRoute from "@/components/ProtectedRoute";
import { formatDate } from "@/utils";
import TokenRender from "@/components/admin/TokenRender";
import { adminApi } from "@/api";
import { Key } from "antd/es/table/interface";

const AdminTokenManagementPage = () => {
    const [loadingPage, setLoadingPage] = useState(true);
    const [tokens, setTokens] = useState<IToken[]>([]);
    const [searchText, setSearchText] = useState("");
    const [usersSelect, setUsersSelect] = useState<IAdminUserSelect[]>([]);
    const [messageApi, contextHolder] = message.useMessage();
    const [open, setOpen] = useState<boolean>(false);
    const [loadingRegister, setLoadingRegister] = useState<boolean>(false);
    const [form] = Form.useForm();

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [tokensData, usersData] = await Promise.all([
                    await adminApi.fetchTokens(),
                    await adminApi.getUsers(),
                ]);

                messageApi.success("Lấy data thành công !");

                setUsersSelect(
                    usersData.map((user: IUserResponse) => ({
                        key: user.id,
                        value: user.username,
                        label: user.username,
                    }))
                );

                setTokens(
                    tokensData.map((token: ITokenResponse) => ({
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
                console.error("Lấy data thất bại", error);
                messageApi.error((error as Error).message);
            } finally {
                setLoadingPage(false);
            }
        };
        fetchData();
    }, []);

    const deleteToken = async (id: string) => {
        try {
            await adminApi.deleteToken(id);

            messageApi.success("Xóa token thành công !");
            setTokens((prev) => prev.filter((token) => token.id !== id));
        } catch (error) {
            console.error("Xóa token thất bại", error);
            messageApi.error((error as Error).message);
        }
    };

    const columns = [
        {
            title: "Tên đăng nhập",
            dataIndex: "username",
            key: "username",
            filteredValue: searchText ? [searchText] : null,
            onFilter: (value: Key | boolean, record: IToken) =>
                record.username
                    .toLowerCase()
                    .includes((value as string).toLowerCase()),

            render: (text: string) => (
                <div className="flex items-center ml-2">
                    <span className="text-cyan-500 font-semibold">{text}</span>
                </div>
            ),
        },
        {
            title: "Quyền",
            dataIndex: "role",
            key: "role",
            render: (text: string) => {
                let color;
                if (text === "user") {
                    color = "green";
                } else if (text === "admin") {
                    color = "red";
                }
                return <Tag color={color}>{text.toUpperCase()}</Tag>;
            },
        },
        {
            title: "Token",
            dataIndex: "token",
            key: "token",
            width: 500,
            render: (text: string) => <TokenRender token={text} />,
        },
        {
            title: "Thời gian tạo",
            dataIndex: "createdAt",
            key: "createdAt",
            render: (text: string) => (
                <div className="flex items-center ml-2">
                    <span className="text-gray-500 font-semibold">{text}</span>
                </div>
            ),
        },
        {
            title: "Thao tác",
            key: "action",
            render: (text: string, record: IToken) => (
                <Space
                    size="large"
                    className="flex gap-2 justify-center items-center w-full"
                >
                    <Tooltip title={<div>{"Sao chép token"}</div>}>
                        <button
                            type="button"
                            className="bg-transparent text-gray-500 p-4 rounded-full hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-300 disabled:opacity-50"
                            onClick={() => {
                                navigator.clipboard.writeText(record.token);
                                messageApi.open({
                                    type: "success",
                                    content: "Đã sao chép !",
                                    duration: 1.5,
                                });
                            }}
                        >
                            <Copy size={16} />
                        </button>
                    </Tooltip>
                    <div className="cursor-pointer flex flex-row gap-4">
                        <Tooltip title={`Xóa token của: ${record.username}`}>
                            <Popconfirm
                                title="Xóa token ?"
                                description={
                                    <span>
                                        Xóa token của:&nbsp;
                                        <span className="text-red-400 font-medium">
                                            {record.username}
                                        </span>
                                        &nbsp; ?
                                    </span>
                                }
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
            const data = await adminApi.createToken(username);

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
                <Select
                    showSearch
                    placeholder="Chọn user muốn tạo token"
                    style={{ width: "100%" }}
                    options={usersSelect}
                />
            </Form.Item>
        </>
    );

    if (loadingPage) {
        return <LoadingSpinner />;
    }

    return (
        <div className="w-[90%] max-w-7xl border shadow-sm rounded-lg mx-auto px-4 md:px-6">
            {contextHolder}
            <div className="flex flex-col md:flex-row flex-wrap justify-between md:justify-around items-center my-5 gap-4">
                <span className="text-lg md:text-xl text-red-500 font-bold text-center">
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
            <div className="overflow-x-auto">
                <div className="flex mb-2 w-full md:max-w-[40%]">
                    <Input.Search
                        placeholder="Tìm theo tên đăng nhập..."
                        onSearch={(value) => {
                            setSearchText(value);
                        }}
                        onChange={(e) => {
                            setSearchText(e.target.value);
                        }}
                    />
                </div>

                <Table<IToken>
                    dataSource={tokens}
                    columns={columns}
                    pagination={{
                        defaultPageSize: 10,
                        showSizeChanger: true,
                        pageSizeOptions: ["10", "20", "30"],
                    }}
                    scroll={{ x: "max-content", y: 55 * 8 }}
                />
            </div>
        </div>
    );
};
export default ProtectedRoute(AdminTokenManagementPage);
