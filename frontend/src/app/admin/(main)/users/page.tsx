"use client";

import { LockOutlined, SearchOutlined, UserOutlined } from "@ant-design/icons";
import { useAuth } from "@/hooks/auth";
import {
    IAdminSwitchUserResponse,
    IUser,
    IUserResponse,
    SignUpFormValues,
} from "@/types";
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
import { Mail, Plus, Trash2, SendHorizontal } from "lucide-react";
import AddModal from "@/components/admin/AddModal";
import { adminApi, authApi } from "@/api";
import ProtectedRoute from "@/components/ProtectedRoute";
import { setCookie } from "cookies-next";
import { formatDate } from "@/utils";

type DataIndex = keyof IUser;

const AdminUserPage = () => {
    const { changeUser } = useAuth();
    const [loadingPage, setLoadingPage] = useState(true);
    const [users, setUsers] = useState<IUser[]>([]);
    const [searchText, setSearchText] = useState("");
    const [searchedColumn, setSearchedColumn] = useState("");
    const searchInput = useRef<InputRef>(null);
    const [messageApi, contextHolder] = message.useMessage();
    const [open, setOpen] = useState<boolean>(false);
    const [loadingRegister, setLoadingRegister] = useState<boolean>(false);
    const [form] = Form.useForm();

    useEffect(() => {
        const fetchAllUser = async () => {
            try {
                const respone = await fetch(
                    `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/admin/users`,
                    {
                        headers: {
                            "Content-Type": "application/json",
                        },
                        credentials: "include",
                    }
                );

                const data = await respone.json();

                if (!respone.ok) {
                    throw new Error(data.detail || "Failed to fetch users");
                }

                messageApi.success("Lấy thông tin người dùng thành công");

                setUsers(
                    data.map((user: IUserResponse) => ({
                        key: user.id,
                        role: user.role,
                        username: user.username,
                        id: user.id,
                        createdAt: formatDate(user.created_at),
                        updatedAt: formatDate(user.updated_at),
                    }))
                );
            } catch (error) {
                console.error("Lấy thông tin người dùng thất bại", error);
                messageApi.error((error as Error).message);
            } finally {
                setLoadingPage(false);
            }
        };
        fetchAllUser();
    }, []);

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

    const deleteUser = async (id: string) => {
        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/admin/users/${id}`,
                {
                    method: "DELETE",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    credentials: "include",
                }
            );

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || "Failed to delete user");
            }

            messageApi.success("Xóa người dùng thành công");
            setUsers(users.filter((user) => user.id !== id));
        } catch (error) {
            console.error("Xóa người dùng thất bại", error);
            messageApi.error((error as Error).message);
        }
    };

    const handleSwitchUser = async (username: string) => {
        try {
            messageApi.open({
                type: "loading",
                content: "Switching ...",
                duration: 0,
            });
            const data = (await adminApi.switchUser(
                username
            )) as IAdminSwitchUserResponse;

            messageApi.destroy();

            setCookie("CHATBOT_SSO", data.access_token, {
                expires: new Date(data.expires),
                path: "/",
            });
            changeUser(data.user);

            successMessage({
                content: `Switch to: ${username}`,
            });
        } catch (err) {
            console.error("Error switching user:", err);
            errorMessage({
                content: "Failed to switch user",
            });
        }
    };

    const getColumnSearchProps = (
        dataIndex: DataIndex,
        renderFunction?: (text: string) => JSX.Element
    ): TableColumnType<IUser> => ({
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

        render: (text) =>
            searchedColumn === dataIndex ? (
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
            ),
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
            render: (text: string, record: IUser) => (
                <Space
                    size="large"
                    className="flex gap-4 justify-center items-center w-full"
                >
                    <div className="cursor-pointer flex flex-row gap-4">
                        <Tooltip title="Chuyển tài khoản">
                            <Popconfirm
                                title="Chuyển tài khoản"
                                description={
                                    <span>
                                        Chuyển sang tài khoản:&nbsp;
                                        <span className="text-red-400 font-medium">
                                            {record.username}
                                        </span>
                                        &nbsp; ?
                                    </span>
                                }
                                onConfirm={() =>
                                    new Promise(async (resolve) => {
                                        await handleSwitchUser(record.username);
                                        resolve(null);
                                    })
                                }
                                okText="Chuyển"
                                cancelText="Hủy"
                            >
                                <SendHorizontal size={16} color="green" />
                            </Popconfirm>
                        </Tooltip>
                    </div>
                    <div className="cursor-pointer flex flex-row gap-4">
                        <Tooltip title={`Xóa: ${record.username}`}>
                            <Popconfirm
                                title="Xóa người dùng"
                                description={
                                    <span>
                                        Xác nhận xóa:&nbsp;
                                        <span className="text-red-400 font-medium">
                                            {record.username}
                                        </span>
                                        &nbsp; ?
                                    </span>
                                }
                                onConfirm={() =>
                                    new Promise(async (resolve) => {
                                        await deleteUser(record.id);
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
        values: SignUpFormValues
    ) => {
        const { username, email, password, retypePassword } = values;

        if (password !== retypePassword) {
            errorMessage({
                content: "Passwords do not match!",
            });
            return;
        }

        try {
            setLoadingRegister(true);
            const result = await authApi.register({
                username: username,
                email: email,
                password: password,
                retypePassword: retypePassword,
            });

            if (!result.success) {
                errorMessage({
                    content: result?.detail || "An unexpected error occurred",
                });
                return;
            }

            successMessage({
                content: `Account created successfully for ${result.data.username}.`,
                duration: 1.5,
            });
            setUsers((prev) => [
                {
                    key: result.data.id,
                    role: result.data.role,
                    username: result.data.username,
                    id: result.data.id,
                    createdAt: formatDate(result.data.createdAt),
                    updatedAt: formatDate(result.data.updatedAt),
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

            <Form.Item
                name="email"
                rules={[
                    {
                        required: true,
                        message: "Please input your email!",
                        type: "email",
                    },
                ]}
                style={{
                    width: "100%",
                }}
            >
                <Input prefix={<Mail size={16} />} placeholder="Email" />
            </Form.Item>

            <Form.Item
                name="password"
                rules={[
                    {
                        required: true,
                        message: "Please input your password!",
                    },
                    () => ({
                        validator(_, value) {
                            if (!value || value.length >= 6) {
                                return Promise.resolve();
                            }
                            return Promise.reject(
                                new Error(
                                    "Password must be at least 6 characters!"
                                )
                            );
                        },
                    }),
                ]}
                style={{
                    width: "100%",
                }}
            >
                <Input.Password
                    prefix={<LockOutlined />}
                    type="password"
                    placeholder="Password"
                />
            </Form.Item>

            <Form.Item
                name="retypePassword"
                dependencies={["password"]}
                rules={[
                    {
                        required: true,
                        message: "Please retype your password!",
                    },
                    ({ getFieldValue }) => ({
                        validator(_, value) {
                            if (!value || getFieldValue("password") === value) {
                                return Promise.resolve();
                            }
                            return Promise.reject(
                                new Error("Passwords do not match!")
                            );
                        },
                    }),
                ]}
                style={{
                    width: "100%",
                }}
            >
                <Input.Password
                    prefix={<LockOutlined />}
                    type="password"
                    placeholder="Retype password"
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
                    Người dùng
                </span>
                <AddModal
                    open={open}
                    setOpen={setOpen}
                    loading={loadingRegister}
                    onFinish={onFinish}
                    form={form}
                    onFinishFailed={onFinishFailed}
                    buttonIcon={<Plus size={16} />}
                    buttonContent="Thêm người dùng"
                    formTitle="Thêm người dùng mới"
                    formItems={formItems}
                    submitButtonContent="Đăng ký người dùng"
                />
            </div>
            <Table<IUser> dataSource={users} columns={columns} />
        </div>
    );
};
export default ProtectedRoute(AdminUserPage);
