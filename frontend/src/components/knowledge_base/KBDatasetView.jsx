"use client";

import React, { useState, useEffect } from "react";
import {
    Search,
    Plus,
    FileText,
    Settings,
    Check,
    FileIcon,
    File,
    Download,
    Trash2,
} from "lucide-react";
import UploadFileModal from "@/components/knowledge_base/UploadFileModal";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorComponent from "@/components/Error";
import { getCookie } from "cookies-next";
import { message } from 'antd';
import { useRouter } from "next/navigation";

const API_BASE_URL =
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

const ALLOWED_FILE_TYPES = [
    ".docx",
    ".hwp",
    ".pdf",
    ".epub",
    ".txt",
    ".html",
    ".htm",
    ".ipynb",
    ".md",
    ".mbox",
    ".pptx",
    ".csv",
    ".xlsx",
    ".xml",
    ".rtf",
    ".mp4",
];

const DatasetView = ({ knowledgeBaseID }) => {
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [knowledgeBase, setKnowledgeBase] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    const [documents, setDocuments] = useState([]);
    const router = useRouter();
    const token = getCookie("access_token");
    const redirectURL = encodeURIComponent(`/knowledge/${knowledgeBaseID}`);

    useEffect(() => {
        const fetchKnowledgeBase = async () => {
            const token = getCookie("access_token");

            if (!token) {
                router.push(`/login?redirect=${redirectURL}`);
                return;
            }
            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/kb/${knowledgeBaseID}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                if (!response.ok) {
                    throw new Error("Failed to fetch knowledge base data");
                }
                const data = await response.json();

                console.log(data);
                setKnowledgeBase(data);
                setDocuments(data.documents);
                setIsLoading(false);
            } catch (err) {
                setError(err.message);
                setIsLoading(false);
            }
        };

        fetchKnowledgeBase();
    }, [knowledgeBaseID]);

    useEffect(() => {
        const checkProcessingDocuments = async () => {
            const token = getCookie("access_token");
            if (!token) {
                window.location.href = `/login?redirect=${redirectURL}`;
            }
            const processingDocs = documents.filter(
                (doc) => doc.status === "processing"
            );
            if (processingDocs.length > 0) {
                const updatedStatuses = await Promise.all(
                    processingDocs.map(async (doc) => {
                        const response = await fetch(
                            `${API_BASE_URL}/api/kb/document_status/${doc.id}`,
                            {
                                headers: {
                                    Authorization: `Bearer ${token}`,
                                },
                            }
                        );
                        const status = await response.json();
                        return { id: doc.id, ...status };
                    })
                );

                setDocuments((prevDocs) =>
                    prevDocs.map((doc) => {
                        const updatedStatus = updatedStatuses.find(
                            (s) => s.id === doc.id
                        );
                        return updatedStatus
                            ? { ...doc, ...updatedStatus }
                            : doc;
                    })
                );
            }
        };

        const intervalId = setInterval(checkProcessingDocuments, 5000);

        return () => clearInterval(intervalId);
    }, [documents]);

    const handleUpload = async (files) => {
        const token = getCookie("access_token");
        if (!token) {
            window.location.href = `/login?redirect=${redirectURL}`;
        }
        for (const file of files) {
            const fileExtension =
                "." + file.name.split(".").pop().toLowerCase();
            if (!ALLOWED_FILE_TYPES.includes(fileExtension)) {
                setError(
                    `File type ${fileExtension} is not allowed. Allowed types are: ${ALLOWED_FILE_TYPES.join(
                        ", "
                    )}`
                );
                continue;
            }

            const formData = new FormData();
            formData.append("file", file);

            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/kb/upload?knowledge_base_id=${knowledgeBaseID}`,
                    {
                        method: "POST",
                        body: formData,
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(
                        errorData.detail || "Failed to upload document"
                    );
                }

                const result = await response.json();
                setDocuments((prevDocuments) => [
                    ...prevDocuments,
                    {
                        id: result.doc_id,
                        file_name: file.name,
                        created_at: result.created_at,
                        file_type: result.file_type,
                        status: "uploaded",
                    },
                ]);
            } catch (error) {
                console.error("Error uploading document:", error);
                setError(error.message);
            }
        }
    };

    const handleDownloadDocument = async (documentId, fileName) => {
        if (!token) {
            window.location.href = `/login?redirect=${redirectURL}`;
        }
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/kb/download/${documentId}`,
                {
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );
            if (!response.ok) {
                throw new Error("Failed to download document");
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (error) {
            console.error("Error downloading document:", error);
            setError(error.message);
        }
    };

    const handleDeleteDocument = async (documentId) => {
        if (window.confirm("Are you sure you want to delete this document?")) {
            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/kb/delete_document/${documentId}`,
                    {
                        method: "DELETE",
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                if (!response.ok) {
                    throw new Error("Failed to delete document");
                }
                setDocuments((prevDocuments) =>
                    prevDocuments.filter((doc) => doc.id !== documentId)
                );
            } catch (error) {
                console.error("Error deleting document:", error);
                setError(error.message);
            }
        }
    };

    const handleProcessDocument = async (documentId) => {
        const token = getCookie("access_token");
        if (!token) {
            const redirectURL = encodeURIComponent(
                `/knowledge/${knowledgeBaseID}`
            );
            window.location.href = `/login?redirect=${redirectURL}`;
        }
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/kb/process/${documentId}`,
                {
                    method: "POST",
                    headers: {
                        Authorization: `Bearer ${token}`,
                    },
                }
            );

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(
                    errorData.detail || "Failed to process document"
                );
            }

            setDocuments((prevDocuments) =>
                prevDocuments.map((doc) =>
                    doc.id === documentId
                        ? { ...doc, status: "processing" }
                        : doc
                )
            );
        } catch (error) {
            console.error("Error processing document:", error);
            setError(error.message);
        }
    };

    const getFileIcon = (fileName) => {
        if (fileName.endsWith(".pdf")) {
            return (
                <FileIcon
                    className="inline-block mr-2 text-red-500"
                    size={16}
                />
            );
        } else if (fileName.endsWith(".docx")) {
            return (
                <FileIcon
                    className="inline-block mr-2 text-blue-500"
                    size={16}
                />
            );
        } else {
            return (
                <File className="inline-block mr-2 text-gray-500" size={16} />
            );
        }
    };

    const truncateFileName = (fileName, maxLength = 80) => {
        if (fileName.length <= maxLength) return fileName;
        const extension = fileName.split(".").pop();
        const nameWithoutExtension = fileName.slice(0, -(extension.length + 1));
        const truncatedName =
            nameWithoutExtension.slice(0, maxLength - 3 - extension.length) +
            "...";
        return truncatedName + "." + extension;
    };

    if (isLoading) return <LoadingSpinner />;
    if (error) return <ErrorComponent message={error} />;

    return (
        <div className="flex h-screen bg-gray-100">
            <aside className="w-64 bg-white shadow-md">
                <div className="p-4">
                    <div className="w-10 h-10 bg-gray-200 rounded-full mb-4"></div>
                    <h2 className="text-xl font-semibold">
                        {knowledgeBase.name}
                    </h2>
                </div>
                <nav className="mt-6">
                    <a
                        href="#"
                        className="block py-2 px-4 bg-blue-100 text-blue-700 border-l-4 border-blue-700"
                    >
                        <FileText className="inline-block mr-2" size={20} />
                        Dataset
                    </a>

                    <a
                        href="#"
                        className="block py-2 px-4 text-gray-600 hover:bg-gray-100"
                    >
                        <Settings className="inline-block mr-2" size={20} />
                        Configuration
                    </a>
                </nav>
            </aside>

            {/* Main content */}
            <main className="flex-1 p-8">
                <div className="mb-4">
                    <h1 className="text-2xl font-bold">Dataset</h1>
                    <p className="text-sm text-gray-600">
                        Knowledge Base / Dataset
                    </p>
                </div>

                {error && (
                    <div
                        className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6"
                        role="alert"
                    >
                        <p className="font-bold">Error:</p>
                        <p>{error}</p>
                    </div>
                )}

                <div
                    className="bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-6"
                    role="alert"
                >
                    <p className="font-bold">Note:</p>
                    <p>
                        Questions and answers can only be answered after the
                        parsing is successful.
                    </p>
                </div>

                <div className="bg-white shadow rounded-lg p-6">
                    <div className="flex justify-between mb-4">
                        <button className="px-4 py-2 bg-gray-100 text-gray-700 rounded">
                            Bulk
                        </button>
                        <div className="flex">
                            <div className="relative mr-2">
                                <input
                                    type="text"
                                    placeholder="Search your files"
                                    className="pl-10 pr-4 py-2 border rounded-md"
                                />
                                <Search
                                    className="absolute left-3 top-2.5 text-gray-400"
                                    size={20}
                                />
                            </div>
                            <button
                                onClick={() => setIsUploadModalOpen(true)}
                                className="px-4 py-2 bg-blue-500 text-white rounded flex items-center"
                            >
                                <Plus size={20} className="mr-2" />
                                Add file
                            </button>
                        </div>
                    </div>
                    <table className="w-full">
                        <colgroup>
                            <col style={{ width: "40%" }} />
                            <col style={{ width: "15%" }} />
                            <col style={{ width: "20%" }} />
                            <col style={{ width: "15%" }} />
                            <col style={{ width: "10%" }} />
                        </colgroup>
                        <thead>
                            <tr className="text-left text-gray-600 bg-gray-100">
                                <th className="p-2">Name</th>
                                <th className="p-2">File Type</th>
                                <th className="p-2">Upload Date</th>
                                <th className="p-2">Status</th>
                                <th className="p-2">Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {documents.length > 0 ? (
                                documents.map((doc) => (
                                    <tr key={doc.id}>
                                        <td className="p-2">
                                            <div className="flex items-center">
                                                {getFileIcon(doc.file_name)}
                                                <span
                                                    title={doc.file_name}
                                                    className="truncate"
                                                >
                                                    {truncateFileName(
                                                        doc.file_name
                                                    )}
                                                </span>
                                            </div>
                                        </td>
                                        <td className="p-2">{doc.file_type}</td>
                                        <td className="p-2">
                                            {new Date(
                                                doc.created_at
                                            ).toLocaleString()}
                                        </td>
                                        <td className="p-2">
                                            {doc.status === "processing" &&
                                            doc.progress ? (
                                                `Processing (${doc.progress.current}/${doc.progress.total})`
                                            ) : doc.status === "processed" ? (
                                                <span className="flex items-center">
                                                    <Check
                                                        className="text-green-500 mr-1"
                                                        size={16}
                                                    />
                                                    Processed
                                                </span>
                                            ) : (
                                                doc.status
                                            )}
                                        </td>
                                        <td className="p-2">
                                            {doc.status === "uploaded" ? (
                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={() =>
                                                            handleProcessDocument(
                                                                doc.id
                                                            )
                                                        }
                                                        className="text-blue-500 hover:text-blue-700"
                                                    >
                                                        Process
                                                    </button>
                                                    <button
                                                        onClick={() =>
                                                            handleDeleteDocument(
                                                                doc.id
                                                            )
                                                        }
                                                        className="text-red-500 hover:text-red-700"
                                                        title="Delete"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            ) : (
                                                <div className="flex space-x-2">
                                                    <button
                                                        onClick={() =>
                                                            handleDownloadDocument(
                                                                doc.id,
                                                                doc.file_name
                                                            )
                                                        }
                                                        className="text-blue-500 hover:text-blue-700"
                                                        title="Download"
                                                    >
                                                        <Download size={16} />
                                                    </button>
                                                    <button
                                                        onClick={() =>
                                                            handleDeleteDocument(
                                                                doc.id
                                                            )
                                                        }
                                                        className="text-red-500 hover:text-red-700"
                                                        title="Delete"
                                                    >
                                                        <Trash2 size={16} />
                                                    </button>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td
                                        colSpan="5"
                                        className="text-center py-4"
                                    >
                                        <div className="flex flex-col items-center text-gray-400">
                                            <FileText size={48} />
                                            <p className="mt-2">No data</p>
                                        </div>
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </main>
            <UploadFileModal
                isOpen={isUploadModalOpen}
                onClose={() => setIsUploadModalOpen(false)}
                onUpload={handleUpload}
                allowedFileTypes={ALLOWED_FILE_TYPES}
            />
        </div>
    );
};

export default DatasetView;
