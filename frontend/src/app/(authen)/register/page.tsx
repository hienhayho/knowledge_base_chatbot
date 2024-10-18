"use client";

import React from "react";
import { Button, Form, Input, FormProps, message } from "antd";
import { useRouter } from "next/navigation";

interface SignUpFormValues {
    username: string;
    email: string;
    password: string;
    retypePassword: string;
}

interface SignUpResponse {
    username: string;
    detail?: string;
}

const SignUp: React.FC = () => {
    const router = useRouter();
    const [messageApi, contextHolder] = message.useMessage();

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
            const result = await fetch(
                `${process.env.NEXT_PUBLIC_BASE_API_URL}/api/users/create`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ username, email, password }),
                }
            );

            const data: SignUpResponse = await result.json();
            if (result.ok) {
                successMessage({
                    content: `Account created successfully for ${data.username}`,
                    duration: 1,
                });

                setTimeout(() => {
                    router.push("/login");
                }, 1000);
            } else {
                errorMessage({
                    content: data.detail || "An unexpected error occurred",
                });
            }
        } catch (error) {
            console.error(error);
            errorMessage({
                content: "An unexpected error occurred",
            });
        }
    };

    const onFinishFailed: FormProps["onFinishFailed"] = (errorInfo) => {
        console.log("Failed:", errorInfo);
    };

    return (
        <div style={styles.container}>
            {contextHolder}
            <div style={styles.formWrapper}>
                <h1 style={styles.header}>Sign Up</h1>
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
                        <Input autoFocus />
                    </Form.Item>

                    <Form.Item
                        label="Email"
                        name="email"
                        rules={[
                            {
                                required: true,
                                message: "Please input your email!",
                                type: "email",
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
                    >
                        <Input.Password />
                    </Form.Item>

                    <Form.Item
                        label="Retype Password"
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

// Styles object with TypeScript typing
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

export default SignUp;
