"use client";

import React, { useState, useEffect } from "react";
import {
    Search,
    Plus,
    FileText,
    Check,
    FileIcon,
    File,
    Download,
    Trash2,
    Play,
    CircleStop,
} from "lucide-react";
import UploadFileModal from "@/components/knowledge_base/UploadFileModal";
import LoadingSpinner from "@/components/LoadingSpinner";
import ErrorComponent from "@/components/Error";
import { useRouter } from "next/navigation";
import { message, Popconfirm, Tooltip } from "antd";
import { formatDate } from "@/utils";
import { useAuth } from "@/hooks/auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_BASE_API_URL;

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

interface Document {
    id: string;
    file_name: string;
    created_at: string;
    file_type: string;
    file_size_in_mb: number;
    status: string;
    progress?: number;
}

interface KnowledgeBase {
    name: string;
    documents: Document[];
}

interface IUploadFile {
    doc_id: string;
    file_name: string;
    file_type: string;
    file_size_in_mb: number;
    created_at: string;
    status: string;
}

const DatasetView: React.FC<{ knowledgeBaseID: string }> = ({
    knowledgeBaseID,
}) => {
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [knowledgeBase, setKnowledgeBase] = useState<KnowledgeBase | null>(
        null
    );
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [documents, setDocuments] = useState<Document[]>([]);

    const [messageApi, contextHolder] = message.useMessage();
    const router = useRouter();
    const { token } = useAuth();
    const redirectURL = encodeURIComponent(`/knowledge/${knowledgeBaseID}`);

    useEffect(() => {
        const fetchKnowledgeBase = async () => {
            try {
                const response = await fetch(
                    `${API_BASE_URL}/api/kb/get_kb/${knowledgeBaseID}`,
                    {
                        headers: {
                            Authorization: `Bearer ${token}`,
                        },
                    }
                );
                const data: KnowledgeBase = await response.json();
                if (!response.ok) {
                    throw new Error("Failed to fetch knowledge base data");
                }

                setKnowledgeBase(data);
                setDocuments(data.documents);
                setIsLoading(false);
            } catch (error) {
                console.error("Error fetching knowledge base data:", error);
                setError((error as Error).message);
                setIsLoading(false);
            }
        };

        fetchKnowledgeBase();
    }, [knowledgeBaseID, token, router, redirectURL]);

    useEffect(() => {
        const checkProcessingDocuments = async () => {
            if (!token) {
                errorMessage({
                    content: "Session expired. Please login again.",
                    duration: 3,
                });
                setTimeout(() => {
                    router.push(`/login?redirect=${redirectURL}`);
                }, 3000);
                return;
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
                            ? {
                                  ...doc,
                                  ...updatedStatus,
                              }
                            : doc;
                    })
                );
            }
        };

        const intervalId = setInterval(checkProcessingDocuments, 1000);

        return () => clearInterval(intervalId);
    }, [documents, token, redirectURL]);

    const successMessage = ({
        content,
        duration = 1,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "success",
            content: content,
            duration: duration,
        });
    };

    const errorMessage = ({
        content,
        duration = 1,
    }: {
        content: string;
        duration?: number;
    }) => {
        messageApi.open({
            type: "error",
            content: content,
            duration: duration,
        });
    };

    const handleUpload = async (files: FileList) => {
        if (!token) {
            window.location.href = `/login?redirect=${redirectURL}`;
            return;
        }
        for (const file of files) {
            const fileExtension =
                "." + file.name.split(".").pop()?.toLowerCase();
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
                    errorMessage({
                        content:
                            errorData.detail || "Failed to upload document",
                        duration: 3,
                    });
                    continue;
                }

                const result: IUploadFile = await response.json();
                setDocuments((prevDocuments) => [
                    ...prevDocuments,
                    {
                        id: result.doc_id,
                        file_name: file.name,
                        created_at: result.created_at,
                        file_type: result.file_type,
                        status: "uploaded",
                        file_size_in_mb: result.file_size_in_mb,
                    },
                ]);

                successMessage({
                    content: `File ${file.name} uploaded successfully`,
                });
            } catch (error) {
                console.error("Error uploading document:", error);
                errorMessage({
                    content: (error as Error).message,
                });
                setError((error as Error).message);
            }
        }
    };

    const handleDownloadDocument = async (
        documentId: string,
        fileName: string
    ) => {
        if (!token) {
            window.location.href = `/login?redirect=${redirectURL}`;
            return;
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
                errorMessage({
                    content: "Failed to download document",
                });
                return;
            }

            successMessage({
                content: `Get ${fileName} successfully !!!`,
            });

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
            errorMessage({
                content: (error as Error).message,
            });
            setError((error as Error).message);
        }
    };

    const handleDeleteDocument = async (documentId: string) => {
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/kb/delete_document/${documentId}`,
                {
                    method: "DELETE",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({ delete_to_retry: false }),
                }
            );
            if (!response.ok) {
                const errorData = await response.json();
                errorMessage({
                    content: errorData.detail || "Failed to delete document",
                });
                return;
            }

            successMessage({
                content: "Document deleted successfully",
            });

            setDocuments((prevDocuments) =>
                prevDocuments.filter((doc) => doc.id !== documentId)
            );
        } catch (error) {
            console.error("Error deleting document:", error);
            errorMessage({
                content: (error as Error).message,
            });
            setError((error as Error).message);
        }
    };

    const handleProcessDocument = async (documentId: string) => {
        if (!token) {
            const redirectURL = encodeURIComponent(
                `/knowledge/${knowledgeBaseID}`
            );
            router.push(`/login?redirect=${redirectURL}`);
            return;
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
                        ? {
                              ...doc,
                              status: "processing",
                          }
                        : doc
                )
            );
        } catch (error) {
            console.error("Error processing document:", error);
            errorMessage({
                content: (error as Error).message,
            });
            setError((error as Error).message);
        }
    };

    const handleStopProcessingDocument = async (documentId: string) => {
        if (!token) {
            const redirectURL = encodeURIComponent(
                `/knowledge/${knowledgeBaseID}`
            );
            router.push(`/login?redirect=${redirectURL}`);
            return;
        }
        try {
            const response = await fetch(
                `${API_BASE_URL}/api/kb/stop_processing/${documentId}`,
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
                    errorData.detail || "Failed to stop processing document"
                );
            }

            setDocuments((prevDocuments) =>
                prevDocuments.map((doc) =>
                    doc.id === documentId
                        ? {
                              ...doc,
                              status: "failed",
                          }
                        : doc
                )
            );
        } catch (error) {
            console.error("Error stopping processing document:", error);
            errorMessage({
                content: (error as Error).message,
            });
            setError((error as Error).message);
        }
    };

    const getFileIcon = (fileName: string) => {
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

    const handleRetryProcessingDocument = async (documentId: string) => {
        if (!token) {
            const redirectURL = encodeURIComponent(
                `/knowledge/${knowledgeBaseID}`
            );
            router.push(`/login?redirect=${redirectURL}`);
            return;
        }
        try {
            const deleteResponse = await fetch(
                `${API_BASE_URL}/api/kb/delete_document/${documentId}`,
                {
                    method: "DELETE",
                    headers: {
                        "Content-Type": "application/json",
                        Authorization: `Bearer ${token}`,
                    },
                    body: JSON.stringify({ delete_to_retry: true }),
                }
            );

            if (!deleteResponse.ok) {
                const errorData = await deleteResponse.json();
                errorMessage({
                    content:
                        errorData.detail || "Failed to clean up old document",
                });
                return;
            }

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
                errorMessage({
                    content:
                        errorData.detail ||
                        "Failed to retry processing document",
                });
                return;
            }

            setDocuments((prevDocuments) =>
                prevDocuments.map((doc) =>
                    doc.id === documentId
                        ? {
                              ...doc,
                              status: "processing",
                          }
                        : doc
                )
            );
        } catch (error) {
            console.error("Error retrying processing document:", error);
            errorMessage({
                content: (error as Error).message,
            });
            setError((error as Error).message);
        }
    };

    const truncateFileName = (fileName: string, maxLength = 80) => {
        if (fileName.length <= maxLength) return fileName;
        const extension = fileName.split(".").pop() || "";
        const nameWithoutExtension = fileName.slice(0, -(extension.length + 1));
        const truncatedName =
            nameWithoutExtension.slice(0, maxLength - 3 - extension.length) +
            "...";
        return truncatedName + "." + extension;
    };

    if (isLoading) return <LoadingSpinner />;
    if (error) return <ErrorComponent message={error} />;
    if (!knowledgeBase) return null;

    return (
        <div className="flex h-screen bg-gray-100">
            {contextHolder}
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
                </nav>
            </aside>

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
                    <div className="flex justify-end mb-4">
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
                            <col style={{ width: "25%" }} />
                            <col style={{ width: "15%" }} />
                            <col style={{ width: "15%" }} />
                            <col style={{ width: "20%" }} />
                            <col style={{ width: "15%" }} />
                            <col style={{ width: "10%" }} />
                        </colgroup>
                        <thead>
                            <tr className="text-left text-gray-600 bg-gray-100">
                                <th className="p-2">Name</th>
                                <th className="p-2">File Size (MB)</th>
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
                                        <td className="p-2">
                                            {Math.round(
                                                doc.file_size_in_mb * 100
                                            ) / 100}
                                        </td>
                                        <td className="p-2">{doc.file_type}</td>
                                        <td className="p-2">
                                            {formatDate(doc.created_at)}
                                        </td>
                                        <td className="p-2">
                                            {doc.status === "processing" &&
                                            doc.progress !== undefined ? (
                                                `Processing: ${doc.progress}%`
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
                                                    <Tooltip title="Process the document">
                                                        <button
                                                            onClick={() =>
                                                                handleProcessDocument(
                                                                    doc.id
                                                                )
                                                            }
                                                            className="text-blue-500 hover:text-blue-700"
                                                        >
                                                            <Play size={16} />
                                                        </button>
                                                    </Tooltip>
                                                    <Tooltip title="Download the document">
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
                                                            <Download
                                                                size={16}
                                                            />
                                                        </button>
                                                    </Tooltip>
                                                    <Tooltip title="Delete the document">
                                                        <Popconfirm
                                                            title="Delete this file"
                                                            description="Are you sure to delete this file?"
                                                            onConfirm={(e) => {
                                                                e?.preventDefault();
                                                                handleDeleteDocument(
                                                                    doc.id
                                                                );
                                                            }}
                                                            onCancel={(e) => {
                                                                e?.preventDefault();
                                                            }}
                                                            okText="Yes"
                                                            cancelText="No"
                                                        >
                                                            <button
                                                                className="text-red-500 hover:text-red-700"
                                                                title="Delete"
                                                            >
                                                                <Trash2
                                                                    size={16}
                                                                />
                                                            </button>
                                                        </Popconfirm>
                                                    </Tooltip>
                                                </div>
                                            ) : doc.status === "processing" ? (
                                                <div className="flex space-x-2">
                                                    <Tooltip title="Download the document">
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
                                                            <Download
                                                                size={16}
                                                            />
                                                        </button>
                                                    </Tooltip>
                                                    <Tooltip title="Stop processing...">
                                                        <button
                                                            onClick={() =>
                                                                handleStopProcessingDocument(
                                                                    doc.id
                                                                )
                                                            }
                                                            className="text-red-500 hover:text-red-700"
                                                            title="Stop processing"
                                                        >
                                                            <CircleStop
                                                                size={16}
                                                            />
                                                        </button>
                                                    </Tooltip>
                                                </div>
                                            ) : doc.status == "processed" ? (
                                                <div className="flex space-x-2">
                                                    <Tooltip title="Download the document">
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
                                                            <Download
                                                                size={16}
                                                            />
                                                        </button>
                                                    </Tooltip>
                                                    <Tooltip title="Delete the document">
                                                        <Popconfirm
                                                            title="Delete this file"
                                                            description="Are you sure to delete this file?"
                                                            onConfirm={(e) => {
                                                                e?.preventDefault();
                                                                handleDeleteDocument(
                                                                    doc.id
                                                                );
                                                            }}
                                                            onCancel={(e) => {
                                                                e?.preventDefault();
                                                            }}
                                                            okText="Yes"
                                                            cancelText="No"
                                                        >
                                                            <button
                                                                className="text-red-500 hover:text-red-700"
                                                                title="Delete"
                                                            >
                                                                <Trash2
                                                                    size={16}
                                                                />
                                                            </button>
                                                        </Popconfirm>
                                                    </Tooltip>
                                                </div>
                                            ) : (
                                                <div className="flex space-x-2">
                                                    <Tooltip title="Retry processing...">
                                                        <button
                                                            onClick={() =>
                                                                handleRetryProcessingDocument(
                                                                    doc.id
                                                                )
                                                            }
                                                            className="text-blue-500 hover:text-blue-700"
                                                            title="Download"
                                                        >
                                                            <Play size={16} />
                                                        </button>
                                                    </Tooltip>
                                                    <Tooltip title="Download the document">
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
                                                            <Download
                                                                size={16}
                                                            />
                                                        </button>
                                                    </Tooltip>
                                                    <Tooltip title="Delete the document">
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
                                                    </Tooltip>
                                                </div>
                                            )}
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td
                                        colSpan={5}
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
