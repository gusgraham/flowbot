import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAnalysisProject, useAnalysisDatasets, useRainfallEvents, useDeleteAnalysisDataset } from '../../api/hooks';
import { ArrowLeft, CloudRain, Activity, Droplets, Loader2, Upload, FileText, Trash2, ChevronDown, LineChart as LineChartIcon } from 'lucide-react';
import { cn } from '../../lib/utils';
import UploadDatasetModal from './UploadDatasetModal';
import FDVChart from './FDVChart';
import DataEditor from './DataEditor';
import ScatterChart from './ScatterChart';
import { CumulativeDepthChart } from './CumulativeDepthChart';

const RainfallTab = ({ datasetId }: { datasetId: number }) => {
    const { data: events, isLoading } = useRainfallEvents(datasetId);

    if (isLoading) return <div className="animate-pulse h-32 bg-gray-50 rounded-lg"></div>;

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-900">Detected Rainfall Events</h3>
            <div className="overflow-hidden border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Depth (mm)</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Peak Intensity (mm/hr)</th>
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                        {events?.map((event: any) => (
                            <tr key={event.event_id}>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                    {new Date(event.start_time).toLocaleString()}
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                    {event.duration_hours} hrs
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{event.total_mm.toFixed(2)}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{event.peak_intensity?.toFixed(2) || '-'}</td>
                            </tr>
                        ))}
                        {events?.length === 0 && (
                            <tr>
                                <td colSpan={4} className="px-6 py-12 text-center text-gray-500">
                                    No rainfall events detected.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

const DWFTab = ({ datasetId }: { datasetId: number }) => (
    <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-dashed border-gray-300">
        <p className="text-gray-500">Dry Weather Flow Analysis Coming Soon</p>
    </div>
);

const AnalysisWorkbench: React.FC = () => {
    const { projectId } = useParams<{ projectId: string }>();
    const id = parseInt(projectId || '0');

    const { data: project } = useAnalysisProject(id);
    const { data: datasets } = useAnalysisDatasets(id);
    const deleteDataset = useDeleteAnalysisDataset();

    // State for selection
    const [selectedDatasetIds, setSelectedDatasetIds] = useState<number[]>([]);
    const [activeTab, setActiveTab] = useState<'rainfall' | 'data-editor' | 'timeseries' | 'scatter' | 'dwf' | 'cumulative-depth'>('rainfall');
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [rainfallExpanded, setRainfallExpanded] = useState(true);
    const [flowExpanded, setFlowExpanded] = useState(true);

    // Group datasets by type
    const rainfallDatasets = datasets?.filter(d => d.variable === 'Rainfall') || [];
    const flowDatasets = datasets?.filter(d => d.variable === 'Flow/Depth' || d.variable === 'Flow') || [];

    // Auto-select first dataset if available and none selected
    React.useEffect(() => {
        if (datasets && datasets.length > 0 && selectedDatasetIds.length === 0) {
            setSelectedDatasetIds([datasets[0].id]);
        }
    }, [datasets]);

    // Handle dataset deletion
    const handleDeleteDataset = (datasetId: number, datasetName: string) => {
        if (window.confirm(`Are  you sure you want to delete "${datasetName}"? This action cannot be undone.`)) {
            deleteDataset.mutate(datasetId, {
                onSuccess: () => {
                    // Remove from selection if selected
                    setSelectedDatasetIds(prev => prev.filter(id => id !== datasetId));
                }
            });
        }
    };

    // Toggle dataset selection
    const toggleDatasetSelection = (datasetId: number) => {
        setSelectedDatasetIds(prev => {
            if (prev.includes(datasetId)) {
                return prev.filter(id => id !== datasetId);
            } else {
                return [...prev, datasetId];
            }
        });
    };

    // Determine available tabs based on dataset type
    const selectedDatasets = datasets?.filter(d => selectedDatasetIds.includes(d.id)) || [];
    const hasRainfall = selectedDatasets.some(d => d.variable === 'Rainfall');
    const hasFlow = selectedDatasets.some(d => d.variable === 'Flow/Depth' || d.variable === 'Flow');

    if (!project) return <div className="p-8"><Loader2 className="animate-spin" /></div>;

    return (
        <div className="h-[calc(100vh-8rem)] flex flex-col">
            <div className="mb-6 flex justify-between items-start">
                <div>
                    <Link to="/analysis" className="inline-flex items-center text-sm text-gray-500 hover:text-gray-900 mb-2">
                        <ArrowLeft size={16} className="mr-1" /> Back to Projects
                    </Link>
                    <h1 className="text-2xl font-bold text-gray-900">{project.name} - Analysis Workbench</h1>
                </div>
                <button
                    onClick={() => setIsUploadModalOpen(true)}
                    className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center"
                >
                    <Upload size={18} className="mr-2" />
                    Upload Dataset
                </button>
            </div>

            <div className="flex-1 flex gap-6 overflow-hidden">
                {/* Sidebar: Datasets */}
                <div className="w-72 bg-white border border-gray-200 rounded-xl flex flex-col overflow-hidden">
                    <div className="p-4 border-b border-gray-200 bg-gray-50">
                        <h3 className="font-semibold text-gray-700">Datasets</h3>
                    </div>
                    <div className="flex-1 overflow-y-auto p-2 space-y-3">
                        {datasets?.length === 0 ? (
                            <div className="text-center py-8 px-4 text-gray-500 text-sm">
                                <FileText size={32} className="mx-auto mb-2 opacity-20" />
                                <p>No datasets uploaded yet.</p>
                                <button
                                    onClick={() => setIsUploadModalOpen(true)}
                                    className="text-purple-600 hover:text-purple-700 mt-2 font-medium"
                                >
                                    Upload one now
                                </button>
                            </div>
                        ) : (
                            <>
                                {/* Rainfall Datasets Section */}
                                {rainfallDatasets.length > 0 && (
                                    <div>
                                        <button
                                            onClick={() => setRainfallExpanded(!rainfallExpanded)}
                                            className="w-full flex items-center justify-between px-2 py-1.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
                                        >
                                            <div className="flex items-center gap-2">
                                                <CloudRain size={16} className="text-blue-600" />
                                                <span>Rainfall Gauges</span>
                                                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                                                    {rainfallDatasets.length}
                                                </span>
                                            </div>
                                            <ChevronDown
                                                size={16}
                                                className={cn(
                                                    "transition-transform",
                                                    rainfallExpanded ? "rotate-180" : ""
                                                )}
                                            />
                                        </button>
                                        {rainfallExpanded && (
                                            <div className="mt-1 space-y-1">
                                                {rainfallDatasets.map(dataset => (
                                                    <div
                                                        key={dataset.id}
                                                        className={cn(
                                                            "text-left p-3 rounded-lg border transition-all flex items-start gap-3 group",
                                                            selectedDatasetIds.includes(dataset.id)
                                                                ? "bg-purple-50 border-purple-200 shadow-sm"
                                                                : "bg-white border-transparent hover:bg-gray-50 hover:border-gray-200"
                                                        )}
                                                    >
                                                        <div className="pt-1">
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedDatasetIds.includes(dataset.id)}
                                                                onChange={() => toggleDatasetSelection(dataset.id)}
                                                                className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded cursor-pointer"
                                                            />
                                                        </div>
                                                        <button
                                                            onClick={() => toggleDatasetSelection(dataset.id)}
                                                            className="flex items-start gap-3 flex-1 min-w-0 text-left"
                                                        >
                                                            <div className="p-2 rounded-md flex-shrink-0 bg-blue-100 text-blue-600">
                                                                <CloudRain size={16} />
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <p className={cn(
                                                                    "font-medium truncate text-sm",
                                                                    selectedDatasetIds.includes(dataset.id) ? "text-purple-900" : "text-gray-900"
                                                                )}>
                                                                    {dataset.name}
                                                                </p>
                                                                <p className="text-xs text-gray-500 truncate">
                                                                    {new Date(dataset.created_at).toLocaleDateString()}
                                                                </p>
                                                            </div>
                                                        </button>
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleDeleteDataset(dataset.id, dataset.name);
                                                            }}
                                                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors opacity-0 group-hover:opacity-100 flex-shrink-0"
                                                            title="Delete dataset"
                                                        >
                                                            <Trash2 size={14} />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}

                                {/* Flow/Depth Datasets Section */}
                                {flowDatasets.length > 0 && (
                                    <div>
                                        <button
                                            onClick={() => setFlowExpanded(!flowExpanded)}
                                            className="w-full flex items-center justify-between px-2 py-1.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
                                        >
                                            <div className="flex items-center gap-2">
                                                <Activity size={16} className="text-green-600" />
                                                <span>Flow Monitors</span>
                                                <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full">
                                                    {flowDatasets.length}
                                                </span>
                                            </div>
                                            <ChevronDown
                                                size={16}
                                                className={cn(
                                                    "transition-transform",
                                                    flowExpanded ? "rotate-180" : ""
                                                )}
                                            />
                                        </button>
                                        {flowExpanded && (
                                            <div className="mt-1 space-y-1">
                                                {flowDatasets.map(dataset => (
                                                    <div
                                                        key={dataset.id}
                                                        className={cn(
                                                            "text-left p-3 rounded-lg border transition-all flex items-start gap-3 group",
                                                            selectedDatasetIds.includes(dataset.id)
                                                                ? "bg-purple-50 border-purple-200 shadow-sm"
                                                                : "bg-white border-transparent hover:bg-gray-50 hover:border-gray-200"
                                                        )}
                                                    >
                                                        <div className="pt-1">
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedDatasetIds.includes(dataset.id)}
                                                                onChange={() => toggleDatasetSelection(dataset.id)}
                                                                className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded cursor-pointer"
                                                            />
                                                        </div>
                                                        <button
                                                            onClick={() => toggleDatasetSelection(dataset.id)}
                                                            className="flex items-start gap-3 flex-1 min-w-0 text-left"
                                                        >
                                                            <div className="p-2 rounded-md flex-shrink-0 bg-green-100 text-green-600">
                                                                <Activity size={16} />
                                                            </div>
                                                            <div className="flex-1 min-w-0">
                                                                <p className={cn(
                                                                    "font-medium truncate text-sm",
                                                                    selectedDatasetIds.includes(dataset.id) ? "text-purple-900" : "text-gray-900"
                                                                )}>
                                                                    {dataset.name}
                                                                </p>
                                                                <p className="text-xs text-gray-500 truncate">
                                                                    {new Date(dataset.created_at).toLocaleDateString()}
                                                                </p>
                                                            </div>
                                                        </button>
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                handleDeleteDataset(dataset.id, dataset.name);
                                                            }}
                                                            className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors opacity-0 group-hover:opacity-100 flex-shrink-0"
                                                            title="Delete dataset"
                                                        >
                                                            <Trash2 size={14} />
                                                        </button>
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </>
                        )}
                    </div>
                </div>

                {/* Main Content: Tabs */}
                <div className="flex-1 bg-white border border-gray-200 rounded-xl flex flex-col overflow-hidden">
                    {selectedDatasetIds.length > 0 ? (
                        <>
                            <div className="border-b border-gray-200">
                                <nav className="flex -mb-px">
                                    {hasRainfall && (
                                        <>
                                            <button
                                                onClick={() => setActiveTab('rainfall')}
                                                className={cn(
                                                    "flex-1 py-4 px-1 text-center border-b-2 font-medium text-sm flex items-center justify-center gap-2",
                                                    activeTab === 'rainfall'
                                                        ? "border-blue-500 text-blue-600"
                                                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                                )}
                                            >
                                                <CloudRain size={18} /> Rainfall Analysis
                                            </button>
                                            <button
                                                onClick={() => setActiveTab('cumulative-depth')}
                                                className={cn(
                                                    "flex-1 py-4 px-1 text-center border-b-2 font-medium text-sm flex items-center justify-center gap-2",
                                                    activeTab === 'cumulative-depth'
                                                        ? "border-blue-500 text-blue-600"
                                                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                                )}
                                            >
                                                <LineChartIcon size={18} /> Cumulative Depth
                                            </button>
                                        </>
                                    )}
                                    {hasFlow && (
                                        <>
                                            <button
                                                onClick={() => setActiveTab('data-editor')}
                                                className={cn(
                                                    "flex-1 py-4 px-1 text-center border-b-2 font-medium text-sm flex items-center justify-center gap-2",
                                                    activeTab === 'data-editor'
                                                        ? "border-blue-500 text-blue-600"
                                                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                                )}
                                            >
                                                <FileText size={18} /> Data Editor
                                            </button>
                                            <button
                                                onClick={() => setActiveTab('timeseries')}
                                                className={cn(
                                                    "flex-1 py-4 px-1 text-center border-b-2 font-medium text-sm flex items-center justify-center gap-2",
                                                    activeTab === 'timeseries'
                                                        ? "border-blue-500 text-blue-600"
                                                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                                )}
                                            >
                                                <LineChartIcon size={18} /> Time Series
                                            </button>
                                            <button
                                                onClick={() => setActiveTab('scatter')}
                                                className={cn(
                                                    "flex-1 py-4 px-1 text-center border-b-2 font-medium text-sm flex items-center justify-center gap-2",
                                                    activeTab === 'scatter'
                                                        ? "border-blue-500 text-blue-600"
                                                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                                )}
                                            >
                                                <Activity size={18} /> Scatter Graph
                                            </button>
                                            <button
                                                onClick={() => setActiveTab('dwf')}
                                                className={cn(
                                                    "flex-1 py-4 px-1 text-center border-b-2 font-medium text-sm flex items-center justify-center gap-2",
                                                    activeTab === 'dwf'
                                                        ? "border-blue-500 text-blue-600"
                                                        : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                                )}
                                            >
                                                <Droplets size={18} /> Dry Weather Flow
                                            </button>
                                        </>
                                    )}
                                </nav>
                            </div>

                            <div className="p-6 flex-1 overflow-y-auto">
                                {hasRainfall && activeTab === 'rainfall' && <RainfallTab datasetId={selectedDatasetIds[0]} />}
                                {hasRainfall && activeTab === 'cumulative-depth' && (
                                    <CumulativeDepthChart
                                        datasetIds={selectedDatasetIds.filter(id => {
                                            const d = datasets?.find(ds => ds.id === id);
                                            return d?.variable === 'Rainfall';
                                        })}
                                        datasets={datasets || []}
                                    />
                                )}
                                {hasFlow && activeTab === 'data-editor' && (
                                    <DataEditor
                                        datasetId={selectedDatasetIds[0]}
                                        currentMetadata={JSON.parse(datasets?.find(d => d.id === selectedDatasetIds[0])?.metadata_json || '{}')}
                                    />
                                )}
                                {hasFlow && activeTab === 'timeseries' && <FDVChart datasetId={selectedDatasetIds[0]} />}
                                {hasFlow && activeTab === 'scatter' && <ScatterChart datasetId={selectedDatasetIds[0]} />}
                                {hasFlow && activeTab === 'dwf' && <DWFTab datasetId={selectedDatasetIds[0]} />}

                                {/* Fallback if tab doesn't match dataset type */}
                                {((hasRainfall && activeTab !== 'rainfall' && activeTab !== 'cumulative-depth') || (hasFlow && activeTab === 'rainfall')) && !hasFlow && !hasRainfall && (
                                    <div className="flex items-center justify-center h-full text-gray-500">
                                        Select a valid tab for this dataset type.
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <div className="flex items-center justify-center h-full text-gray-500">
                            Select a dataset to view analysis.
                        </div>
                    )}
                </div>
            </div>

            <UploadDatasetModal
                isOpen={isUploadModalOpen}
                onClose={() => setIsUploadModalOpen(false)}
                projectId={id}
            />
        </div>
    );
};

export default AnalysisWorkbench;
