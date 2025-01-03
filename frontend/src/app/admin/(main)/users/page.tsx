"use client";

import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { useAuth } from "@/hooks/auth";
import {
    IAdminSwitchUserResponse,
    IUser,
    IUserResponse,
    SignUpFormValues,
} from "@/types";
import {
    Form,
    FormProps,
    Input,
    message,
    Popconfirm,
    Space,
    Table,
    Tag,
    Tooltip,
} from "antd";
import { useEffect, useState } from "react";
import LoadingSpinner from "@/components/LoadingSpinner";
import {
    Mail,
    Plus,
    Trash2,
    SendHorizontal,
    Info,
    PenLine,
} from "lucide-react";
import AddModal from "@/components/admin/AddModal";
import { adminApi, authApi } from "@/api";
import ProtectedRoute from "@/components/ProtectedRoute";
import { setCookie } from "cookies-next";
import { formatDate } from "@/utils";
import DetailToolTip from "@/components/DetailToolTip";
import EditUserModal from "@/components/admin/EditUser";
import { Key } from "antd/es/table/interface";

const AdminUserPage = () => {
    const { changeUser } = useAuth();
    const [loadingPage, setLoadingPage] = useState(true);
    const [users, setUsers] = useState<IUser[]>([]);
    const [searchText, setSearchText] = useState("");
    const [messageApi, contextHolder] = message.useMessage();
    const [open, setOpen] = useState<boolean>(false);
    const [loadingRegister, setLoadingRegister] = useState<boolean>(false);
    const [form] = Form.useForm();

    useEffect(() => {
        const fetchAllUser = async () => {
            try {
                const data = await adminApi.getUsers();

                messageApi.success("Lấy thông tin người dùng thành công");

                setUsers(
                    data.map((user: IUserResponse) => ({
                        key: user.id,
                        role: user.role,
                        username: user.username,
                        organization: user.organization,
                        id: user.id,
                        createdAt: formatDate(user.created_at),
                        updatedAt: formatDate(user.updated_at),
                    }))
                );
            } catch (error) {
                const errMessage = (error as Error).message;
                console.error("Lấy thông tin người dùng thất bại", error);
                messageApi.error(errMessage);
            } finally {
                setLoadingPage(false);
            }
        };
        fetchAllUser();
    }, []);

    const deleteUser = async (id: string) => {
        try {
            await adminApi.deleteUser(id);

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

    const columns = [
        {
            title: "Tên đăng nhập",
            dataIndex: "username",
            key: "username",
            filteredValue: searchText ? [searchText] : null,
            onFilter: (value: Key | boolean, record: IUser) => {
                return (
                    record.username
                        .toLowerCase()
                        .includes((value as string).toLowerCase()) ||
                    (record.organization &&
                        record.organization
                            .toLowerCase()
                            .includes((value as string).toLowerCase())) ||
                    record.role
                        .toLowerCase()
                        .includes((value as string).toLowerCase())
                );
            },

            render: (text: string) => (
                <div className="flex items-center ml-2">
                    <span className="text-cyan-500 font-semibold">{text}</span>
                </div>
            ),
        },
        {
            title: "Tổ chức",
            dataIndex: "organization",
            key: "organization",
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
                    <div className="cursor-pointer">
                        <EditUserModal
                            key={record.id}
                            icon={<PenLine size={16} />}
                            user={record}
                            allUsers={users}
                            setUsers={setUsers}
                        />
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
        const { username, email, password, retypePassword, organization } =
            values;

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
                organization: organization,
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
                    organization: result.data.organization,
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

            <div className="flex items-center gap-4 justify-center">
                <div className="w-[95%]">
                    <Form.Item
                        name="organization"
                        rules={[
                            {
                                required: true,
                                message: "Please input your organization!",
                            },
                        ]}
                        style={{
                            width: "100%",
                        }}
                    >
                        <Input autoFocus placeholder="Organization" />
                    </Form.Item>
                </div>
                <DetailToolTip
                    title="Sẽ được đưa vào câu chào mừng lúc tạo conversation mới (VNDC sẽ được xử lý riêng) ==> Xin chào anh/chị. Em là nhân viên hỗ trợ tư vấn của {organization}. Anh/chị cần giúp đỡ hoặc có câu hỏi gì không ạ ?"
                    icon={<Info size={16} />}
                />
            </div>
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
            <div className="overflow-x-auto">
                <div className="flex mb-2 w-full md:max-w-[40%]">
                    <Input.Search
                        placeholder="Tìm theo tên đăng nhập, tên công ty, quyền..."
                        onSearch={(value) => {
                            setSearchText(value);
                        }}
                        onChange={(e) => {
                            setSearchText(e.target.value);
                        }}
                    />
                </div>

                <Table<IUser>
                    dataSource={users}
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
export default ProtectedRoute(AdminUserPage);
