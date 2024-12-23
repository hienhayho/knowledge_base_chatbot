"use client";

import React, { Suspense, useState } from "react";
import { Button, Form, Input, FormProps, message } from "antd";
import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { ValidateErrorEntity } from "rc-field-form/lib/interface";
import { useSearchParams, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/auth";
import { ILoginFormValues } from "@/types";

const styles: Record<string, React.CSSProperties> = {
    container: {
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        backgroundColor: "#f0f2f5",
    },
    formWrapper: {
        padding: "16px",
        border: "1px solid #d9d9d9",
        borderRadius: "8px",
        backgroundColor: "#fff",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
        maxWidth: "600px",
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

const SignInContent: React.FC = () => {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [messageApi, contextHolder] = message.useMessage();
    const [loading, setLoading] = useState<boolean>(false);
    const redirectPath = searchParams?.get("redirect") || "/knowledge";
    const { login } = useAuth();

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
        values: ILoginFormValues
    ) => {
        const { username, password } = values;

        const body = new URLSearchParams();
        body.append("grant_type", "password");
        body.append("username", username);
        body.append("password", password);
        body.append("scope", "");
        body.append("client_id", "client_id");
        body.append("client_secret", "client_secret");

        try {
            setLoading(true);
            const userData = await login(body);

            successMessage({
                content: `Login successful`,
                duration: 1.5,
            });

            setTimeout(() => {
                if (userData.role === "admin") {
                    router.push("/admin");
                    return;
                }
                router.push(redirectPath);
            }, 1000);
        } catch (error) {
            console.error("Login error:", error);
            errorMessage({
                content:
                    (error as Error).message ||
                    "An unexpected error occurred. Please try again.",
                duration: 1,
            });
        } finally {
            setLoading(false);
        }
    };

    const onFinishFailed: FormProps["onFinishFailed"] = (
        errorInfo: ValidateErrorEntity<ILoginFormValues>
    ) => {
        console.error("Failed:", errorInfo);
        errorMessage({
            content: `Some fields are missing or invalid, ${errorInfo.errorFields.map(
                (field) => field.name
            )}`,
        });
    };

    return (
        <div style={styles.container}>
            {contextHolder}
            <div style={styles.formWrapper}>
                <h1 style={styles.header}>Login</h1>
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
                        name="password"
                        rules={[
                            {
                                required: true,
                                message: "Please input your password!",
                            },
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

                    <div
                        style={{
                            width: "100%",
                            display: "flex",
                            justifyContent: "space-evenly",
                        }}
                    >
                        <Form.Item wrapperCol={{ offset: 6, span: 18 }}>
                            <Button
                                type="primary"
                                htmlType="submit"
                                loading={loading}
                            >
                                Login
                            </Button>
                        </Form.Item>

                        <div style={styles.footer}>
                            Don&apos;t have an account?&nbsp;
                            <a
                                href="/register"
                                className="text-blue-500 block ml-4"
                            >
                                Register
                            </a>
                        </div>
                    </div>
                </Form>
            </div>
        </div>
    );
};

const SignIn: React.FC = () => {
    return (
        <Suspense fallback={<div>Loading...</div>}>
            <SignInContent />
        </Suspense>
    );
};

export default SignIn;
