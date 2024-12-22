import { INavItem } from "./types";

export const userNavItems: INavItem[] = [
    {
        name: "Knowledge Base",
        path: "/knowledge",
        description: "Trang chứa các knowledge base theo từng user.",
    },
    {
        name: "Chat",
        path: "/chat",
        description: "Trang chatbot giúp người dùng tương tác với hệ thống.",
    },
    {
        name: "Dashboard",
        path: "/dashboard",
        description: "Trang thống kê dữ liệu của từng user.",
    },
];

export const adminNavItems: INavItem[] = [
    {
        name: "Users",
        path: "/admin/users",
        description: "Trang để admin quản lý user.",
        feature: "Quản lý người dùng trong hệ thống (tạo, xóa người dùng)",
    },
    {
        name: "Tokens",
        path: "/admin/tokens",
        description: "Trang để admin quản lý các tokens không hết hạn.",
        feature:
            "Tạo và quản lý tokens dài hạn (không hết hạn), có thể loại bỏ khi cần thiết",
    },
];

export const dashboardNavItems: INavItem[] = [
    {
        name: "Statistic",
        path: "/dashboard",
        description: "Trang thống kê dữ liệu của từng user.",
    },
    {
        name: "Wordcloud",
        path: "/dashboard/wordcloud",
        description: "Trang hiển thị wordcloud của từng user.",
    },
    {
        name: "Knowledge Base",
        path: "/knowledge",
        description: "Trang chứa các knowledge base theo từng user.",
    },
];
