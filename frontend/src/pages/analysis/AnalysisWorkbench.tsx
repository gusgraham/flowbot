import React, { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useAnalysisProject, useAnalysisDatasets, useDeleteAnalysisDataset, useProjectEvents } from '../../api/hooks';
import { ArrowLeft, CloudRain, Activity, Loader2, Upload, FileText, Trash2, ChevronDown, LineChart as LineChartIcon, AlertCircle, Calendar, Pencil } from 'lucide-react';
import { cn } from '../../lib/utils';
import UploadDatasetModal from './UploadDatasetModal';
import FDVChart from './FDVChart';
import DataEditor from './DataEditor';
import ScatterChart from './ScatterChart';
import { CumulativeDepthChart } from './CumulativeDepthChart';
import RainfallEventsAnalysis from './RainfallEventsAnalysis';

// const RainfallTab = ({ datasetId }: { datasetId: number }) => {
//     const { data: events, isLoading } = useRainfallEvents(datasetId);

//     if (isLoading) return <div className="animate-pulse h-32 bg-gray-50 rounded-lg"></div>;

//     return (
//         <div className="space-y-4">
//             <h3 className="text-lg font-semibold text-gray-900">Detected Rainfall Events</h3>
//             <div className="overflow-hidden border border-gray-200 rounded-lg">
//                 <table className="min-w-full divide-y divide-gray-200">
//                     <thead className="bg-gray-50">
//                         <tr>
//                             <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
//                             <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration</th>
//                             <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Depth (mm)</th>
//                             <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Peak Intensity (mm/hr)</th>
//                         </tr>
//                     </thead>
//                     <tbody className="bg-white divide-y divide-gray-200">
//                         {events?.map((event: any) => (
//                             <tr key={event.event_id}>
//                                 <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
//                                     {new Date(event.start_time).toLocaleString()}
//                                 </td>
//                                 <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
//                                     {event.duration_hours} hrs
//                                 </td>
//                                 <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{event.total_mm.toFixed(2)}</td>
//                                 <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{event.peak_intensity?.toFixed(2) || '-'}</td>
//                             </tr>
//                         ))}
//                         {events?.length === 0 && (
//                             <tr>
//                                 <td colSpan={4} className="px-6 py-12 text-center text-gray-500">
//                                     No rainfall events detected.
//                                 </td>
//                             </tr>
//                         )}
//                     </tbody>
//                 </table>
//             </div>
//         </div>
//     );
// };

const DWFTab = ({ datasetId: _datasetId }: { datasetId: number }) => (
    <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border border-dashed border-gray-300">
        <p className="text-gray-500">Dry Weather Flow Analysis Coming Soon</p>
    </div>
);

interface AnalysisWorkbenchProps {
    projectId?: number;
    embedded?: boolean;
}

