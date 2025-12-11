import React, { useState } from 'react';
import { Upload, ArrowRight, Check, FileText, Loader2, AlertCircle, X } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useParams } from 'react-router-dom';

const API_URL = 'http://localhost:8001/api';

interface WQDataImportProps {
    onComplete: () => void;
    onError: (msg: string) => void;
}

interface DatasetResponse {
    dataset_id: number;
    headers: string[];
    filename: string;
    details: {
        detected_monitor_name?: string;
    };
}

const WQDataImport: React.FC<WQDataImportProps> = ({ onComplete, onError }) => {
    const { projectId } = useParams<{ projectId: string }>();
    const queryClient = useQueryClient();

    // Steps: 'upload' -> 'mapping' -> 'processing' -> 'success'
    const [step, setStep] = useState<'upload' | 'mapping' | 'processing' | 'success'>('upload');

    // Batch State
    const [files, setFiles] = useState<File[]>([]);
    const [uploadedDatasets, setUploadedDatasets] = useState<DatasetResponse[]>([]);
    const [mapping, setMapping] = useState<Record<string, string>>({});
    const [progress, setProgress] = useState<{ current: number, total: number }>({ current: 0, total: 0 });

    const [dragActive, setDragActive] = useState(false);

    // Standard variables to map to
    const STANDARD_VARS = ['Date', 'pH', 'Temperature', 'DO', 'DOSat', 'Turbidity', 'Conductivity', 'Ammonia', 'Flow'];

    // Drag and Drop Handlers
    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            setFiles(prev => [...prev, ...Array.from(e.dataTransfer.files)]);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFiles(prev => [...prev, ...Array.from(e.target.files || [])]);
        }
    };

    const removeFile = (index: number) => {
        setFiles(prev => prev.filter((_, i) => i !== index));
    };

    // 1. Bulk Upload
    const uploadMutation = useMutation({
        mutationFn: async () => {
            const results: DatasetResponse[] = [];
            for (const file of files) {
                const formData = new FormData();
                formData.append('file', file);
                const res = await axios.post(`${API_URL}/wq/projects/${projectId}/datasets/upload`, formData);
                results.push(res.data);
            }
            return results;
        },
        onSuccess: (data) => {
            setUploadedDatasets(data);
            setStep('mapping');

            // Init mapping using the FIRST file's headers
            if (data.length > 0) {
                const firstHeaders = data[0].headers;
                const initialMapping: Record<string, string> = {};
                STANDARD_VARS.forEach(std => {
                    const match = firstHeaders.find((h: string) => h.toLowerCase().includes(std.toLowerCase()));
                    if (match) initialMapping[std] = match;
                });
                setMapping(initialMapping);
            }
        },
        onError: (err: any) => {
            onError(err.response?.data?.detail || "Upload failed");
        }
    });

    // 2. Bulk Process
    const processMutation = useMutation({
        mutationFn: async () => {
            let completed = 0;
            setProgress({ current: 0, total: uploadedDatasets.length });

            for (const ds of uploadedDatasets) {
                const payload = {
                    mapping,
                    // Use detected name if available, otherwise filename fallback
                    monitor_name: ds.details?.detected_monitor_name || ds.filename.split('.')[0]
                };
                await axios.post(`${API_URL}/wq/datasets/${ds.dataset_id}/import`, payload);
                completed++;
                setProgress({ current: completed, total: uploadedDatasets.length });
            }
            return true;
        },
        onSuccess: () => {
            setStep('success');
            queryClient.invalidateQueries({ queryKey: ['wq-monitors', projectId] });
            setTimeout(onComplete, 2000);
        },
        onError: (err: any) => {
            onError(err.response?.data?.detail || "Some imports failed");
            // Stay on mapping or move to partial success?
            // For now, let user retry or cancel
            setStep('success'); // Show what we have? Or stay?
            setTimeout(onComplete, 2000);
        }
    });

    return (
        <div className="bg-white rounded-lg p-6 shadow-sm border border-gray-200">
            <h2 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Upload size={20} className="text-cyan-600" /> Import Data (Batch)
            </h2>

            {step === 'upload' && (
                <div className="space-y-4" onDragEnter={handleDrag}>
                    <div
                        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors relative ${dragActive ? 'border-cyan-500 bg-cyan-50' : 'border-gray-300 bg-gray-50 hover:bg-gray-100'
                            }`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                    >
                        <input
                            type="file"
                            accept=".csv"
                            multiple
                            onChange={handleFileChange}
                            className="hidden"
                            id="file-upload"
                        />
                        <label htmlFor="file-upload" className="cursor-pointer block w-full h-full">
                            <FileText size={48} className={`mx-auto mb-2 ${dragActive ? 'text-cyan-500' : 'text-gray-400'}`} />
                            <p className="text-gray-600 font-medium">Drag & Drop files here</p>
                            <p className="text-xs text-gray-400 mt-1">or click to select multiple .csv files</p>
                        </label>
                        {dragActive && (
                            <div className="absolute inset-0 bg-cyan-50/50 flex items-center justify-center pointer-events-none">
                                <p className="text-cyan-700 font-bold">Drop files here</p>
                            </div>
                        )}
                    </div>

                    {/* File List */}
                    {files.length > 0 && (
                        <div className="max-h-32 overflow-y-auto border rounded p-2 text-sm space-y-1">
                            {files.map((f, i) => (
                                <div key={i} className="flex justify-between items-center bg-gray-50 p-1.5 rounded">
                                    <span className="truncate flex-1">{f.name}</span>
                                    <button onClick={() => removeFile(i)} className="text-gray-400 hover:text-red-500 ml-2">
                                        <X size={14} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}

                    <div className="flex justify-end">
                        <button
                            disabled={files.length === 0 || uploadMutation.isPending}
                            onClick={() => uploadMutation.mutate()}
                            className="bg-cyan-600 text-white px-4 py-2 rounded-lg hover:bg-cyan-700 disabled:opacity-50 flex items-center gap-2"
                        >
                            {uploadMutation.isPending ? <Loader2 className="animate-spin" size={16} /> : <ArrowRight size={16} />}
                            Upload {files.length > 0 ? `${files.length} Files` : ''}
                        </button>
                    </div>
                </div>
            )}

            {step === 'mapping' && uploadedDatasets.length > 0 && (
                <div className="space-y-4">
                    <div className="bg-blue-50 border border-blue-200 rounded p-3 text-sm text-blue-800 flex items-start gap-2">
                        <AlertCircle size={16} className="mt-0.5 shrink-0" />
                        <div>
                            Defining mapping based on <strong>{uploadedDatasets[0].filename}</strong>.
                            <br />
                            This mapping will be applied to all <strong>{uploadedDatasets.length}</strong> uploaded files.
                        </div>
                    </div>

                    <div className="border rounded-lg overflow-hidden">
                        <table className="w-full text-sm">
                            <thead className="bg-gray-50">
                                <tr>
                                    <th className="p-2 text-left">Standard Variable</th>
                                    <th className="p-2 text-left">CSV Column ({uploadedDatasets[0].filename})</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-100">
                                {STANDARD_VARS.map(std => (
                                    <tr key={std}>
                                        <td className="p-2 font-medium">{std} {std === 'Date' && <span className="text-red-500">*</span>}</td>
                                        <td className="p-2">
                                            <select
                                                className="w-full border p-1 rounded"
                                                value={mapping[std] || ""}
                                                onChange={e => setMapping({ ...mapping, [std]: e.target.value })}
                                            >
                                                <option value="">-- Ignore --</option>
                                                {uploadedDatasets[0].headers.map(h => (
                                                    <option key={h} value={h}>{h}</option>
                                                ))}
                                            </select>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    <div className="flex justify-end gap-2">
                        <button onClick={() => setStep('upload')} className="px-4 py-2 text-gray-600">Back</button>
                        <button
                            onClick={() => { setStep('processing'); processMutation.mutate(); }}
                            disabled={!mapping['Date'] || processMutation.isPending}
                            className="bg-cyan-600 text-white px-4 py-2 rounded-lg hover:bg-cyan-700 disabled:opacity-50 flex items-center gap-2"
                        >
                            <Check size={16} />
                            Process Batch ({uploadedDatasets.length})
                        </button>
                    </div>
                    {!mapping['Date'] && (
                        <p className="text-xs text-red-500 text-right">Date mapping is required</p>
                    )}
                </div>
            )}

            {step === 'processing' && (
                <div className="text-center py-8">
                    <Loader2 className="animate-spin text-cyan-500 mx-auto mb-2" size={32} />
                    <p className="text-gray-500 font-medium mb-1">Processing Batch Import...</p>
                    <p className="text-sm text-gray-400">
                        {progress.current} / {progress.total} files processed
                    </p>
                </div>
            )}

            {step === 'success' && (
                <div className="text-center py-8 text-green-600">
                    <Check className="mx-auto mb-2" size={32} />
                    <p className="font-medium">Batch Import Successful!</p>
                </div>
            )}
        </div>
    );
};

export default WQDataImport;
