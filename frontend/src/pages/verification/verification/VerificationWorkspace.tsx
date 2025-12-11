import { useState, useMemo, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, AlertTriangle, XCircle, Activity, Droplets, Settings, BarChart2, RefreshCw, X, MousePointer2 } from 'lucide-react';
import { useWorkspaceData, useUpdateVerificationRunSettings, type AnalysisSettings } from '../../../api/hooks';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceDot,
    ScatterChart, Scatter, ReferenceLine
} from 'recharts';

interface VerificationWorkspaceProps {
    runId?: number | null;
    embedded?: boolean;
}

// Simple decimation downsampling (moved outside component)
const downsample = <T,>(data: T[], targetPoints: number = 2000): T[] => {
    if (!data || data.length <= targetPoints) return data;
    const step = Math.ceil(data.length / targetPoints);
    return data.filter((_, i) => i % step === 0);
};

const formatTime = (isoString: string) => new Date(isoString).toLocaleString();

// Analysis Controls Component
interface AnalysisControlsProps {
    currentSettings: AnalysisSettings;
    onSettingsChange: (settings: AnalysisSettings) => void;
    onApply: () => void;
    isFetching: boolean;
    onClose: () => void;
    editSeries: 'obs_flow' | 'pred_flow' | null;
    setEditSeries: (series: 'obs_flow' | 'pred_flow' | null) => void;
}

