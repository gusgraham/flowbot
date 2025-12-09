import React, { useState, useRef, useCallback } from 'react';
import { Upload, File, X, Loader2, CheckCircle, Trash2 } from 'lucide-react';
import { useSSDFiles, useSSDUpload, useDeleteSSDFile } from '../../api/hooks';

interface DataImportTabProps {
    projectId: number;
}

const DataImportTab: React.FC<DataImportTabProps> = ({ projectId }) => {
    const { data: files, isLoading } = useSSDFiles(projectId);
    const uploadMutation = useSSDUpload();
    const deleteFileMutation = useDeleteSSDFile();

    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFileSelect = (fileList: FileList | null) => {
        if (!fileList) return;
        const csvFiles = Array.from(fileList).filter(f => f.name.toLowerCase().endsWith('.csv'));
        setSelectedFiles(prev => [...prev, ...csvFiles]);
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        handleFileSelect(e.dataTransfer.files);
    }, []);

    const handleDragOver = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    }, []);

    const handleDragLeave = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    }, []);

    const removeSelectedFile = (index: number) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index));
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return;
        try {
            await uploadMutation.mutateAsync({ projectId, files: selectedFiles });
            setSelectedFiles([]);
        } catch (error) {
            console.error('Upload failed:', error);
        }
    };

    const handleDeleteFile = async (filename: string) => {
        try {
            await deleteFileMutation.mutateAsync({ projectId, filename });
        } catch (error) {
            console.error('Delete failed:', error);
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-32">
                <Loader2 className="animate-spin text-orange-500" size={24} />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Hidden file input */}
            <input
                ref={fileInputRef}
                type="file"
                multiple
                accept=".csv"
                className="hidden"
                onChange={(e) => handleFileSelect(e.target.files)}
            />

            {/* Drop zone */}
            <div
                onClick={() => fileInputRef.current?.click()}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                className={`border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition ${isDragging
                        ? 'border-orange-500 bg-orange-50'
                        : 'border-gray-300 hover:border-orange-400 bg-gray-50 hover:bg-orange-50/50'
                    }`}
            >
                <Upload className={`mx-auto mb-3 ${isDragging ? 'text-orange-500' : 'text-gray-400'}`} size={40} />
                <p className="text-gray-600 font-medium">
                    {isDragging ? 'Drop files here' : 'Click to browse or drag CSV files'}
                </p>
                <p className="text-sm text-gray-400 mt-1">
                    InfoWorks ICM time-series exports (flow, depth, rainfall)
                </p>
            </div>

            {/* Selected files to upload */}
            {selectedFiles.length > 0 && (
                <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
                    <h3 className="text-sm font-medium text-orange-800 mb-3">Ready to upload ({selectedFiles.length})</h3>
                    <div className="space-y-2 mb-4">
                        {selectedFiles.map((file, index) => (
                            <div key={`${file.name}-${index}`} className="flex items-center justify-between bg-white border border-orange-200 rounded-lg px-3 py-2">
                                <div className="flex items-center gap-2">
                                    <File size={16} className="text-orange-500" />
                                    <span className="text-sm text-gray-700">{file.name}</span>
                                    <span className="text-xs text-gray-400">({(file.size / 1024).toFixed(1)} KB)</span>
                                </div>
                                <button onClick={() => removeSelectedFile(index)} className="text-gray-400 hover:text-red-500">
                                    <X size={16} />
                                </button>
                            </div>
                        ))}
                    </div>
                    <button
                        onClick={handleUpload}
                        disabled={uploadMutation.isPending}
                        className="w-full bg-orange-600 text-white py-2.5 rounded-lg hover:bg-orange-700 transition disabled:opacity-50 flex items-center justify-center gap-2 font-medium"
                    >
                        {uploadMutation.isPending ? <Loader2 className="animate-spin" size={18} /> : <Upload size={18} />}
                        Upload {selectedFiles.length} File{selectedFiles.length > 1 ? 's' : ''}
                    </button>
                </div>
            )}

            {/* Uploaded files list */}
            {files && files.length > 0 && (
                <div>
                    <h3 className="text-sm font-semibold text-gray-900 mb-3">Uploaded Data Files ({files.length})</h3>
                    <div className="space-y-2">
                        {files.map((file) => (
                            <div key={file.filename} className="flex items-center justify-between bg-green-50 border border-green-200 rounded-lg px-4 py-3">
                                <div className="flex items-center gap-3">
                                    <CheckCircle size={18} className="text-green-500" />
                                    <div>
                                        <span className="text-sm font-medium text-gray-700">{file.filename}</span>
                                        <span className="text-xs text-gray-400 ml-2">({(file.size_bytes / 1024).toFixed(1)} KB)</span>
                                    </div>
                                </div>
                                <button
                                    onClick={() => handleDeleteFile(file.filename)}
                                    disabled={deleteFileMutation.isPending}
                                    className="text-gray-400 hover:text-red-500 p-1.5 hover:bg-red-50 rounded transition"
                                    title="Delete file"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {(!files || files.length === 0) && selectedFiles.length === 0 && (
                <div className="text-center py-8 text-gray-400">
                    <p>No data files uploaded yet.</p>
                    <p className="text-sm mt-1">Upload CSV exports from InfoWorks ICM to begin analysis.</p>
                </div>
            )}
        </div>
    );
};

export default DataImportTab;
