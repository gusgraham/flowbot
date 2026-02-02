import React, { useState, useEffect, useMemo } from 'react';
import { X, Loader2, Download, CheckSquare, Square } from 'lucide-react';
import { useExportDWF } from '../../api/hooks';

interface DWFExportModalProps {
    isOpen: boolean;
    onClose: () => void;
    projectId: number;
    datasets: { id: number; name: string }[];
}

const DWFExportModal: React.FC<DWFExportModalProps> = ({ isOpen, onClose, projectId, datasets }) => {
    const sortedDatasets = useMemo(() => {
        return [...datasets].sort((a, b) => a.name.localeCompare(b.name));
    }, [datasets]);

    const [selectedDatasetIds, setSelectedDatasetIds] = useState<number[]>([]);
    const [variable, setVariable] = useState<string>('All');
    const [startDate, setStartDate] = useState<string>(new Date().toISOString().split('T')[0] + 'T00:00');

    // Export options (SG filter uses per-monitor saved settings)
    const [profileLine, setProfileLine] = useState<string>('mean');
    const [format, setFormat] = useState<string>('infoworks');

    const exportMutation = useExportDWF();

    useEffect(() => {
        if (isOpen) {
            setSelectedDatasetIds(datasets.map(d => d.id));
        }
    }, [isOpen, datasets]);

    if (!isOpen) return null;

    const toggleDataset = (id: number) => {
        setSelectedDatasetIds(prev =>
            prev.includes(id) ? prev.filter(d => d !== id) : [...prev, id]
        );
    };

    const toggleAll = () => {
        if (selectedDatasetIds.length === datasets.length) {
            setSelectedDatasetIds([]);
        } else {
            setSelectedDatasetIds(datasets.map(d => d.id));
        }
    };

    const handleExport = async () => {
        if (selectedDatasetIds.length === 0) return;

        const variablesToExport = variable === 'All'
            ? ['Flow', 'Depth', 'Velocity']
            : [variable];

        try {
            for (const v of variablesToExport) {
                const data = await exportMutation.mutateAsync({
                    projectId,
                    datasetIds: selectedDatasetIds,
                    startDate: startDate,
                    variable: v,
                    profileLine,
                    format
                });

                // Trigger download
                const url = window.URL.createObjectURL(new Blob([data]));
                const link = document.createElement('a');
                link.href = url;
                const suffix = format === 'generic' ? 'Generic' : v;
                link.setAttribute('download', `DWF_Export_${suffix}.csv`);
                document.body.appendChild(link);
                link.click();
                link.remove();
                window.URL.revokeObjectURL(url);
            }

            onClose();
        } catch (error) {
            console.error("Export failed", error);
        }
    };

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-xl w-full max-w-lg p-6 max-h-[90vh] flex flex-col">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold text-gray-900">Export DWF Profiles</h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
                        <X size={24} />
                    </button>
                </div>

                <div className="space-y-6 flex-1 overflow-y-auto">
                    {/* Format Selection */}
                    <div className="flex gap-4">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="radio"
                                name="format"
                                value="infoworks"
                                checked={format === 'infoworks'}
                                onChange={(e) => setFormat(e.target.value)}
                                className="text-purple-600 focus:ring-purple-500"
                            />
                            <span className="text-sm text-gray-700">InfoWorks Format</span>
                        </label>
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="radio"
                                name="format"
                                value="generic"
                                checked={format === 'generic'}
                                onChange={(e) => setFormat(e.target.value)}
                                className="text-purple-600 focus:ring-purple-500"
                            />
                            <span className="text-sm text-gray-700">Generic CSV</span>
                        </label>
                    </div>

                    {/* Settings Row 1 */}
                    <div className="grid grid-cols-3 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Variable</label>
                            <select
                                value={variable}
                                onChange={(e) => setVariable(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
                            >
                                <option value="All">All</option>
                                <option value="Flow">Flow</option>
                                <option value="Depth">Depth</option>
                                <option value="Velocity">Velocity</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Profile Line</label>
                            <select
                                value={profileLine}
                                onChange={(e) => setProfileLine(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
                            >
                                <option value="mean">Average</option>
                                <option value="min">Minimum</option>
                                <option value="max">Maximum</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Start Date</label>
                            <input
                                type="datetime-local"
                                value={startDate}
                                onChange={(e) => setStartDate(e.target.value)}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-purple-500 text-sm"
                            />
                        </div>
                    </div>

                    {/* Note: SG filter uses each monitor's saved settings */}
                    <p className="text-xs text-gray-500 italic">SG filter uses each monitor's saved settings</p>

                    {/* Datasets Selection */}
                    <div>
                        <div className="flex justify-between items-center mb-2">
                            <label className="block text-sm font-medium text-gray-700">Select Monitors</label>
                            <button
                                onClick={toggleAll}
                                className="text-xs text-purple-600 hover:text-purple-700 font-medium"
                            >
                                {selectedDatasetIds.length === datasets.length ? 'Deselect All' : 'Select All'}
                            </button>
                        </div>
                        <div className="border border-gray-200 rounded-lg overflow-y-auto max-h-60">
                            {sortedDatasets.map(d => (
                                <div
                                    key={d.id}
                                    onClick={() => toggleDataset(d.id)}
                                    className="px-3 py-2 border-b border-gray-100 last:border-0 hover:bg-gray-50 cursor-pointer flex items-center gap-2"
                                >
                                    {selectedDatasetIds.includes(d.id) ? (
                                        <CheckSquare size={16} className="text-purple-600" />
                                    ) : (
                                        <Square size={16} className="text-gray-300" />
                                    )}
                                    <span className="text-sm text-gray-700">{d.name}</span>
                                </div>
                            ))}
                        </div>
                        <p className="text-xs text-gray-500 mt-1">
                            Selected: {selectedDatasetIds.length} monitors
                        </p>
                    </div>
                </div>

                <div className="flex justify-end space-x-3 mt-6 pt-4 border-t border-gray-100">
                    <button
                        type="button"
                        onClick={onClose}
                        className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        onClick={handleExport}
                        disabled={exportMutation.isPending || selectedDatasetIds.length === 0}
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {exportMutation.isPending ? <Loader2 className="animate-spin mr-2" size={18} /> : <Download className="mr-2" size={18} />}
                        Export CSV
                    </button>
                </div>
            </div>
        </div>
    );
};

export default DWFExportModal;
