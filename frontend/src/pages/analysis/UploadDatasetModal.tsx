import React, { useState } from 'react';
import { useUploadAnalysisDataset } from '../../api/hooks';
import { Loader2, Upload, AlertCircle, FileText } from 'lucide-react';

interface UploadDatasetModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: number;
}

const UploadDatasetModal: React.FC<UploadDatasetModalProps> = ({ isOpen, onClose, projectId }) => {
    const [files, setFiles] = useState<File[]>([]);
    const [datasetType, setDatasetType] = useState<'Rainfall' | 'Flow/Depth'>('Rainfall');
    const [error, setError] = useState<string | null>(null);

    const uploadMutation = useUploadAnalysisDataset();

    if (!isOpen) return null;

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files.length > 0) {
            setFiles(Array.from(e.target.files));
            setError(null);
        }
    };

    const hasStdFile = files.some(f => f.name.toLowerCase().endsWith('.std'));

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (files.length === 0) {
            setError('Please select at least one file.');
            return;
        }

        try {
            // Upload files sequentially
            for (const file of files) {
                const isStdFile = file.name.toLowerCase().endsWith('.std');
                await uploadMutation.mutateAsync({
                    projectId,
                    file,
                    datasetType: isStdFile ? datasetType : undefined
                });
            }
            onClose();
            setFiles([]);
            setDatasetType('Rainfall');
        } catch (err) {
            setError('Failed to upload one or more files. Please check the format.');
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold text-gray-900">Upload Dataset</h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                        &times;
                    </button>
                </div>

                {error && (
                    <div className="mb-4 p-3 bg-red-50 text-red-600 rounded-lg flex items-center text-sm">
                        <AlertCircle size={16} className="mr-2" />
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-purple-500 transition-colors cursor-pointer relative">
                        <input
                            type="file"
                            multiple
                            onChange={handleFileChange}
                            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                            accept=".r,.std,.fdv"
                        />
                        {files.length > 0 ? (
                            <div className="flex flex-col items-center text-purple-600">
                                <FileText size={48} className="mb-2" />
                                <span className="font-medium">
                                    {files.length === 1 ? files[0].name : `${files.length} files selected`}
                                </span>
                                <span className="text-xs text-gray-500 mt-1">
                                    {files.length === 1
                                        ? `${(files[0].size / 1024).toFixed(1)} KB`
                                        : `Total: ${(files.reduce((sum, f) => sum + f.size, 0) / 1024).toFixed(1)} KB`
                                    }
                                </span>
                            </div>
                        ) : (
                            <div className="flex flex-col items-center text-gray-500">
                                <Upload size={48} className="mb-2" />
                                <span className="font-medium">Click to upload or drag and drop</span>
                                <span className="text-xs mt-1">Supported: .R, .FDV, .STD (multiple files allowed)</span>
                            </div>
                        )}
                    </div>

                    {hasStdFile && (
                        <div className="space-y-2">
                            <label className="block text-sm font-medium text-gray-700">
                                Dataset Type
                            </label>
                            <select
                                value={datasetType}
                                onChange={(e) => setDatasetType(e.target.value as 'Rainfall' | 'Flow/Depth')}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            >
                                <option value="Rainfall">Rainfall Gauge</option>
                                <option value="Flow/Depth">Flow/Depth Monitor</option>
                            </select>
                            <p className="text-xs text-gray-500">
                                .STD files can contain either rainfall or flow data. This type will be applied to all .STD files.
                            </p>
                        </div>
                    )}

                    <div className="flex justify-end gap-3 mt-6">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={files.length === 0 || uploadMutation.isPending}
                            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 flex items-center"
                        >
                            {uploadMutation.isPending ? (
                                <>
                                    <Loader2 className="animate-spin mr-2" size={18} />
                                    Uploading {files.length} file{files.length > 1 ? 's' : ''}...
                                </>
                            ) : (
                                'Upload'
                            )}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default UploadDatasetModal;
