"use client";

import React, { useState } from "react";
import { Button, Form, Input, FormProps, message } from "antd";
import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { useRouter } from "next/navigation";
import { Mail } from "lucide-react";
import { SignUpFormValues } from "@/types";
import { authApi } from "@/api";

const SignUp: React.FC = () => {
    const router = useRouter();
    const [messageApi, contextHolder] = message.useMessage();
    const [loading, setLoading] = useState<boolean>(false);

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
            setLoading(true);
            const result = await authApi.register({
                username: username,
                email: email,
                password: password,
                retypePassword: retypePassword,
                admin_access_token: "",
            });

            if (!result.success) {
                errorMessage({
                    content: result?.detail || "An unexpected error occurred",
                });
                return;
            }

            successMessage({
                content: `Account created successfully for ${result.data.username}. Please login again.`,
                duration: 1.5,
            });

            setTimeout(() => {
                router.push("/login");
            }, 1500);
        } catch (error) {
            console.error(error);
            errorMessage({
                content: (error as string) || "An unexpected error occurred",
            });
        } finally {
            setLoading(false);
        }
    };

    const onFinishFailed: FormProps["onFinishFailed"] = (errorInfo) => {
        console.log("Failed:", errorInfo);
    };

    return (
        <div style={styles.container}>
            {contextHolder}
            <div style={styles.formWrapper}>
                <h1 style={styles.header}>Register</h1>
                <Form
                    name="basic"
                    style={{
                        display: "flex",
                        flexDirection: "column",
                        alignItems: "center",
                        width: "100%",
                    }}
                    initialValues={{ remember: true }}
                    onFinish={onFinish}
                    onFinishFailed={onFinishFailed}
                    autoComplete="off"
                >
                    <Form.Item
                        name="username"
                        rules={[
                            {
                                required: true,
                                message: "Please input your username!",
                            },
                        ]}
                        style={{
                            width: "80%",
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
                            width: "80%",
                        }}
                    >
                        <Input
                            prefix={<Mail size={16} />}
                            placeholder="Email"
                        />
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
                            width: "80%",
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
                                    if (
                                        !value ||
                                        getFieldValue("password") === value
                                    ) {
                                        return Promise.resolve();
                                    }
                                    return Promise.reject(
                                        new Error("Passwords do not match!")
                                    );
                                },
                            }),
                        ]}
                        style={{
                            width: "80%",
                        }}
                    >
                        <Input.Password
                            prefix={<LockOutlined />}
                            type="password"
                            placeholder="Retype password"
                        />
                    </Form.Item>

                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-evenly",
                            width: "100%",
                        }}
                    >
                        <Form.Item wrapperCol={{ offset: 6, span: 18 }}>
                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={loading}
                            >
                                Register
                            </Button>
                        </Form.Item>
                        <div style={styles.footer}>
                            Already have an account?&nbsp;
                            <a
                                href="/login"
                                className="text-blue-500 block ml-4"
                            >
                                Log In
                            </a>
                        </div>
                    </div>
                </Form>
            </div>
        </div>
    );
};

const styles: Record<string, React.CSSProperties> = {
    container: {
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        backgroundColor: "#f0f2f5",
    },
    formWrapper: {
        padding: "32px",
        border: "1px solid #d9d9d9",
        borderRadius: "8px",
        backgroundColor: "#fff",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
        maxWidth: "800px",
        width: "100%",
    },
    header: {
        fontSize: "28px",
        fontWeight: "bold",
        textAlign: "center",
        marginBottom: "32px",
        color: "rgb(239 68 68)",
    },
    footer: {
        textAlign: "right",
        marginTop: "0.5rem",
    },
};

export default SignUp;