const AnalysisControls = ({
    currentSettings,
    onSettingsChange,
    onApply,
    isFetching,
    onClose,
    editSeries,
    setEditSeries
}: AnalysisControlsProps) => {
    // Local state for inputs (synced with currentSettings)
    const [smoothingObs, setSmoothingObs] = useState(currentSettings.smoothing_obs ?? 0);
    const [smoothingPred, setSmoothingPred] = useState(currentSettings.smoothing_pred ?? 0);
    const [maxPeaksObs, setMaxPeaksObs] = useState<number | ''>(currentSettings.max_peaks_obs ?? '');
    const [maxPeaksPred, setMaxPeaksPred] = useState<number | ''>(currentSettings.max_peaks_pred ?? '');
    const [peakMode, setPeakMode] = useState<'auto' | 'manual'>(currentSettings.peak_mode ?? 'auto');

    // Sync local state when props change (e.g. initial load)
    useEffect(() => {
        setSmoothingObs(currentSettings.smoothing_obs ?? 0);
        setSmoothingPred(currentSettings.smoothing_pred ?? 0);
        setMaxPeaksObs(currentSettings.max_peaks_obs ?? '');
        setMaxPeaksPred(currentSettings.max_peaks_pred ?? '');
        setPeakMode(currentSettings.peak_mode ?? 'auto');
    }, [currentSettings.smoothing_obs, currentSettings.smoothing_pred, currentSettings.max_peaks_obs, currentSettings.max_peaks_pred, currentSettings.peak_mode]);

    // Update parent settings whenever inputs change
    useEffect(() => {
        onSettingsChange({
            ...currentSettings,
            smoothing_obs: smoothingObs,
            smoothing_pred: smoothingPred,
            max_peaks_obs: maxPeaksObs === '' ? undefined : Number(maxPeaksObs),
            max_peaks_pred: maxPeaksPred === '' ? undefined : Number(maxPeaksPred),
            peak_mode: peakMode
        });
    }, [smoothingObs, smoothingPred, maxPeaksObs, maxPeaksPred, peakMode]);

    const handleReset = () => {
        setSmoothingObs(0);
        setSmoothingPred(0);
        setMaxPeaksObs('');
        setMaxPeaksPred('');
        setPeakMode('auto');
        setEditSeries(null);
        onSettingsChange({
            smoothing_obs: 0,
            smoothing_pred: 0,
            max_peaks_obs: undefined,
            max_peaks_pred: undefined,
            peak_mode: 'auto',
            manual_peaks: {}
        });
    };

    return (
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm animate-in slide-in-from-top-2 relative mb-4">
            <button
                onClick={onClose}
                className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
            >
                <X size={16} />
            </button>
            <div className="flex flex-col gap-6">

                {/* Smoothing Section */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="space-y-4">
                        <h4 className="font-semibold text-gray-700 text-sm">Smoothing (0.0 - 1.0)</h4>
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-semibold mb-1" style={{ color: '#15803d' }}>Observed</label>
                                <input
                                    type="number" min="0" max="1" step="0.01"
                                    value={smoothingObs}
                                    onChange={(e) => setSmoothingObs(parseFloat(e.target.value))}
                                    className="w-full px-3 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 font-mono"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-semibold mb-1" style={{ color: '#dc2626' }}>Predicted</label>
                                <input
                                    type="number" min="0" max="1" step="0.01"
                                    value={smoothingPred}
                                    onChange={(e) => setSmoothingPred(parseFloat(e.target.value))}
                                    className="w-full px-3 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 font-mono"
                                />
                            </div>
                        </div>
                    </div>

                    {/* Peak Detection Section */}
                    <div className="space-y-4">
                        <div className="flex items-center justify-between">
                            <h4 className="font-semibold text-gray-700 text-sm">Peak Selection</h4>
                            <div className="flex bg-gray-100 rounded p-1">
                                <button
                                    onClick={() => { setPeakMode('auto'); setEditSeries(null); }}
                                    className={`px-3 py-1 text-xs font-medium rounded ${peakMode === 'auto' ? 'bg-white shadow text-blue-700' : 'text-gray-500 hover:text-gray-700'}`}
                                >
                                    Auto
                                </button>
                                <button
                                    onClick={() => setPeakMode('manual')}
                                    className={`px-3 py-1 text-xs font-medium rounded ${peakMode === 'manual' ? 'bg-white shadow text-blue-700' : 'text-gray-500 hover:text-gray-700'}`}
                                >
                                    Manual
                                </button>
                            </div>
                        </div>

                        {peakMode === 'auto' ? (
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-xs font-semibold mb-1" style={{ color: '#15803d' }}>Max Peaks (Obs)</label>
                                    <input
                                        type="number" min="1" step="1"
                                        placeholder="All"
                                        value={maxPeaksObs}
                                        onChange={(e) => setMaxPeaksObs(e.target.value === '' ? '' : parseInt(e.target.value))}
                                        className="w-full px-3 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 font-mono"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold mb-1" style={{ color: '#dc2626' }}>Max Peaks (Pred)</label>
                                    <input
                                        type="number" min="1" step="1"
                                        placeholder="All"
                                        value={maxPeaksPred}
                                        onChange={(e) => setMaxPeaksPred(e.target.value === '' ? '' : parseInt(e.target.value))}
                                        className="w-full px-3 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 font-mono"
                                    />
                                </div>
                            </div>
                        ) : (
                            <div className="grid grid-cols-2 gap-4">
                                <button
                                    onClick={() => setEditSeries(editSeries === 'obs_flow' ? null : 'obs_flow')}
                                    className={`flex items-center justify-center gap-2 px-2 py-1.5 text-xs font-medium rounded border transition-colors ${editSeries === 'obs_flow' ? 'bg-green-100 border-green-500 text-green-800 ring-2 ring-green-200' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
                                >
                                    <MousePointer2 size={14} />
                                    {editSeries === 'obs_flow' ? 'Selecting...' : 'Select Obs'}
                                </button>
                                <button
                                    onClick={() => setEditSeries(editSeries === 'pred_flow' ? null : 'pred_flow')}
                                    className={`flex items-center justify-center gap-2 px-2 py-1.5 text-xs font-medium rounded border transition-colors ${editSeries === 'pred_flow' ? 'bg-red-100 border-red-500 text-red-800 ring-2 ring-red-200' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
                                >
                                    <MousePointer2 size={14} />
                                    {editSeries === 'pred_flow' ? 'Selecting...' : 'Select Pred'}
                                </button>
                                <div className="col-span-2 text-xs text-gray-500 italic text-center">
                                    Click chart to toggle peaks for selected series.
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex justify-end gap-3 pt-2 border-t border-gray-100">
                    <button
                        onClick={handleReset}
                        className="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 font-medium"
                    >
                        Reset Defaults
                    </button>
                    <button
                        onClick={onApply}
                        disabled={isFetching}
                        className="px-6 py-2 bg-blue-600 text-white rounded-md text-sm font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        {isFetching ? 'Applying...' : 'Apply Analysis'}
                    </button>
                </div>
            </div>
        </div>
    );
};

export default function VerificationWorkspace({ runId: propRunId, embedded = false }: VerificationWorkspaceProps) {
    const { runId: paramRunId } = useParams<{ runId: string }>();
    const navigate = useNavigate();

    const effectiveRunId = propRunId || (paramRunId ? parseInt(paramRunId) : null);

    // Workspace UI State
    const [showControls, setShowControls] = useState(false);
    const [viewMode, setViewMode] = useState<'timeseries' | 'shapefit'>('timeseries');

    // Manual Peak Editing State
    const [editSeries, setEditSeries] = useState<'obs_flow' | 'pred_flow' | null>(null);

    // Analysis Settings State
    const [analysisSettings, setAnalysisSettings] = useState<AnalysisSettings>({});

    // Fetch Data
    const { data, isLoading, error, isFetching, refetch } = useWorkspaceData(effectiveRunId, analysisSettings);
    const updateSettingsMutation = useUpdateVerificationRunSettings();

    // Initialize local settings from server data on load (only if empty to avoid overwrite during edits)
    // Actually we should sync on load essentially once or when runId changes
    useEffect(() => {
        if (data?.run?.analysis_settings && effectiveRunId) {
            // Only update if we don't have local changes? 
            // Or better: Use server settings as 'initial', but allow fully controlled local state
            setAnalysisSettings(data.run.analysis_settings);
        }
    }, [data?.run?.analysis_settings, effectiveRunId]);

    const handleApplyAnalysis = () => {
        if (!effectiveRunId) return;
        updateSettingsMutation.mutate({
            runId: effectiveRunId,
            settings: analysisSettings
        }, {
            onSuccess: () => {
                refetch();
                setEditSeries(null); // Exit edit mode
            }
        });
    };

    const handleChartClick = (e: any) => {
        console.log('Chart Click Event:', e);
        if (analysisSettings.peak_mode !== 'manual' || !editSeries) {
            console.log('Click ignored: Not in manual mode or no series selected', { peakMode: analysisSettings.peak_mode, editSeries });
            return;
        }

        // Recharts gives 'activeLabel' which matches our XAxis dataKey 'time' (formatted string)
        const clickedLabel = e?.activeLabel;

        if (!clickedLabel) {
            console.log('Click ignored: No activeLabel in event');
            return;
        }

        console.log('Processing click for label:', clickedLabel);

        // Find existing peaks for this series
        const currentPeaks = analysisSettings.manual_peaks?.[editSeries] || [];

        // Check if we are adding or removing
        // IMPORTANT: We must match based on valid time.
        // If stored peaks are ISO, we need to convert clickedLabel (Formatted) to ISO to match?
        // Or convert stored ISO to Formatted?
        // Let's use Formatted for UI matching since clickedLabel is formatted.

        // Find data point to get ISO for clicked label
        const clickedDataPoint = flowChartData.find(d => d.time === clickedLabel);
        const clickedIso = (clickedDataPoint as any)?.iso_time;

        const existingIndex = currentPeaks.findIndex(p => p.time === clickedIso);

        let newPeaks;
        if (existingIndex >= 0) {
            // Remove
            console.log('Removing existing peak at:', clickedLabel);
            newPeaks = currentPeaks.filter((_, i) => i !== existingIndex);
        } else {
            // Add
            // Try to find value from activePayload first (tooltip data)
            let valueToAdd: number | undefined;

            if (e.activePayload && e.activePayload.length > 0) {
                const payloadItem = e.activePayload.find((p: any) => {
                    if (editSeries === 'obs_flow') return p.dataKey === 'observed' || p.dataKey === 'obs_smoothed';
                    if (editSeries === 'pred_flow') return p.dataKey === 'predicted' || p.dataKey === 'pred_smoothed';
                    return false;
                });
                if (payloadItem) {
                    valueToAdd = Number(payloadItem.value);
                }
            }

            // Fallback: Look up in flowChartData directly using the label
            if (valueToAdd === undefined) {
                const dataPoint = flowChartData.find(d => d.time === clickedLabel);
                if (dataPoint) {
                    if (editSeries === 'obs_flow') valueToAdd = (dataPoint.obs_smoothed as number) ?? (dataPoint.observed as number);
                    if (editSeries === 'pred_flow') valueToAdd = (dataPoint.pred_smoothed as number) ?? (dataPoint.predicted as number);
                }
            }

            if (valueToAdd !== undefined && valueToAdd !== null && clickedIso) {
                console.log('Adding new peak:', { time: clickedIso, value: valueToAdd });
                newPeaks = [...currentPeaks, { time: clickedIso, value: valueToAdd }];
            } else {
                console.warn('Could not determine value or ISO time for peak at:', clickedLabel);
                return;
            }

        }


        // Update state
        setAnalysisSettings(prev => ({
            ...prev,
            manual_peaks: {
                ...prev.manual_peaks,
                [editSeries]: newPeaks
            }
        }));
    };

    const chartTooltipFormatter = (value: number) => {
        if (value == null) return '';
        return value.toFixed(3);
    };

    // Prepare chart data
    const maxScatterVal = useMemo(() => {
        if (!data?.series?.obs_flow || !data?.series?.pred_flow) return 0;
        const obsMax = Math.max(...data.series.obs_flow.values);
        const predMax = Math.max(...data.series.pred_flow.values);
        return Math.max(obsMax, predMax);
    }, [data]);

    const { flowChartData, depthChartData, flowScatterData } = useMemo(() => {
        if (!data?.series) return { flowChartData: [], depthChartData: [], flowScatterData: [] };

        const obs = data.series.obs_flow ? downsample(data.series.obs_flow.values) : [];
        const pred = data.series.pred_flow ? downsample(data.series.pred_flow.values) : [];
        const time = data.series.obs_flow ? downsample(data.series.obs_flow.time) : [];

        const obsSmooth = data.series.obs_flow_smoothed ? downsample(data.series.obs_flow_smoothed.values) : null;
        const predSmooth = data.series.pred_flow_smoothed ? downsample(data.series.pred_flow_smoothed.values) : null;

        const flowChartData = time.map((t, i) => ({
            time: formatTime(t),
            iso_time: t, // Keep raw ISO for backend
            observed: obs[i],
            predicted: pred[i],
            obs_smoothed: obsSmooth ? obsSmooth[i] : null,
            pred_smoothed: predSmooth ? predSmooth[i] : null,
        }));

        const obsDepth = data.series.obs_depth ? downsample(data.series.obs_depth.values) : [];
        const predDepth = data.series.pred_depth ? downsample(data.series.pred_depth.values) : [];
        const timeDepth = data.series.obs_depth ? downsample(data.series.obs_depth.time) : [];
        const obsDepthSmooth = data.series.obs_depth_smoothed ? downsample(data.series.obs_depth_smoothed.values) : null;
        const predDepthSmooth = data.series.pred_depth_smoothed ? downsample(data.series.pred_depth_smoothed.values) : null;

        const depthChartData = timeDepth.map((t, i) => ({
            time: formatTime(t),
            observed: obsDepth[i],
            predicted: predDepth[i],
            obs_smoothed: obsDepthSmooth ? obsDepthSmooth[i] : null,
            pred_smoothed: predDepthSmooth ? predDepthSmooth[i] : null,
        }));

        const flowScatterData = downsample(data.series.obs_flow?.values.map((val, i) => ({
            observed: val,
            predicted: data.series.pred_flow?.values[i]
        })).filter(d => d.observed != null && d.predicted != null) || [], 2000);

        return { flowChartData, depthChartData, flowScatterData };
    }, [data?.series]);

    // Peaks to display: Prioritize local manuals if mode is manual, otherwise use server peaks (which might be persisted manuals or auto)
    // Actually, we should just visualize what's in `analysisSettings.manual_peaks` if mode is manual.
    // NOTE: 'manual_peaks' in settings might be unsaved (local edits).
    const displayPeaks = useMemo(() => {
        if (analysisSettings.peak_mode === 'manual') {
            const manual = analysisSettings.manual_peaks || {};
            // Format time to match chart labels (toLocaleString) for ReferenceDot validation
            // Wait, ReferenceDot matches XAxis which uses `formatTime(t)`.
            // My manual peaks store ISO string.
            // I need to ensure matches.
            return {
                obs_flow: manual.obs_flow?.map(p => ({ ...p, time_label: formatTime(p.time) })) || [],
                pred_flow: manual.pred_flow?.map(p => ({ ...p, time_label: formatTime(p.time) })) || [],
            };
        }
        // Auto mode or initial load: use server provided peaks (formatted with time string already?)
        // Server peaks have `time` as ISO? Check backend workspace.
        // Backend `get_run_workspace`: `peaks_data` items have `time` formatted as `strftime('%Y-%m-%dT%H:%M:%S')`.
        // Frontend `formatTime` uses `toLocaleString`.
        // Mismatch risk?
        // `formatTime`: `new Date(isoString).toLocaleString()`.
        // Server: '2023...'. `new Date()` works.
        // IMPORTANT: The chart XAxis uses `formatTime`. So ReferenceDot `x` must match `formatTime`.
        // Server data `peaks` need to be mapped.
        // `data.peaks` items have `time` string.
        return {
            obs_flow: data?.peaks?.obs_flow?.map(p => ({ ...p, time_label: formatTime(p.time) })) || [],
            pred_flow: data?.peaks?.pred_flow?.map(p => ({ ...p, time_label: formatTime(p.time) })) || [],
            obs_depth: data?.peaks?.obs_depth?.map(p => ({ ...p, time_label: formatTime(p.time) })) || [],
            pred_depth: data?.peaks?.pred_depth?.map(p => ({ ...p, time_label: formatTime(p.time) })) || []
        };
    }, [analysisSettings.peak_mode, analysisSettings.manual_peaks, data?.peaks]);

    // ... Rendering Helpers ...
    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'VERIFIED': return <CheckCircle className="text-green-600" size={28} />;
            case 'MARGINAL': return <AlertTriangle className="text-amber-600" size={28} />;
            case 'NOT_VERIFIED': return <XCircle className="text-red-600" size={28} />;
            default: return null;
        }
    };
    const getStatusColor = (status: string) => {
        switch (status) {
            case 'VERIFIED': return 'bg-green-50 border-green-200';
            case 'MARGINAL': return 'bg-amber-50 border-amber-200';
            case 'NOT_VERIFIED': return 'bg-red-50 border-red-200';
            default: return 'bg-gray-50 border-gray-200';
        }
    };
    const getBandColor = (band?: string) => {
        switch (band) {
            case 'OK': return 'bg-green-100 text-green-800';
            case 'FAIR': return 'bg-amber-100 text-amber-800';
            case 'NO': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };
    const getMetricLabel = (name: string) => {
        // Simplification for brewity
        return name.replace(/_/g, ' ');
    };

    if (isLoading && !data) {
        return <div className="p-8 text-center text-gray-500">Loading analysis workspace...</div>;
    }
    if (error || (!isLoading && !data)) {
        return <div className="p-8 text-center text-red-500">Error loading workspace data</div>;
    }
    if (!data) return null;

    return (
        <div className="h-full flex flex-col bg-gray-50 overflow-y-auto">
            <div className="bg-white border-b border-gray-200 px-6 py-4 flex justify-between items-center sticky top-0 z-10 shadow-sm">
                <div className="flex items-center gap-4">
                    {!embedded && (
                        <button
                            onClick={() => navigate(-1)}
                            className="p-2 rounded-full hover:bg-gray-200 transition"
                        >
                            <ArrowLeft size={24} />
                        </button>
                    )}
                    <div>
                        <h1 className="text-2xl font-bold text-gray-900">
                            {data?.monitor?.name} - {data?.event?.name}
                        </h1>
                        <p className="text-gray-500">
                            Event: {data?.event?.event_type} |
                            {data?.monitor?.is_critical && <span className="ml-2 text-red-600 font-medium">Critical</span>}
                            {data?.monitor?.is_surcharged && <span className="ml-2 text-purple-600 font-medium">Surcharged</span>}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <div className="flex bg-white rounded-md border border-gray-300 overflow-hidden">
                        <button
                            className={`px-3 py-1.5 text-sm font-medium ${viewMode === 'timeseries' ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-50'}`}
                            onClick={() => setViewMode('timeseries')}
                        >
                            Time Series
                        </button>
                        <button
                            className={`px-3 py-1.5 text-sm font-medium ${viewMode === 'shapefit' ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-50'}`}
                            onClick={() => setViewMode('shapefit')}
                        >
                            Shape Fit
                        </button>
                    </div>
                    <button
                        onClick={() => setShowControls(!showControls)}
                        className={`flex items-center gap-2 px-3 py-1.5 rounded-md border font-medium transition-colors ${showControls ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}`}
                    >
                        <Settings size={16} />
                        Analysis
                    </button>
                </div>
            </div>

            {/* Analysis Controls Panel */}
            {showControls && (
                <div className="px-6 pt-4">
                    <AnalysisControls
                        currentSettings={analysisSettings}
                        onSettingsChange={setAnalysisSettings}
                        onApply={handleApplyAnalysis}
                        isFetching={isFetching || updateSettingsMutation.isPending}
                        onClose={() => setShowControls(false)}
                        editSeries={editSeries}
                        setEditSeries={setEditSeries}
                    />
                </div>
            )}

            {/* Content */}
            <div className="p-6">
                {viewMode === 'timeseries' ? (
                    <>
                        {/* Flow Chart */}
                        {flowChartData.length > 0 && (
                            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                                <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
                                    Flow Comparison
                                    {editSeries && (
                                        <span className="text-xs font-medium px-2 py-1 bg-yellow-100 text-yellow-800 rounded animate-pulse border border-yellow-200 flex items-center gap-1">
                                            <MousePointer2 size={12} />
                                            Mode Active: Click chart to toggle {editSeries === 'obs_flow' ? 'Observed' : 'Predicted'} Peaks
                                        </span>
                                    )}
                                </h3>
                                <ResponsiveContainer width="100%" height={400}>
                                    <LineChart
                                        data={flowChartData}
                                        onClick={handleChartClick}
                                        className={editSeries ? 'cursor-crosshair' : ''}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="time"
                                            tick={{ fontSize: 10 }}
                                            interval="preserveStartEnd"
                                            angle={-45}
                                            textAnchor="end"
                                            height={80}
                                        />
                                        <YAxis label={{ value: 'Flow', angle: -90, position: 'insideLeft' }} />
                                        <Tooltip formatter={chartTooltipFormatter} />
                                        <Legend />
                                        <Line
                                            type="monotone"
                                            dataKey="observed"
                                            stroke="#15803d" // Leaf Green
                                            strokeWidth={2}
                                            dot={false}
                                            name="Observed (Raw)"
                                            opacity={data.series.obs_flow_smoothed ? 0.3 : 1}
                                            isAnimationActive={false} // Disable animation for faster click feedback
                                            activeDot={editSeries === 'obs_flow' ? { r: 6, stroke: '#22c55e', strokeWidth: 2 } : { r: 4 }}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="predicted"
                                            stroke="#dc2626" // Nice Red
                                            strokeWidth={2}
                                            dot={false}
                                            name="Predicted (Raw)"
                                            opacity={data.series.pred_flow_smoothed ? 0.3 : 1}
                                            isAnimationActive={false}
                                            activeDot={editSeries === 'pred_flow' ? { r: 6, stroke: '#ef4444', strokeWidth: 2 } : { r: 4 }}
                                        />
                                        {data.series.obs_flow_smoothed && (
                                            <Line
                                                type="monotone"
                                                dataKey="obs_smoothed"
                                                stroke="#15803d"
                                                strokeWidth={2}
                                                dot={false}
                                                name="Observed (Smoothed)"
                                                isAnimationActive={false}
                                            />
                                        )}
                                        {data.series.pred_flow_smoothed && (
                                            <Line
                                                type="monotone"
                                                dataKey="pred_smoothed"
                                                stroke="#dc2626"
                                                strokeWidth={2}
                                                dot={false}
                                                name="Predicted (Smoothed)"
                                                isAnimationActive={false}
                                            />
                                        )}

                                        {/* Peak markers use time_label to match XAxis */}
                                        {displayPeaks.obs_flow?.map((peak: any, i: number) => (
                                            <ReferenceDot
                                                key={`obs-peak-${i}`}
                                                x={peak.time_label}
                                                y={peak.value}
                                                r={6}
                                                fill="#15803d"
                                                stroke="#fff"
                                                strokeWidth={1.5}
                                            />
                                        ))}
                                        {displayPeaks.pred_flow?.map((peak: any, i: number) => (
                                            <ReferenceDot
                                                key={`pred-peak-${i}`}
                                                x={peak.time_label}
                                                y={peak.value}
                                                r={6}
                                                fill="#dc2626"
                                                stroke="#fff"
                                                strokeWidth={1.5}
                                            />
                                        ))}
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        )}

                        {/* Depth Chart (Simplified replication of existing) - Manual edits skipped for now as per immediate req logic focus on flow */}
                        {/* ... Depth Chart Omitted for brevity of update, assuming user focused on flow logic first or can be copied ... */}
                        {/* Wait, I MUST provide the full file or I lose the Depth Chart. */}
                        {/* Re-inserting Depth Chart Code */}
                        {depthChartData.length > 0 && (
                            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                                <h3 className="text-lg font-semibold mb-4">Depth Comparison</h3>
                                <ResponsiveContainer width="100%" height={400}>
                                    <LineChart data={depthChartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="time"
                                            tick={{ fontSize: 10 }}
                                            interval="preserveStartEnd"
                                            angle={-45}
                                            textAnchor="end"
                                            height={80}
                                        />
                                        <YAxis label={{ value: 'Depth', angle: -90, position: 'insideLeft' }} />
                                        <Tooltip formatter={chartTooltipFormatter} />
                                        <Legend />
                                        <Line
                                            type="monotone"
                                            dataKey="observed"
                                            stroke="#15803d"
                                            strokeWidth={2}
                                            dot={false}
                                            name="Observed (Raw)"
                                            opacity={data.series.obs_depth_smoothed ? 0.3 : 1}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="predicted"
                                            stroke="#dc2626"
                                            strokeWidth={2}
                                            dot={false}
                                            name="Predicted (Raw)"
                                            opacity={data.series.pred_depth_smoothed ? 0.3 : 1}
                                        />
                                        {data.series.obs_depth_smoothed && (
                                            <Line
                                                type="monotone"
                                                dataKey="obs_smoothed"
                                                stroke="#15803d"
                                                strokeWidth={2}
                                                dot={false}
                                                name="Observed (Smoothed)"
                                            />
                                        )}
                                        {data.series.pred_depth_smoothed && (
                                            <Line
                                                type="monotone"
                                                dataKey="pred_smoothed"
                                                stroke="#dc2626"
                                                strokeWidth={2}
                                                dot={false}
                                                name="Predicted (Smoothed)"
                                            />
                                        )}
                                        {displayPeaks.obs_depth?.map((peak: any, i: number) => (
                                            <ReferenceDot
                                                key={`obs-peak-${i}`}
                                                x={peak.time_label}
                                                y={peak.value}
                                                r={6}
                                                fill="#15803d"
                                                stroke="#fff"
                                            />
                                        ))}
                                        {displayPeaks.pred_depth?.map((peak: any, i: number) => (
                                            <ReferenceDot
                                                key={`pred-peak-${i}`}
                                                x={peak.time_label}
                                                y={peak.value}
                                                r={6}
                                                fill="#dc2626"
                                                stroke="#fff"
                                            />
                                        ))}
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        )}

                        {/* Flow Metrics */}
                        <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                            <div className="flex items-center gap-2 mb-4">
                                <Activity className="text-blue-600" />
                                <h3 className="text-lg font-semibold">Flow Metrics</h3>
                            </div>
                            <div className="flex flex-wrap gap-4">
                                {data?.metrics?.flow?.map((metric) => (
                                    <div key={metric.name} className="p-4 bg-gray-50 rounded-lg min-w-[200px] flex-1">
                                        <div className="text-sm text-gray-500 capitalize">
                                            {getMetricLabel(metric.name)}
                                        </div>
                                        <div className="text-xl font-bold text-gray-900">
                                            {typeof metric.value === 'number' ? metric.value.toFixed(3) : 'N/A'}
                                        </div>
                                        {metric.band && (
                                            <span className={`inline-block mt-1 px-2 py-0.5 text-xs rounded ${getBandColor(metric.band)}`}>
                                                {metric.band} ({metric.points} pts)
                                            </span>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Depth Metrics */}
                        {data.metrics.depth && data.metrics.depth.length > 0 && (
                            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                                <div className="flex items-center gap-2 mb-4">
                                    <Droplets className="text-cyan-600" />
                                    <h3 className="text-lg font-semibold">Depth Metrics</h3>
                                </div>
                                <div className="flex flex-wrap gap-4">
                                    {data.metrics.depth.map((metric) => (
                                        <div key={metric.name} className="p-4 bg-gray-50 rounded-lg min-w-[200px] flex-1">
                                            <div className="text-sm text-gray-500 capitalize">
                                                {getMetricLabel(metric.name)}
                                            </div>
                                            <div className="text-xl font-bold text-gray-900">
                                                {typeof metric.value === 'number' ? metric.value.toFixed(3) : 'N/A'}
                                            </div>
                                            {metric.band && (
                                                <span className={`inline-block mt-1 px-2 py-0.5 text-xs rounded ${getBandColor(metric.band)}`}>
                                                    {metric.band} ({metric.points} pts)
                                                </span>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Status Card */}
                        <div className={`p-6 rounded-lg border-2 ${getStatusColor(data?.run?.overall_status || 'UNKNOWN')}`}>
                            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                                <div className="flex items-center gap-4">
                                    {getStatusIcon(data?.run?.overall_status || 'UNKNOWN')}
                                    <div>
                                        <h2 className="text-xl font-bold">{data?.run?.overall_status?.replace('_', ' ')}</h2>
                                        <p className="text-gray-600">
                                            NSE: {data?.run?.nse?.toFixed(3)} |
                                            KGE: {data?.run?.kge?.toFixed(3)} |
                                            CV: {data?.run?.cv_obs?.toFixed(3)}
                                        </p>
                                    </div>
                                </div>
                                {(data as any).is_preview && (
                                    <div className="flex items-center gap-2 bg-blue-50 px-3 py-2 rounded text-blue-700 text-sm font-medium border border-blue-200 animate-pulse">
                                        <Activity size={16} />
                                        Preview Mode (Unsaved)
                                    </div>
                                )}
                            </div>
                        </div>
                    </>
                ) : (
                    /* Shape Fit View */
                    <div className="bg-white rounded-lg border border-gray-200 p-6 h-[700px] flex flex-col">
                        <div className="flex items-center justify-between mb-6 shrink-0">
                            <div className="flex items-center gap-2">
                                <BarChart2 className="text-purple-600" />
                                <h3 className="text-lg font-semibold">Shape Fit (Observed vs Predicted)</h3>
                            </div>
                            <div className="text-sm bg-gray-50 px-3 py-2 rounded-lg border flex gap-4">
                                <span className="font-semibold" title="NSE">NSE: {data?.run?.nse?.toFixed(3)}</span>
                                <span className="font-semibold" title="KGE">KGE: {data?.run?.kge?.toFixed(3)}</span>
                                <span className="font-semibold" title="CV">CV: {data?.run?.cv_obs?.toFixed(3)}</span>
                            </div>
                        </div>
                        <div className="flex-1 w-full min-h-0">
                            <ResponsiveContainer width="100%" height="100%">
                                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                    <CartesianGrid />
                                    <XAxis type="number" dataKey="observed" name="Observed" label={{ value: 'Observed Flow', position: 'bottom', offset: 0 }} domain={[0, maxScatterVal]} />
                                    <YAxis type="number" dataKey="predicted" name="Predicted" label={{ value: 'Predicted Flow', angle: -90, position: 'insideLeft' }} domain={[0, maxScatterVal]} />
                                    <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={chartTooltipFormatter} />
                                    <Legend />
                                    <Scatter name="Flow Correlation" data={flowScatterData} fill="#8884d8" />
                                    <ReferenceLine segment={[{ x: 0, y: 0 }, { x: maxScatterVal, y: maxScatterVal }]} stroke="green" strokeDasharray="3 3" label="Perfect Fit (1:1)" />
                                </ScatterChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
