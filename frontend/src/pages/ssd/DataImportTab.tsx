import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Upload, File, X, Loader2, CheckCircle, Trash2, Calendar, Settings, AlertTriangle } from 'lucide-react';
import { useSSDFiles, useSSDUpload, useDeleteSSDFile, useDetectDateFormat, useUpdateDateFormat } from '../../api/hooks';

interface DataImportTabProps {
    projectId: number;
}

const DataImportTab: React.FC<DataImportTabProps> = ({ projectId }) => {
    const { data: files, isLoading } = useSSDFiles(projectId);
    const { data: dateDetection, refetch: refetchDateDetection } = useDetectDateFormat(projectId);
    const uploadMutation = useSSDUpload();
    const deleteFileMutation = useDeleteSSDFile();
    const updateDateFormatMutation = useUpdateDateFormat();

    const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
    const [isDragging, setIsDragging] = useState(false);
    const [showFormatConfig, setShowFormatConfig] = useState(false);
    const [customFormat, setCustomFormat] = useState('');

    const fileInputRef = useRef<HTMLInputElement>(null);

    // Refresh detection when files change
    useEffect(() => {
        if (files && files.length > 0) {
            refetchDateDetection();
        }
    }, [files, refetchDateDetection]);

    // Initialize custom format input from current setting
    useEffect(() => {
        if (dateDetection?.current_format) {
            setCustomFormat(dateDetection.current_format);
        } else if (dateDetection?.detected_format) {
            setCustomFormat(dateDetection.detected_format);
        }
    }, [dateDetection]);

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
            // Backend detection happens on GET request, so just refetching is enough
            setTimeout(() => refetchDateDetection(), 500);
        } catch (error) {
            console.error('Upload failed:', error);
        }
    };

    const handleDeleteFile = async (filename: string) => {
        try {
            await deleteFileMutation.mutateAsync({ projectId, filename });
            // Refetch after deletion
            setTimeout(() => refetchDateDetection(), 500);
        } catch (error) {
            console.error('Delete failed:', error);
        }
    };

    const handleUpdateFormat = async (format: string | null) => {
        try {
            await updateDateFormatMutation.mutateAsync({ projectId, dateFormat: format });
            setShowFormatConfig(false);
            refetchDateDetection();
        } catch (error) {
            console.error('Failed to update date format:', error);
        }
    };

    const commonFormats = [
        { label: 'Auto-detect (dayfirst)', value: null },
        { label: 'DD/MM/YYYY HH:mm:ss', value: '%d/%m/%Y %H:%M:%S' },
        { label: 'DD-MM-YY HH:mm', value: '%d-%m-%y %H:%M' },
        { label: 'DD/MM/YYYY HH:mm', value: '%d/%m/%Y %H:%M' },
        { label: 'YYYY-MM-DD HH:mm:ss', value: '%Y-%m-%d %H:%M:%S' },
        { label: 'DD/MM/YY HH:mm:ss', value: '%d/%m/%y %H:%M:%S' },
    ];

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

            {/* Date Format Configuration */}
            {files && files.length > 0 && dateDetection && (
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-5">
                    <div className="flex items-start justify-between">
                        <div className="flex gap-3">
                            <Calendar className="text-blue-500 mt-1" size={20} />
                            <div>
                                <h3 className="font-semibold text-gray-900">Date Format Configuration</h3>
                                <p className="text-sm text-gray-600 mt-1">
                                    {dateDetection.current_format
                                        ? <span className="flex items-center gap-2">
                                            Using configured format:
                                            <span className="font-mono bg-blue-100 px-1 rounded">{dateDetection.current_format}</span>
                                        </span>
                                        : dateDetection.can_auto_parse
                                            ? <span className="text-green-700 flex items-center gap-1.5 font-medium">
                                                <CheckCircle size={15} />
                                                Fast auto-detection supported - manual configuration not required
                                            </span>
                                            : dateDetection.detected_format
                                                ? <span className="text-green-700 flex items-center gap-1.5 font-medium">
                                                    <CheckCircle size={15} />
                                                    <span>Detected optimal format: <span className="font-mono bg-green-100 px-1 rounded text-green-800">{dateDetection.detected_format}</span> - manual configuration not required</span>
                                                </span>
                                                : <span className="text-amber-700 flex items-center gap-1.5 font-medium">
                                                    <AlertTriangle size={15} />
                                                    Complex format detected - manual configuration recommended for speed
                                                </span>
                                    }
                                </p>
                            </div>
                        </div>
                        <button
                            onClick={() => setShowFormatConfig(!showFormatConfig)}
                            className="bg-white border border-gray-300 text-gray-700 px-3 py-1.5 rounded-lg text-sm font-medium hover:bg-gray-50 flex items-center gap-2"
                        >
                            <Settings size={16} />
                            Configure
                        </button>
                    </div>

                    {showFormatConfig && (
                        <div className="mt-4 pt-4 border-t border-blue-200">
                            <h4 className="text-sm font-medium text-gray-900 mb-2">Sample Dates from File:</h4>
                            <div className="bg-gray-900 text-gray-300 p-3 rounded-lg font-mono text-xs mb-4">
                                {dateDetection.sample_dates.length > 0
                                    ? dateDetection.sample_dates.slice(0, 3).map((d, i) => <div key={i}>{d}</div>)
                                    : <span className="text-gray-500">No sample dates available</span>
                                }
                            </div>

                            <h4 className="text-sm font-medium text-gray-900 mb-2">Select Format:</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-4">
                                {commonFormats.map((fmt, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleUpdateFormat(fmt.value)}
                                        className={`text-left px-3 py-2 rounded-lg text-sm border ${(dateDetection.current_format === fmt.value)
                                            ? 'bg-blue-100 border-blue-300 text-blue-800'
                                            : 'bg-white border-gray-200 hover:border-blue-300 text-gray-700'
                                            }`}
                                    >
                                        <div className="font-medium">{fmt.label}</div>
                                        {fmt.value && <div className="text-xs text-gray-500 font-mono">{fmt.value}</div>}
                                    </button>
                                ))}
                            </div>

                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    placeholder="Or enter custom format..."
                                    value={customFormat}
                                    onChange={(e) => setCustomFormat(e.target.value)}
                                    className="flex-1 text-sm border border-gray-300 rounded-lg px-3 py-2"
                                />
                                <button
                                    onClick={() => handleUpdateFormat(customFormat || null)}
                                    className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700"
                                >
                                    Save Custom
                                </button>
                            </div>
                            <p className="text-xs text-gray-500 mt-2">
                                Specifying an explicit format significantly improves CSV parsing speed compared to auto-detection (dateutil).
                            </p>
                        </div>
                    )}
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
