import { INavItem } from "./types";

export const userNavItems: INavItem[] = [
    {
        name: "Knowledge Base",
        path: "/knowledge",
    },
    {
        name: "Chat",
        path: "/chat",
    },
    {
        name: "Dashboard",
        path: "/dashboard",
    },
];

export const adminNavItems: INavItem[] = [
    {
        name: "Users",
        path: "/admin/users",
    },
];

export const dashboardNavItems: INavItem[] = [
    { name: "Statistic", path: "/dashboard" },
    { name: "Wordcloud", path: "/dashboard/wordcloud" },
    { name: "Knowledge Base", path: "/knowledge" },
];