const AnalysisWorkbench: React.FC<AnalysisWorkbenchProps> = ({ projectId: propProjectId, embedded = false }) => {
    const { projectId: paramProjectId } = useParams<{ projectId: string }>();
    const id = propProjectId || parseInt(paramProjectId || '0');

    const { data: project } = useAnalysisProject(id);

    const { data: datasets, refetch: refetchDatasets } = useAnalysisDatasets(id);
    const { data: savedEvents, refetch: refetchEvents } = useProjectEvents(id);
    const deleteDataset = useDeleteAnalysisDataset();

    // State for selection
    const [selectedDatasetIds, setSelectedDatasetIds] = useState<number[]>([]);
    const [activeTab, setActiveTab] = useState<'rainfall' | 'data-editor' | 'timeseries' | 'scatter' | 'dwf' | 'cumulative-depth' | 'event-analysis'>('rainfall');
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [rainfallExpanded, setRainfallExpanded] = useState(true);
    const [flowExpanded, setFlowExpanded] = useState(true);
    const [eventsExpanded, setEventsExpanded] = useState(true);

    // Group datasets by type
    const rainfallDatasets = datasets?.filter(d => d.variable === 'Rainfall') || [];
    const flowDatasets = datasets?.filter(d => d.variable === 'Flow/Depth' || d.variable === 'Flow') || [];

    // Auto-select first dataset if available and none selected
    React.useEffect(() => {
        if (datasets && datasets.length > 0 && selectedDatasetIds.length === 0) {
            // Only auto-select ready datasets
            const readyDataset = datasets.find(d => d.status === 'ready' || !d.status);
            if (readyDataset) {
                setSelectedDatasetIds([readyDataset.id]);
            }
        }
    }, [datasets]);

    // Poll for status updates if any dataset is processing
    React.useEffect(() => {
        const hasProcessing = datasets?.some(d => d.status === 'processing');
        if (hasProcessing) {
            const interval = setInterval(() => {
                refetchDatasets();
            }, 3000);
            return () => clearInterval(interval);
        }
    }, [datasets, refetchDatasets]);

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
    // Only include READY datasets for analysis
    const selectedDatasets = datasets?.filter(d => selectedDatasetIds.includes(d.id) && (d.status === 'ready' || !d.status)) || [];
    const hasRainfall = selectedDatasets.some(d => d.variable === 'Rainfall');
    const hasFlow = selectedDatasets.some(d => d.variable === 'Flow/Depth' || d.variable === 'Flow');
    const hasMixedTypes = hasRainfall && hasFlow;

    // Helper to check if multi-select is allowed
    const canMultiSelect = (variable: string) => {
        if (activeTab === 'timeseries') return true;

        if (variable === 'Rainfall') {
            return ['event-analysis', 'cumulative-depth'].includes(activeTab);
        }
        return false;
    };

    // Handle dataset click
    const handleDatasetClick = (id: number, variable: string) => {
        if (canMultiSelect(variable)) {
            toggleDatasetSelection(id);
        } else {
            setSelectedDatasetIds([id]);
        }
    };

    // Auto-switch tab if current tab is not valid for selected dataset type
    React.useEffect(() => {
        if (selectedDatasetIds.length > 0) {
            // If mixed types selected, only timeseries is valid
            if (hasMixedTypes && activeTab !== 'timeseries') {
                setActiveTab('timeseries');
                return;
            }

            // Define which tabs are valid for which dataset types
            const rainfallOnlyTabs = ['rainfall', 'event-analysis', 'cumulative-depth'];
            const flowOnlyTabs = ['dwf', 'scatter', 'data-editor'];
            const universalTabs = ['timeseries'];

            // Check if current tab is valid
            const isTabValid =
                universalTabs.includes(activeTab) ||
                (hasRainfall && !hasFlow && rainfallOnlyTabs.includes(activeTab)) ||
                (hasFlow && !hasRainfall && flowOnlyTabs.includes(activeTab));

            // If tab is not valid, switch to an appropriate one
            if (!isTabValid) {
                if (hasRainfall) {
                    setActiveTab('timeseries');
                } else if (hasFlow) {
                    setActiveTab('data-editor');
                } else {
                    setActiveTab('timeseries');
                }
            }
        }
    }, [selectedDatasetIds, hasRainfall, hasFlow, hasMixedTypes, activeTab]);

    if (!project) return <div className="p-8"><Loader2 className="animate-spin" /></div>;

    return (
        <div className={cn("flex flex-col", embedded ? "h-full" : "h-[calc(100vh-8rem)]")}>
            {!embedded && (
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
            )}

            {embedded && (
                <div className="mb-4 flex justify-end">
                    <button
                        onClick={() => setIsUploadModalOpen(true)}
                        className="bg-purple-600 text-white px-3 py-1.5 text-sm rounded-lg hover:bg-purple-700 transition-colors flex items-center"
                    >
                        <Upload size={16} className="mr-2" />
                        Upload Dataset
                    </button>
                </div>
            )}

            <div className="flex-1 flex gap-6 overflow-hidden">
                {/* Sidebar: Project Data */}
                <div className="w-72 bg-white border border-gray-200 rounded-xl flex flex-col overflow-hidden">
                    <div className="p-4 border-b border-gray-200 bg-gray-50">
                        <h3 className="font-semibold text-gray-700">Project Data</h3>
                    </div>
                    <div className="flex-1 overflow-y-auto p-2 space-y-3">
                        {datasets?.length === 0 ? (
                            <div className="text-center py-6 px-4 text-gray-500 text-sm border-b border-gray-100 pb-6">
                                <FileText size={24} className="mx-auto mb-2 opacity-20" />
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
                                                {rainfallDatasets.map(dataset => {
                                                    const isMulti = canMultiSelect(dataset.variable);
                                                    return (
                                                        <div
                                                            key={dataset.id}
                                                            className={cn(
                                                                "text-left p-3 rounded-lg border transition-all flex items-start gap-3 group",
                                                                selectedDatasetIds.includes(dataset.id)
                                                                    ? "bg-purple-50 border-purple-200 shadow-sm"
                                                                    : "bg-white border-transparent hover:bg-gray-50 hover:border-gray-200"
                                                            )}
                                                        >
                                                            {isMulti && (
                                                                <div className="pt-1">
                                                                    <input
                                                                        type="checkbox"
                                                                        checked={selectedDatasetIds.includes(dataset.id)}
                                                                        onChange={() => toggleDatasetSelection(dataset.id)}
                                                                        className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded cursor-pointer"
                                                                    />
                                                                </div>
                                                            )}
                                                            <button
                                                                onClick={() => handleDatasetClick(dataset.id, dataset.variable)}
                                                                className="flex items-start gap-3 flex-1 min-w-0 text-left"
                                                            >
                                                                <div className="p-2 rounded-md flex-shrink-0 bg-blue-100 text-blue-600">
                                                                    <CloudRain size={16} />
                                                                </div>

                                                                <div className="flex-1 min-w-0">
                                                                    <div className="flex items-center gap-2">
                                                                        <p className={cn(
                                                                            "font-medium truncate text-sm",
                                                                            selectedDatasetIds.includes(dataset.id) ? "text-purple-900" : "text-gray-900"
                                                                        )}>
                                                                            {dataset.name}
                                                                        </p>
                                                                        {dataset.status === 'processing' && (
                                                                            <span className="flex items-center text-xs text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full border border-amber-100">
                                                                                <Loader2 size={10} className="animate-spin mr-1" />
                                                                                Processing
                                                                            </span>
                                                                        )}
                                                                        {dataset.status === 'error' && (
                                                                            <span className="flex items-center text-xs text-red-600 bg-red-50 px-1.5 py-0.5 rounded-full border border-red-100" title={dataset.error_message}>
                                                                                <AlertCircle size={10} className="mr-1" />
                                                                                Error
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                    <p className="text-xs text-gray-500 truncate">
                                                                        {new Date(dataset.imported_at).toLocaleDateString()}
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
                                                    );
                                                })}
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
                                                <Activity size={16} className="text-emerald-600" />
                                                <span>Flow/Depth Monitors</span>
                                                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">
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
                                                {flowDatasets.map(dataset => {
                                                    const isMulti = canMultiSelect(dataset.variable);
                                                    return (
                                                        <div
                                                            key={dataset.id}
                                                            className={cn(
                                                                "text-left p-3 rounded-lg border transition-all flex items-start gap-3 group",
                                                                selectedDatasetIds.includes(dataset.id)
                                                                    ? "bg-purple-50 border-purple-200 shadow-sm"
                                                                    : "bg-white border-transparent hover:bg-gray-50 hover:border-gray-200"
                                                            )}
                                                        >
                                                            {isMulti && (
                                                                <div className="pt-1">
                                                                    <input
                                                                        type="checkbox"
                                                                        checked={selectedDatasetIds.includes(dataset.id)}
                                                                        onChange={() => toggleDatasetSelection(dataset.id)}
                                                                        className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded cursor-pointer"
                                                                    />
                                                                </div>
                                                            )}
                                                            <button
                                                                onClick={() => handleDatasetClick(dataset.id, dataset.variable)}
                                                                className="flex items-start gap-3 flex-1 min-w-0 text-left"
                                                            >
                                                                <div className="p-2 rounded-md flex-shrink-0 bg-emerald-100 text-emerald-600">
                                                                    <Activity size={16} />
                                                                </div>

                                                                <div className="flex-1 min-w-0">
                                                                    <div className="flex items-center gap-2">
                                                                        <p className={cn(
                                                                            "font-medium truncate text-sm",
                                                                            selectedDatasetIds.includes(dataset.id) ? "text-purple-900" : "text-gray-900"
                                                                        )}>
                                                                            {dataset.name}
                                                                        </p>
                                                                        {dataset.status === 'processing' && (
                                                                            <span className="flex items-center text-xs text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded-full border border-amber-100">
                                                                                <Loader2 size={10} className="animate-spin mr-1" />
                                                                                Processing
                                                                            </span>
                                                                        )}
                                                                        {dataset.status === 'error' && (
                                                                            <span className="flex items-center text-xs text-red-600 bg-red-50 px-1.5 py-0.5 rounded-full border border-red-100" title={dataset.error_message}>
                                                                                <AlertCircle size={10} className="mr-1" />
                                                                                Error
                                                                            </span>
                                                                        )}
                                                                    </div>
                                                                    <p className="text-xs text-gray-500 truncate">
                                                                        {new Date(dataset.imported_at).toLocaleDateString()}
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
                                                    );
                                                })}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </>
                        )}

                        {/* Events Section */}
                        <div className="pt-2 border-t border-gray-100">
                            {savedEvents?.length === 0 ? (
                                <div className="text-center py-4 px-4 text-gray-500 text-sm">
                                    <Calendar size={24} className="mx-auto mb-2 opacity-20" />
                                    <p>No events captured yet.</p>
                                </div>
                            ) : (
                                <div>
                                    <button
                                        onClick={() => setEventsExpanded(!eventsExpanded)}
                                        className="w-full flex items-center justify-between px-2 py-1.5 text-sm font-semibold text-gray-700 hover:bg-gray-50 rounded-md transition-colors"
                                    >
                                        <div className="flex items-center gap-2">
                                            <Calendar size={16} className="text-purple-600" />
                                            <span>Saved Events</span>
                                            <span className="text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                                                {savedEvents?.length || 0}
                                            </span>
                                        </div>
                                        <ChevronDown
                                            size={16}
                                            className={cn(
                                                "transition-transform",
                                                eventsExpanded ? "rotate-180" : ""
                                            )}
                                        />
                                    </button>
                                    {eventsExpanded && (
                                        <div className="mt-1 space-y-1">
                                            {savedEvents?.map(event => (
                                                <div
                                                    key={event.id}
                                                    className="text-left p-3 rounded-lg border bg-white border-transparent hover:bg-gray-50 hover:border-gray-200 transition-all flex items-start gap-3 group"
                                                >
                                                    <div className="p-2 rounded-md flex-shrink-0 bg-purple-100 text-purple-600">
                                                        <Calendar size={16} />
                                                    </div>
                                                    <div className="min-w-0 flex-1">
                                                        <p className="font-medium text-gray-900 truncate" title={event.name}>
                                                            {event.name}
                                                        </p>
                                                        <p className="text-xs text-gray-500 mt-0.5">
                                                            {new Date(event.start_time).toLocaleDateString()}
                                                        </p>
                                                        <p className="text-xs text-gray-400 mt-0.5">
                                                            {event.event_type}
                                                        </p>
                                                    </div>
                                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                        <button
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                // TODO: Open edit modal
                                                                console.log('Edit event:', event.id);
                                                            }}
                                                            className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                                            title="Edit event"
                                                        >
                                                            <Pencil size={14} />
                                                        </button>
                                                        <button
                                                            onClick={async (e) => {
                                                                e.stopPropagation();
                                                                if (confirm(`Delete event "${event.name}"?`)) {
                                                                    try {
                                                                        const response = await fetch(`/api/fsa/events/${event.id}`, {
                                                                            method: 'DELETE'
                                                                        });
                                                                        if (response.ok) {
                                                                            refetchEvents();
                                                                        }
                                                                    } catch (error) {
                                                                        console.error('Failed to delete event:', error);
                                                                    }
                                                                }
                                                            }}
                                                            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                                                            title="Delete event"
                                                        >
                                                            <Trash2 size={14} />
                                                        </button>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Main Content Area */}
                <div className="flex-1 bg-white border border-gray-200 rounded-xl flex flex-col overflow-hidden">
                    {selectedDatasetIds.length === 0 ? (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-500">
                            <LineChartIcon size={48} className="mb-4 opacity-20" />
                            <p className="text-lg font-medium">No datasets selected</p>
                            <p className="text-sm">Select a dataset from the sidebar to view analysis.</p>
                        </div>
                    ) : (
                        <>
                            {/* Tabs */}
                            <div className="border-b border-gray-200 px-4 flex items-center gap-6 overflow-x-auto">
                                {/* Rainfall-specific tabs - only show if no flow datasets selected */}
                                {hasRainfall && !hasMixedTypes && (
                                    <>
                                        <button
                                            onClick={() => setActiveTab('timeseries')}
                                            className={cn(
                                                "py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                                                activeTab === 'timeseries'
                                                    ? "border-purple-600 text-purple-600"
                                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                            )}
                                        >
                                            Time Series
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('cumulative-depth')}
                                            className={cn(
                                                "py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                                                activeTab === 'cumulative-depth'
                                                    ? "border-purple-600 text-purple-600"
                                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                            )}
                                        >
                                            Cumulative Depth
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('event-analysis')}
                                            className={cn(
                                                "py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                                                activeTab === 'event-analysis'
                                                    ? "border-purple-600 text-purple-600"
                                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                            )}
                                        >
                                            Event Analysis
                                        </button>

                                    </>
                                )}

                                {/* Flow-specific tabs - only show if no rainfall datasets selected */}
                                {hasFlow && !hasMixedTypes && (
                                    <>
                                        <button
                                            onClick={() => setActiveTab('data-editor')}
                                            className={cn(
                                                "py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                                                activeTab === 'data-editor'
                                                    ? "border-purple-600 text-purple-600"
                                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                            )}
                                        >
                                            Data Editor
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('timeseries')}
                                            className={cn(
                                                "py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                                                activeTab === 'timeseries'
                                                    ? "border-purple-600 text-purple-600"
                                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                            )}
                                        >
                                            Time Series
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('scatter')}
                                            className={cn(
                                                "py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                                                activeTab === 'scatter'
                                                    ? "border-purple-600 text-purple-600"
                                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                            )}
                                        >
                                            Scatter Plot
                                        </button>
                                        <button
                                            onClick={() => setActiveTab('dwf')}
                                            className={cn(
                                                "py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                                                activeTab === 'dwf'
                                                    ? "border-purple-600 text-purple-600"
                                                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                            )}
                                        >
                                            Dry Weather Flow
                                        </button>
                                    </>
                                )}

                                {/* Mixed types - only show Time Series */}
                                {hasMixedTypes && (
                                    <button
                                        onClick={() => setActiveTab('timeseries')}
                                        className={cn(
                                            "py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap",
                                            activeTab === 'timeseries'
                                                ? "border-purple-600 text-purple-600"
                                                : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                                        )}
                                    >
                                        Time Series
                                    </button>
                                )}
                            </div>

                            {/* Content */}
                            <div className="flex-1 overflow-y-auto p-6">
                                {/* {activeTab === 'rainfall' && (
                                    <RainfallTab datasetId={selectedDatasetIds[0]} />
                                )} */}
                                {activeTab === 'event-analysis' && (
                                    <RainfallEventsAnalysis
                                        datasetIds={selectedDatasetIds}
                                        projectId={id}
                                        onEventSaved={refetchEvents}
                                    />
                                )}
                                {activeTab === 'timeseries' && (
                                    <FDVChart datasets={selectedDatasets} />
                                )}
                                {activeTab === 'scatter' && (
                                    <ScatterChart datasetId={selectedDatasetIds[0].toString()} />
                                )}
                                {activeTab === 'cumulative-depth' && (
                                    <CumulativeDepthChart
                                        datasetIds={selectedDatasetIds}
                                        datasets={datasets || []}
                                    />
                                )}
                                {activeTab === 'data-editor' && (
                                    <DataEditor
                                        datasetId={selectedDatasetIds[0]}
                                        currentMetadata={selectedDatasets[0]?.metadata_json ? JSON.parse(selectedDatasets[0].metadata_json) : {}}
                                    />
                                )}
                                {activeTab === 'dwf' && (
                                    <DWFTab datasetId={selectedDatasetIds[0]} />
                                )}
                            </div>
                        </>
                    )
                    }
                </div >
            </div >

            <UploadDatasetModal
                isOpen={isUploadModalOpen}
                onClose={() => setIsUploadModalOpen(false)}
                projectId={id}
            />
        </div >
    );
};

export default AnalysisWorkbench;
