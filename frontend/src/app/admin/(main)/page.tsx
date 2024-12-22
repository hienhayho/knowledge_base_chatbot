"use client";

import ProtectedRoute from "@/components/ProtectedRoute";
import { adminNavItems } from "@/constants";

const AdminHomePage = () => {
    const features = adminNavItems
        .map((route) => route.feature)
        .filter(Boolean);

    return (
        <div className="w-[90%] max-w-6xl border shadow-md rounded-lg mx-auto p-8 bg-white">
            <h1 className="text-3xl font-extrabold mb-8 text-center text-red-500">
                Trang Quản Trị
            </h1>

            <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                Các trang hiện có:
            </h2>
            <div className="overflow-x-auto shadow-sm rounded-lg">
                <table className="min-w-full bg-gray-50 border border-gray-300 rounded-lg">
                    <thead className="bg-gray-100">
                        <tr>
                            <th className="px-6 py-4 text-left text-sm font-bold text-gray-600 uppercase tracking-wide border-b">
                                Các trang
                            </th>
                            <th className="px-6 py-4 text-left text-sm font-bold text-gray-600 uppercase tracking-wide border-b">
                                Mô tả
                            </th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {adminNavItems.map((route, index) => (
                            <tr key={index} className="hover:bg-gray-50">
                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-800">
                                    {route.name}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600">
                                    {route.description}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            {features.length > 0 && (
                <div className="mt-10">
                    <h2 className="text-2xl font-semibold mb-4 text-gray-700">
                        Giới thiệu
                    </h2>
                    <p className="text-gray-700 mb-6 leading-relaxed">
                        {"Chào mừng đến với trang quản trị. Đây là nơi bạn"}
                        &nbsp;
                        <span className="text-green-500">có thể:</span>
                    </p>
                    <ul className="list-disc list-inside text-gray-700 space-y-3 pl-6">
                        {features.map((feature) => (
                            <li className="flex items-center" key={feature}>
                                <span className="w-2 h-2 bg-red-500 rounded-full"></span>
                                <span className="ml-3">{feature}</span>
                            </li>
                        ))}
                    </ul>
                </div>
            )}
        </div>
    );
};

export default ProtectedRoute(AdminHomePage);
