"use client";

import React, { useEffect, Suspense } from "react";
import { setCookie } from "cookies-next";
import { Button, Form, Input, FormProps, message } from "antd";
import { ValidateErrorEntity } from "rc-field-form/lib/interface";
import { useSearchParams, useRouter } from "next/navigation";

interface LoginFormValues {
    username: string;
    password: string;
}

interface LoginResponse {
    access_token: string;
}

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
        marginTop: "16px",
    },
};

const SignInContent: React.FC = () => {
    const router = useRouter();
    const searchParams = useSearchParams();
    const [messageApi, contextHolder] = message.useMessage();

    useEffect(() => {
        const redirectPath = searchParams?.get("redirect") || "/knowledge";
        localStorage.setItem("redirectPath", redirectPath);
    }, [searchParams]);

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

    const onFinish: FormProps["onFinish"] = async (values: LoginFormValues) => {
        const { username, password } = values;

        const path = localStorage.getItem("redirectPath") || "/knowledge";

        const body = new URLSearchParams();
        body.append("grant_type", "password");
        body.append("username", username);
        body.append("password", password);
        body.append("scope", "");
        body.append("client_id", "client_id");
        body.append("client_secret", "client_secret");

        try {
            const response = await fetch(
                `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/users/login`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/x-www-form-urlencoded",
                    },
                    body: body.toString(),
                }
            );

            if (response.ok) {
                const data: LoginResponse = await response.json();

                setCookie("access_token", data.access_token, {
                    maxAge: 30 * 60,
                    path: "/",
                });

                successMessage({
                    content: "Login successful.",
                    duration: 1,
                });

                setTimeout(() => router.push(path), 1000);
            } else if (response.status === 401) {
                errorMessage({
                    content: "Invalid username or password.",
                });
            } else {
                errorMessage({
                    content: "An unexpected error occurred. Please try again.",
                });
            }
        } catch (error) {
            console.error("Login error:", error);
            errorMessage({
                content: "An unexpected error occurred. Please try again.",
                duration: 1,
            });
        }
    };

    const onFinishFailed: FormProps["onFinishFailed"] = (
        errorInfo: ValidateErrorEntity<LoginFormValues>
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
                <h1 style={styles.header}>Sign In</h1>
                <Form
                    name="basic"
                    labelCol={{ span: 6 }}
                    wrapperCol={{ span: 18 }}
                    initialValues={{ remember: true }}
                    onFinish={onFinish}
                    onFinishFailed={onFinishFailed}
                    autoComplete="off"
                >
                    <Form.Item
                        label="Username"
                        name="username"
                        rules={[
                            {
                                required: true,
                                message: "Please input your username!",
                            },
                        ]}
                    >
                        <Input />
                    </Form.Item>

                    <Form.Item
                        label="Password"
                        name="password"
                        rules={[
                            {
                                required: true,
                                message: "Please input your password!",
                            },
                        ]}
                    >
                        <Input.Password />
                    </Form.Item>

                    <div
                        style={{
                            display: "flex",
                            justifyContent: "space-evenly",
                        }}
                    >
                        <Form.Item wrapperCol={{ offset: 6, span: 18 }}>
                            <Button type="primary" htmlType="submit">
                                Login
                            </Button>
                        </Form.Item>

                        <div style={styles.footer}>
                            Don&apos;t have an account?&nbsp;
                            <a
                                href="/register"
                                className="text-blue-500 block ml-4"
                            >
                                Sign Up
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
