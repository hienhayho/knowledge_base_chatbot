"use client";
import { useEffect } from "react";
import { setCookie } from "cookies-next";
import React from "react";
import { Button, Form, Input } from "antd";
import { useSearchParams } from 'next/navigation'


const onFinish = async (values) => {
  const username = values.username;
  const password = values.password;

  const path = localStorage.getItem("redirectPath") || "/knowledge";

  const body = new URLSearchParams();
  body.append("grant_type", "password");
  body.append("username", username);
  body.append("password", password);
  body.append("scope", "");
  body.append("client_id", "client_id");
  body.append("client_secret", "client_secret");

  const result = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/users/login`,
      {
          method: "POST",
          headers: {
              "Content-Type": "application/x-www-form-urlencoded",
          },
          body: body.toString(),
      }
  );

  if (result.ok) {
      const data = await result.json();

      setCookie("access_token", data.access_token, {
          maxAge: 30 * 60,
          path: '/',
      });

      window.location.href = path;
  } else {
      console.error("Failed to login");
  }
};


const onFinishFailed = (errorInfo) => {
    console.log("Failed:", errorInfo);
};

const SignIn = () => {
    const searchParams = useSearchParams();

    useEffect(() => {
        const redirectPath = searchParams.get("redirect") || "/knowledge";
        localStorage.setItem("redirectPath", redirectPath);
    }, [searchParams]);


    return (
      <div style={styles.container}>
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

                <Form.Item wrapperCol={{ offset: 6, span: 18 }}>
                    <Button type="primary" htmlType="submit">
                        Submit
                    </Button>
                </Form.Item>
            </Form>

            <div style={styles.footer}>
              Don't have an account?
              <a href="/register" className="text-blue-500 block ml-4">Sign Up</a>
            </div>
        </div>
    </div>
    )
  };

const styles = {
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
    },
    footer: {
        textAlign: "center",
        marginTop: "16px",
    },
};

export default SignIn;
