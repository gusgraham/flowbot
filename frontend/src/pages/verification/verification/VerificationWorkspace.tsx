import { useState, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, CheckCircle, AlertTriangle, XCircle, Activity, Droplets, Settings, BarChart2, RefreshCw } from 'lucide-react';
import { useWorkspaceData } from '../../../api/hooks';
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

// Analysis Controls Component to isolate re-renders
interface AnalysisControlsProps {
    currentParams: {
        smoothing_obs: number;
        smoothing_pred: number;
        max_peaks_obs?: number;
        max_peaks_pred?: number;
    };
    onApply: (params: any) => void;
    isFetching: boolean;
    onClose: () => void;
}

const AnalysisControls = ({ currentParams, onApply, isFetching, onClose }: AnalysisControlsProps) => {
    // Local state for inputs
    const [smoothingObs, setSmoothingObs] = useState(currentParams.smoothing_obs);
    const [smoothingPred, setSmoothingPred] = useState(currentParams.smoothing_pred);
    const [maxPeaksObs, setMaxPeaksObs] = useState<number | ''>(currentParams.max_peaks_obs ?? '');
    const [maxPeaksPred, setMaxPeaksPred] = useState<number | ''>(currentParams.max_peaks_pred ?? '');

    const handleApply = () => {
        onApply({
            smoothing_obs: smoothingObs,
            smoothing_pred: smoothingPred,
            max_peaks_obs: maxPeaksObs === '' ? undefined : Number(maxPeaksObs),
            max_peaks_pred: maxPeaksPred === '' ? undefined : Number(maxPeaksPred)
        });
    };

    const handleReset = () => {
        setSmoothingObs(0);
        setSmoothingPred(0);
        setMaxPeaksObs('');
        setMaxPeaksPred('');
        onApply({
            smoothing_obs: 0,
            smoothing_pred: 0,
            max_peaks_obs: undefined,
            max_peaks_pred: undefined
        });
    };

    return (
        <div className="bg-white rounded-lg border border-gray-200 p-4 shadow-sm animate-in slide-in-from-top-2">
            <div className="flex flex-col md:flex-row md:items-end gap-6">
                <div className="space-y-4 flex-1">
                    <h4 className="font-semibold text-gray-700 text-sm">Smoothing (0.0 - 1.0)</h4>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs text-gray-500 mb-1">Observed Smoothing</label>
                            <input
                                type="number" min="0" max="1" step="0.01"
                                value={smoothingObs}
                                onChange={(e) => setSmoothingObs(parseFloat(e.target.value))}
                                className="w-full px-3 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 font-mono"
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-gray-500 mb-1">Predicted Smoothing</label>
                            <input
                                type="number" min="0" max="1" step="0.01"
                                value={smoothingPred}
                                onChange={(e) => setSmoothingPred(parseFloat(e.target.value))}
                                className="w-full px-3 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 font-mono"
                            />
                        </div>
                    </div>
                </div>

                <div className="space-y-4 flex-1">
                    <h4 className="font-semibold text-gray-700 text-sm">Peak Detection</h4>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs text-gray-500 mb-1">Max Peaks (Obs)</label>
                            <input
                                type="number" min="0"
                                value={maxPeaksObs}
                                onChange={(e) => setMaxPeaksObs(e.target.value === '' ? '' : parseInt(e.target.value))}
                                placeholder="Auto"
                                className="w-full px-3 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                        <div>
                            <label className="block text-xs text-gray-500 mb-1">Max Peaks (Pred)</label>
                            <input
                                type="number" min="0"
                                value={maxPeaksPred}
                                onChange={(e) => setMaxPeaksPred(e.target.value === '' ? '' : parseInt(e.target.value))}
                                placeholder="Auto"
                                className="w-full px-3 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500"
                            />
                        </div>
                    </div>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={handleReset}
                        className="px-4 py-2 text-sm text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-md font-medium"
                    >
                        Reset
                    </button>
                    <button
                        onClick={handleApply}
                        disabled={isFetching}
                        className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-md font-medium flex items-center gap-2 disabled:opacity-50"
                    >
                        {isFetching ? <RefreshCw className="animate-spin" size={16} /> : null}
                        Apply Analysis
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

    // Analysis State
    const [showControls, setShowControls] = useState(false);
    const [viewMode, setViewMode] = useState<'timeseries' | 'shapefit'>('timeseries');

    // Applied Parameters (trigger fetch) - State moved to AnalysisControls
    const [appliedParams, setAppliedParams] = useState({
        smoothing_obs: 0,
        smoothing_pred: 0,
        max_peaks_obs: undefined as number | undefined,
        max_peaks_pred: undefined as number | undefined
    });

    const { data, isLoading, error, isFetching } = useWorkspaceData(effectiveRunId, appliedParams);

    // Memoize chart data to avoid expensive recalculation on every render (e.g. when typing in inputs)
    const { flowChartData, depthChartData, flowScatterData, maxScatterVal } = useMemo(() => {
        // Handle null data gracefully inside the hook
        if (!data) return { flowChartData: [], depthChartData: [], flowScatterData: [], maxScatterVal: 0 };

        const rawFlowData = data?.series?.obs_flow?.time.map((time, i) => ({
            time: formatTime(time),
            original_time: time,
            observed: data.series.obs_flow?.values[i],
            predicted: data.series.pred_flow?.values[i],
            obs_smoothed: data.series.obs_flow_smoothed?.values[i],
            pred_smoothed: data.series.pred_flow_smoothed?.values[i]
        })) || [];

        const flowChartData = downsample(rawFlowData, 1000);

        const rawDepthData = data?.series?.obs_depth?.time.map((time, i) => ({
            time: formatTime(time),
            observed: data.series.obs_depth?.values[i],
            predicted: data.series.pred_depth?.values[i],
            obs_smoothed: data.series.obs_depth_smoothed?.values[i],
            pred_smoothed: data.series.pred_depth_smoothed?.values[i]
        })) || [];

        const depthChartData = downsample(rawDepthData, 1000);

        const flowScatterData = downsample(data?.series?.obs_flow?.values.map((obs, i) => ({
            observed: obs,
            predicted: data.series.pred_flow?.values[i]
        })).filter(d => d.observed != null && d.predicted != null) || [], 2000);

        const maxScatterVal = Math.max(
            ...flowScatterData.map(d => Math.max(d.observed, d.predicted || 0))
        );

        return { flowChartData, depthChartData, flowScatterData, maxScatterVal };
    }, [data]);

    if (isLoading && !data) {
        return (
            <div className="p-6">
                <div className="animate-pulse space-y-4">
                    <div className="h-8 bg-gray-200 rounded w-1/3"></div>
                    <div className="h-64 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    if (error || (!isLoading && !data)) {
        return (
            <div className="p-6">
                <div className="text-red-500">Error loading workspace data</div>
                <button onClick={() => navigate(-1)} className="mt-4 text-blue-600 hover:underline">
                    Go back
                </button>
            </div>
        );
    }

    if (!data) return null;

    // Helper for status styles
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

    // Metric Labels Mapping
    const METRIC_LABELS: Record<string, string> = {
        'peak_time_diff': 'Peak Time Diff (hrs)',
        'peak_diff_pct': 'Peak Diff (%)',
        'peak_diff_abs': 'Peak Diff (m)',
        'volume_diff_pct': 'Volume Diff (%)',
        'peak_diff': 'Peak Diff (m)', // Depth often uses this
        'nse': 'NSE',
        'kge': 'KGE',
        'cv': 'CV',
        // Fallbacks for generic keys (PREVIEW MODE / Legacy)
        'peak_time': 'Peak Time Diff (hrs)',
        'peak_flow': 'Peak Diff (%)',
        'peak_depth': 'Peak Diff (m)',
        'volume': 'Volume Diff (%)'
    };

    const getMetricLabel = (name: string) => {
        const lowerName = name.toLowerCase();
        // Handle specific keys or fallback to space-separated
        const key = Object.keys(METRIC_LABELS).find(k => lowerName.includes(k));

        if (METRIC_LABELS[lowerName]) return METRIC_LABELS[lowerName];
        if (key) return METRIC_LABELS[key];
        // Handle variations like 'peak_time_diff_hrs' if needed
        if (lowerName === 'peak_time_diff_hrs') return 'Peak Time Diff (hrs)';

        return name.replace(/_/g, ' ');
    };



    const chartTooltipFormatter = (value: number) => {
        if (value == null) return '';
        return value.toFixed(3);
    };

    return (
        <div className="p-6 space-y-6 bg-gray-50 min-h-screen">
            {/* Header */}
            <div className="flex items-center justify-between">
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
                <AnalysisControls
                    currentParams={appliedParams}
                    onApply={setAppliedParams}
                    isFetching={isFetching}
                    onClose={() => setShowControls(false)}
                />
            )}

            {/* Content: Timeseries vs Shape Fit */}
            {viewMode === 'timeseries' ? (
                <>
                    {/* Flow Chart (Moved to Top) */}
                    {flowChartData.length > 0 && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <h3 className="text-lg font-semibold mb-4">Flow Comparison</h3>
                            <ResponsiveContainer width="100%" height={400}>
                                <LineChart data={flowChartData}>
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
                                        stroke="#2563eb"
                                        strokeWidth={2}
                                        dot={false}
                                        name="Observed (Raw)"
                                        opacity={data.series.obs_flow_smoothed ? 0.3 : 1}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="predicted"
                                        stroke="#dc2626"
                                        strokeWidth={2}
                                        dot={false}
                                        name="Predicted (Raw)"
                                        opacity={data.series.pred_flow_smoothed ? 0.3 : 1}
                                    />
                                    {/* Smoothed lines */}
                                    {data.series.obs_flow_smoothed && (
                                        <Line
                                            type="monotone"
                                            dataKey="obs_smoothed"
                                            stroke="#1e40af"
                                            strokeWidth={2}
                                            dot={false}
                                            name="Observed (Smoothed)"
                                        />
                                    )}
                                    {data.series.pred_flow_smoothed && (
                                        <Line
                                            type="monotone"
                                            dataKey="pred_smoothed"
                                            stroke="#991b1b"
                                            strokeWidth={2}
                                            dot={false}
                                            name="Predicted (Smoothed)"
                                        />
                                    )}
                                    {/* Peak markers */}
                                    {data?.peaks?.obs_flow?.map((peak, i) => (
                                        <ReferenceDot
                                            key={`obs-peak-${i}`}
                                            x={new Date(peak.time).toLocaleString()}
                                            y={peak.value}
                                            r={6}
                                            fill="#2563eb"
                                            stroke="#fff"
                                        />
                                    ))}
                                    {data?.peaks?.pred_flow?.map((peak, i) => (
                                        <ReferenceDot
                                            key={`pred-peak-${i}`}
                                            x={new Date(peak.time).toLocaleString()}
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

                    {/* Depth Chart (Moved to Top) */}
                    {depthChartData.length > 0 && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
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
                                        stroke="#0891b2"
                                        strokeWidth={2}
                                        dot={false}
                                        name="Observed (Raw)"
                                        opacity={data.series.obs_depth_smoothed ? 0.3 : 1}
                                    />
                                    <Line
                                        type="monotone"
                                        dataKey="predicted"
                                        stroke="#c026d3"
                                        strokeWidth={2}
                                        dot={false}
                                        name="Predicted (Raw)"
                                        opacity={data.series.pred_depth_smoothed ? 0.3 : 1}
                                    />
                                    {/* Smoothed lines */}
                                    {data.series.obs_depth_smoothed && (
                                        <Line
                                            type="monotone"
                                            dataKey="obs_smoothed"
                                            stroke="#0e7490"
                                            strokeWidth={2}
                                            dot={false}
                                            name="Observed (Smoothed)"
                                        />
                                    )}
                                    {data.series.pred_depth_smoothed && (
                                        <Line
                                            type="monotone"
                                            dataKey="pred_smoothed"
                                            stroke="#a21caf"
                                            strokeWidth={2}
                                            dot={false}
                                            name="Predicted (Smoothed)"
                                        />
                                    )}
                                    {/* Peak markers for observed */}
                                    {data.peaks.obs_depth?.map((peak, i) => (
                                        <ReferenceDot
                                            key={`obs-peak-${i}`}
                                            x={new Date(peak.time).toLocaleString()}
                                            y={peak.value}
                                            r={6}
                                            fill="#0891b2"
                                            stroke="#fff"
                                        />
                                    ))}
                                    {/* Peak markers for predicted */}
                                    {data.peaks.pred_depth?.map((peak, i) => (
                                        <ReferenceDot
                                            key={`pred-peak-${i}`}
                                            x={new Date(peak.time).toLocaleString()}
                                            y={peak.value}
                                            r={6}
                                            fill="#c026d3"
                                            stroke="#fff"
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    )}

                    {/* Flow Metrics (Middle) */}
                    <div className="bg-white rounded-lg border border-gray-200 p-6">
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

                    {/* Depth Metrics (Middle) */}
                    {data.metrics.depth && data.metrics.depth.length > 0 && (
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
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

                    {/* Status Card (Bottom) */}
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
                                <div className="flex items-center gap-2 bg-blue-50 px-3 py-2 rounded text-blue-700 text-sm font-medium border border-blue-200">
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
                            <span className="font-semibold cursor-help border-b border-dotted border-gray-400" title="Nash-Sutcliffe Efficiency: 1.0 is perfect, >0.5 is good.">
                                NSE: {data?.run?.nse?.toFixed(3)}
                            </span>
                            <span className="font-semibold cursor-help border-b border-dotted border-gray-400" title="Kling-Gupta Efficiency: Combines correlation, variability, and bias. 1.0 is perfect.">
                                KGE: {data?.run?.kge?.toFixed(3)}
                            </span>
                            <span className="font-semibold cursor-help border-b border-dotted border-gray-400" title="Coefficient of Variation: Measures observed data variability (std dev / mean).">
                                CV: {data?.run?.cv_obs?.toFixed(3)}
                            </span>
                        </div>
                    </div>

                    <div className="flex-1 w-full min-h-0">
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart
                                margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                            >
                                <CartesianGrid />
                                <XAxis
                                    type="number"
                                    dataKey="observed"
                                    name="Observed"
                                    label={{ value: 'Observed Flow', position: 'bottom', offset: 0 }}
                                    domain={[0, maxScatterVal]}
                                />
                                <YAxis
                                    type="number"
                                    dataKey="predicted"
                                    name="Predicted"
                                    label={{ value: 'Predicted Flow', angle: -90, position: 'insideLeft' }}
                                    domain={[0, maxScatterVal]}
                                />
                                <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={chartTooltipFormatter} />
                                <Legend />
                                <Scatter name="Flow Correlation" data={flowScatterData} fill="#8884d8" />
                                <ReferenceLine
                                    segment={[{ x: 0, y: 0 }, { x: maxScatterVal, y: maxScatterVal }]}
                                    stroke="green"
                                    strokeDasharray="3 3"
                                    label="Perfect Fit (1:1)"
                                />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            )}

        </div>
    );
}
