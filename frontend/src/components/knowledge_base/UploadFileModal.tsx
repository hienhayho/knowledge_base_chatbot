import React, { useState, useCallback } from "react";
import { useDropzone, FileRejection, DropzoneOptions } from "react-dropzone";
import { X, Upload, FileIcon, Trash2 } from "lucide-react";

interface UploadFileModalProps {
    isOpen: boolean;
    onClose: () => void;
    onUpload: (files: FileList) => Promise<void>;
    allowedFileTypes: string[];
}

const UploadFileModal: React.FC<UploadFileModalProps> = ({
    isOpen,
    onClose,
    onUpload,
    allowedFileTypes,
}) => {
    const [files, setFiles] = useState<File[]>([]);
    const [uploading, setUploading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    const onDrop = useCallback(
        (acceptedFiles: File[], rejectedFiles: FileRejection[]) => {
            setFiles((prevFiles) => [...prevFiles, ...acceptedFiles]);
            if (rejectedFiles.length > 0) {
                setError(
                    `Some files were rejected. Allowed types are: ${allowedFileTypes.join(
                        ", "
                    )}`
                );
            } else {
                setError(null);
            }
        },
        [allowedFileTypes]
    );

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: allowedFileTypes.reduce<Record<string, string[]>>(
            (acc, type) => {
                acc[type] = [];
                return acc;
            },
            {}
        ),
        multiple: true,
    } as DropzoneOptions);

    if (!isOpen) return null;

    const handleUpload = async () => {
        setUploading(true);
        const dataTransfer = new DataTransfer();
        files.forEach((file) => {
            dataTransfer.items.add(file);
        });
        await onUpload(dataTransfer.files);
        setUploading(false);
        setFiles([]);
        onClose();
    };

    const removeFile = (index: number) => {
        setFiles((prevFiles) => prevFiles.filter((_, i) => i !== index));
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-start pt-16">
            <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl">
                <div className="flex justify-between items-center p-6 border-b">
                    <h2 className="text-xl font-semibold">Upload Files</h2>
                    <button
                        onClick={onClose}
                        className="text-gray-400 hover:text-gray-600"
                    >
                        <X size={24} />
                    </button>
                </div>
                <div className="p-6">
                    <div className="flex space-x-4 mb-4">
                        <button className="px-4 py-2 bg-blue-100 text-blue-700 rounded">
                            File
                        </button>
                        <button className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded">
                            Directory
                        </button>
                    </div>
                    <div
                        {...getRootProps()}
                        className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer"
                    >
                        <input {...getInputProps()} />
                        <Upload
                            className="mx-auto text-gray-400 mb-4"
                            size={48}
                        />
                        {isDragActive ? (
                            <p>Drop the files here ...</p>
                        ) : (
                            <p>Click or drag files to this area to upload</p>
                        )}
                        <p className="text-sm text-gray-500 mt-2">
                            Support for multiple file upload. Strictly
                            prohibited from uploading company data or other
                            banned files.
                        </p>
                        <p className="text-sm text-gray-500 mt-2">
                            Allowed file types: {allowedFileTypes.join(", ")}
                        </p>
                    </div>
                    {error && <p className="text-red-500 mt-2">{error}</p>}
                    {files.length > 0 && (
                        <div className="mt-4">
                            {files.map((file, index) => (
                                <div
                                    key={`${file.name}-${index}`}
                                    className="flex items-center justify-between text-sm text-gray-600 my-1"
                                >
                                    <div className="flex items-center">
                                        <FileIcon size={16} className="mr-2" />
                                        {file.name}
                                    </div>
                                    <button
                                        onClick={() => removeFile(index)}
                                        className="text-red-500 hover:text-red-700"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                <div className="flex justify-end space-x-2 p-6 border-t">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded"
                        disabled={uploading}
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleUpload}
                        className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                        disabled={files.length === 0 || uploading}
                    >
                        {uploading ? "Uploading..." : "Upload"}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default UploadFileModal;
