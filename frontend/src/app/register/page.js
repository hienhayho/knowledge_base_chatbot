"use client";
import React from "react";
import { Button, Form, Input } from "antd";

const onFinish = async (values) => {
    const username = values.username;
    const password = values.password;
    const email = values.email;
    const retypePassword = values.retypePassword;

    if (password !== retypePassword) {
        window.alert("Passwords do not match");
        return;
    }

    const result = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/users/create`,
        {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ username, email, password }),
        }
    );

    if (result.ok) {
        const data = await result.json();
        window.alert("Account created successfully");

        // Redirect to login page
        window.location.href = "/login";
    } else {
        console.error("Failed to login");
    }
};

const onFinishFailed = (errorInfo) => {
    console.log("Failed:", errorInfo);
};

const SignUp = () => (
    <div style={styles.container}>
        <div style={styles.formWrapper}>
            <h1 style={styles.header}>Sign Up</h1>
            <Form
                name="basic"
                labelCol={{ span: 6 }} // Adjusted for a larger layout
                wrapperCol={{ span: 18 }} // Adjusted for a larger layout
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
                    label="Email"
                    name="email"
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

                <Form.Item
                    label="Retype Password"
                    name="retypePassword"
                    rules={[
                        {
                            required: true,
                            message: "Please retype your password!",
                        },
                    ]}
                >
                    <Input.Password />
                </Form.Item>

                <Form.Item wrapperCol={{ offset: 6, span: 18 }}>
                    <Button type="primary" htmlType="submit">
                        Submit
                    </Button>
                </Form.Item>
            </Form>
        </div>
    </div>
);

const styles = {
    container: {
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        height: "100vh",
        backgroundColor: "#f0f2f5",
    },
    formWrapper: {
        padding: "32px", // Increased padding for a larger feel
        border: "1px solid #d9d9d9",
        borderRadius: "8px",
        backgroundColor: "#fff",
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.1)",
        maxWidth: "800px", // Increased max width for a larger form
        width: "100%", // Ensures the form takes full width up to the max width
    },
    header: {
        fontSize: "28px", // Slightly larger font for the header
        fontWeight: "bold",
        textAlign: "center",
        marginBottom: "32px", // Added more space below the header
    },
};

export default SignUp;
