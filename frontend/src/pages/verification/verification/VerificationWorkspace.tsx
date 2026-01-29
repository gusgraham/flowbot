import { useState, useMemo, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';
import { ArrowLeft, CheckCircle, AlertTriangle, XCircle, Activity, Droplets, Settings, BarChart2, RefreshCw, X, MousePointer2, Camera } from 'lucide-react';
import html2canvas from 'html2canvas';
import { useWorkspaceData, useUpdateVerificationRunSettings, useUpdateVerificationRun, type AnalysisSettings } from '../../../api/hooks';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceDot,
    ScatterChart, Scatter, ReferenceLine, BarChart, Bar, Cell, ReferenceArea, Customized
} from 'recharts';

interface VerificationWorkspaceProps {
    runId?: number | null;
    embedded?: boolean;
}

// Simple decimation downsampling (moved outside component)
const downsample = <T,>(data: T[], targetPoints: number = 50000): T[] => {
    if (!data || data.length <= targetPoints) return data;
    const step = Math.ceil(data.length / targetPoints);
    return data.filter((_, i) => i % step === 0);
};

const formatTime = (isoString: string) => new Date(isoString).toLocaleString();

// Compact date formatter for chart axis (show "12 Dec 14:00" format)
const formatAxisDate = (value: string | number) => {
    const d = new Date(value);
    const day = d.getDate();
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const month = months[d.getMonth()];
    const hours = d.getHours().toString().padStart(2, '0');
    const mins = d.getMinutes().toString().padStart(2, '0');
    return `${day} ${month} ${hours}:${mins}`;
};

// Analysis Controls Component
type EditSeriesType = 'obs_flow' | 'pred_flow' | 'obs_depth' | 'pred_depth' | null;

interface AnalysisControlsProps {
    currentSettings: AnalysisSettings;
    onSettingsChange: (settings: AnalysisSettings) => void;
    onApply: () => void;
    isFetching: boolean;
    onClose: () => void;
    editSeries: EditSeriesType;
    setEditSeries: (series: EditSeriesType) => void;
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
    const [maxPeaks, setMaxPeaks] = useState<number | ''>(currentSettings.max_peaks ?? 1);
    const [peakMode, setPeakMode] = useState<'auto' | 'manual'>(currentSettings.peak_mode ?? 'auto');

    // Sync local state when props change (e.g. initial load)
    useEffect(() => {
        setSmoothingObs(currentSettings.smoothing_obs ?? 0);
        setSmoothingPred(currentSettings.smoothing_pred ?? 0);
        setMaxPeaks(currentSettings.max_peaks ?? 1);
        setPeakMode(currentSettings.peak_mode ?? 'auto');
    }, [currentSettings.smoothing_obs, currentSettings.smoothing_pred, currentSettings.max_peaks, currentSettings.peak_mode]);

    // Update parent settings whenever inputs change
    useEffect(() => {
        onSettingsChange({
            ...currentSettings,
            smoothing_obs: smoothingObs,
            smoothing_pred: smoothingPred,
            max_peaks: maxPeaks === '' ? undefined : Number(maxPeaks),
            peak_mode: peakMode
        });
    }, [smoothingObs, smoothingPred, maxPeaks, peakMode]);

    const handleReset = () => {
        setSmoothingObs(0);
        setSmoothingPred(0);
        setMaxPeaks(1);
        setPeakMode('auto');
        setEditSeries(null);
        onSettingsChange({
            smoothing_obs: 0,
            smoothing_pred: 0,
            max_peaks: 1,
            peak_mode: 'auto',
            manual_peaks: {}
        });
    };

    return (
        <div className="bg-white rounded-lg border border-gray-200 p-3 shadow-sm animate-in slide-in-from-top-2 relative mb-3">
            <button
                onClick={onClose}
                className="absolute top-2 right-2 p-1 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100"
            >
                <X size={16} />
            </button>

            {/* Header with Reset, Apply, and Auto/Manual toggle */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wide">Analysis Settings</span>
                    <button
                        onClick={handleReset}
                        className="px-2 py-0.5 text-xs text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                    >
                        Reset
                    </button>
                    <button
                        onClick={() => { onApply(); onClose(); }}
                        disabled={isFetching}
                        className="px-2 py-0.5 text-xs font-medium bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                    >
                        {isFetching ? 'Saving...' : 'Apply'}
                    </button>
                </div>
                <div className="flex bg-gray-100 rounded p-0.5">
                    <button
                        onClick={() => { setPeakMode('auto'); setEditSeries(null); }}
                        className={`px-2 py-0.5 text-xs font-medium rounded ${peakMode === 'auto' ? 'bg-white shadow text-blue-700' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Auto
                    </button>
                    <button
                        onClick={() => setPeakMode('manual')}
                        className={`px-2 py-0.5 text-xs font-medium rounded ${peakMode === 'manual' ? 'bg-white shadow text-blue-700' : 'text-gray-500 hover:text-gray-700'}`}
                    >
                        Manual
                    </button>
                </div>
            </div>

            {/* Compact controls in a single row */}
            <div className="flex items-end gap-4 flex-wrap">
                {/* Smoothing */}
                <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-500 whitespace-nowrap">Smoothing:</span>
                    <div className="flex items-center gap-1">
                        <label className="text-xs font-medium" style={{ color: '#15803d' }}>Obs</label>
                        <input
                            type="number" min="0" max="1" step="0.01"
                            value={smoothingObs}
                            onChange={(e) => setSmoothingObs(parseFloat(e.target.value))}
                            className="w-14 px-1.5 py-0.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 font-mono"
                        />
                    </div>
                    <div className="flex items-center gap-1">
                        <label className="text-xs font-medium" style={{ color: '#dc2626' }}>Pred</label>
                        <input
                            type="number" min="0" max="1" step="0.01"
                            value={smoothingPred}
                            onChange={(e) => setSmoothingPred(parseFloat(e.target.value))}
                            className="w-14 px-1.5 py-0.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 font-mono"
                        />
                    </div>
                </div>

                <div className="h-4 w-px bg-gray-200" />

                {/* Peak Controls */}
                {peakMode === 'auto' ? (
                    <div className="flex items-center gap-2">
                        <label className="text-xs text-gray-500 whitespace-nowrap">Max Peaks:</label>
                        <input
                            type="number" min="1" step="1"
                            placeholder="All"
                            value={maxPeaks}
                            onChange={(e) => setMaxPeaks(e.target.value === '' ? '' : parseInt(e.target.value))}
                            className="w-14 px-1.5 py-0.5 text-xs border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 font-mono"
                        />
                    </div>
                ) : (
                    <div className="flex items-center gap-4">
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-gray-500">Flow:</span>
                            <button
                                onClick={() => setEditSeries(editSeries === 'obs_flow' ? null : 'obs_flow')}
                                className={`flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded border transition-colors ${editSeries === 'obs_flow' ? 'bg-green-100 border-green-500 text-green-800' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
                            >
                                <MousePointer2 size={12} />
                                {editSeries === 'obs_flow' ? 'Selecting...' : 'Obs'}
                            </button>
                            <button
                                onClick={() => setEditSeries(editSeries === 'pred_flow' ? null : 'pred_flow')}
                                className={`flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded border transition-colors ${editSeries === 'pred_flow' ? 'bg-red-100 border-red-500 text-red-800' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
                            >
                                <MousePointer2 size={12} />
                                {editSeries === 'pred_flow' ? 'Selecting...' : 'Pred'}
                            </button>
                        </div>
                        <div className="flex items-center gap-1">
                            <span className="text-xs text-gray-500">Depth:</span>
                            <button
                                onClick={() => setEditSeries(editSeries === 'obs_depth' ? null : 'obs_depth')}
                                className={`flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded border transition-colors ${editSeries === 'obs_depth' ? 'bg-green-100 border-green-500 text-green-800' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
                            >
                                <MousePointer2 size={12} />
                                {editSeries === 'obs_depth' ? 'Selecting...' : 'Obs'}
                            </button>
                            <button
                                onClick={() => setEditSeries(editSeries === 'pred_depth' ? null : 'pred_depth')}
                                className={`flex items-center gap-1 px-2 py-0.5 text-xs font-medium rounded border transition-colors ${editSeries === 'pred_depth' ? 'bg-red-100 border-red-500 text-red-800' : 'bg-white border-gray-300 text-gray-700 hover:bg-gray-50'}`}
                            >
                                <MousePointer2 size={12} />
                                {editSeries === 'pred_depth' ? 'Selecting...' : 'Pred'}
                            </button>
                        </div>
                    </div>
                )}

                {isFetching && (
                    <span className="text-xs text-gray-400 ml-auto">Updating...</span>
                )}
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


    const workspaceRef = useRef<HTMLDivElement>(null);
    const [isCapturing, setIsCapturing] = useState(false);

    // Manual Peak Editing State
    const [editSeries, setEditSeries] = useState<EditSeriesType>(null);

    // Analysis Settings State - Default to 1 peak for cleaner visualization
    const [analysisSettings, setAnalysisSettings] = useState<AnalysisSettings>({
        max_peaks: 1
    });

    // Fetch Data
    const { data, isLoading, error, isFetching, refetch } = useWorkspaceData(effectiveRunId, analysisSettings);
    const updateSettingsMutation = useUpdateVerificationRunSettings();
    const updateRunMutation = useUpdateVerificationRun();

    // Depth Only State
    const [isDepthOnly, setIsDepthOnly] = useState(false);
    const [depthOnlyComment, setDepthOnlyComment] = useState('');

    // Effective Depth Only (Monitor setting takes precedence)
    const isMonitorDepthOnly = (data as any)?.monitor?.is_depth_only ?? false;
    const effectiveDepthOnly = isDepthOnly || isMonitorDepthOnly;

    // Initialize local settings from server data on load
    // IMPORTANT: Only reset when runId actually changes, not on every data fetch
    const prevRunIdRef = useRef<number | null>(null);

    useEffect(() => {
        // Only reset if runId actually changed
        if (effectiveRunId === prevRunIdRef.current) {
            return; // Same runId, don't reset
        }

        // RunId changed - update ref and reset settings
        prevRunIdRef.current = effectiveRunId;

        const defaults: AnalysisSettings = {
            smoothing_obs: 0,
            smoothing_pred: 0,
            max_peaks: 1,
            peak_mode: 'auto',
            manual_peaks: {}
        };

        if (data?.run?.analysis_settings && Object.keys(data.run.analysis_settings).length > 0) {
            // Server has saved settings - merge them over defaults
            setAnalysisSettings({
                ...defaults,
                ...data.run.analysis_settings
            });
        } else {
            // No server settings - use defaults
            setAnalysisSettings(defaults);
        }


        // Sync Depth Only state
        if (data?.run) {
            setIsDepthOnly(data.run.is_depth_only || false);
            setDepthOnlyComment(data.run.depth_only_comment || '');
        }

        // Force view mode if depth only
        if ((data?.run?.is_depth_only || (data as any)?.monitor?.is_depth_only) && viewMode !== 'timeseries') {
            setViewMode('timeseries');
        }
    }, [effectiveRunId, data?.run?.analysis_settings, data?.run?.is_depth_only, data?.run?.depth_only_comment, (data as any)?.monitor?.is_depth_only]);

    const handleDepthOverrideChange = (checked: boolean) => {
        setIsDepthOnly(checked);
        if (checked) {
            setViewMode('timeseries');
        }
        if (effectiveRunId) {
            updateRunMutation.mutate({
                runId: effectiveRunId,
                update: { is_depth_only: checked }
            }, {
                onSuccess: () => refetch()
            });
        }
    };

    const handleDepthCommentSave = () => {
        if (effectiveRunId) {
            updateRunMutation.mutate({
                runId: effectiveRunId,
                update: { depth_only_comment: depthOnlyComment }
            });
        }
    };

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

    const handleCapture = async () => {
        if (!workspaceRef.current) return;
        setIsCapturing(true);

        try {
            // Wait for any renders
            await new Promise(resolve => setTimeout(resolve, 100));

            // Create a clone of the element to render full height
            const element = workspaceRef.current;
            const clone = element.cloneNode(true) as HTMLElement;

            // Style the clone to be full height and invisible but rendered
            clone.style.position = 'fixed'; // Fixed to viewport
            clone.style.top = '0';
            clone.style.left = '0';
            clone.style.width = `${element.offsetWidth}px`; // Match original width
            clone.style.height = 'auto'; // Let it grow to full height
            clone.style.overflow = 'visible'; // Show all content
            clone.style.zIndex = '-9999'; // Behind everything
            clone.style.background = '#f9fafb'; // Ensure background color (bg-gray-50)

            // Append to body to render
            document.body.appendChild(clone);

            // Wait a tick for layout
            await new Promise(resolve => setTimeout(resolve, 100));

            // Capture the clone
            const canvas = await html2canvas(clone, {
                useCORS: true,
                scale: 2,
                logging: false,
                height: clone.scrollHeight,
                windowHeight: clone.scrollHeight,
                scrollY: 0, // IMPORTANT: Ignore window scroll
                x: 0,
                y: 0
            });

            // Cleanup
            document.body.removeChild(clone);

            const image = canvas.toDataURL("image/png");

            // Create download link
            const link = document.createElement('a');
            link.href = image;
            link.download = `verification_trace_${data?.monitor?.name}_${data?.event?.name}.png`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (err) {
            console.error('Screen capture failed:', err);
        } finally {
            setIsCapturing(false);
        }
    };

    // Determine if current editSeries is for flow or depth chart
    const isFlowSeries = editSeries === 'obs_flow' || editSeries === 'pred_flow';
    const isDepthSeries = editSeries === 'obs_depth' || editSeries === 'pred_depth';

    const handleChartClick = (chartType: 'flow' | 'depth') => (e: any) => {
        console.log('Chart Click Event:', chartType, e);
        if (analysisSettings.peak_mode !== 'manual' || !editSeries) {
            //console.log('Click ignored: Not in manual mode or no series selected', { peakMode: analysisSettings.peak_mode, editSeries });
            return;
        }

        // Ensure we're clicking on the right chart for the selected series
        if (chartType === 'flow' && !isFlowSeries) {
            //console.log('Click ignored: Flow chart clicked but depth series selected');
            return;
        }
        if (chartType === 'depth' && !isDepthSeries) {
            //console.log('Click ignored: Depth chart clicked but flow series selected');
            return;
        }

        // Recharts gives 'activeLabel' which matches our XAxis dataKey 'iso_time' (raw ISO string)
        const clickedLabel = e?.activeLabel;

        if (!clickedLabel) {
            //console.log('Click ignored: No activeLabel in event');
            return;
        }

        //console.log('Processing click for label:', clickedLabel);

        // Find existing peaks for this series
        const currentPeaks = analysisSettings.manual_peaks?.[editSeries] || [];

        // Use the appropriate chart data based on chart type
        const chartData = chartType === 'flow' ? flowChartData : depthChartData;

        // Find data point to get ISO for clicked label
        // activeLabel comes from XAxis dataKey 'timestamp' (number)
        // We need to find the corresponding ISO time string from the data
        let clickedIso: string | undefined;
        let dataPoint: any;

        if (typeof clickedLabel === 'number') {
            dataPoint = chartData.find(d => d.timestamp === clickedLabel);
            clickedIso = dataPoint?.iso_time;
        } else {
            // Fallback if it's already a string (shouldn't happen with type="number" axis)
            clickedIso = clickedLabel;
            dataPoint = chartData.find(d => d.iso_time === clickedLabel);
        }

        if (!clickedIso) {
            console.warn('Click ignored: Could not resolve ISO time for label:', clickedLabel);
            return;
        }

        const existingIndex = currentPeaks.findIndex(p => p.time === clickedIso);

        let newPeaks;
        if (existingIndex >= 0) {
            // Remove
            //console.log('Removing existing peak at:', clickedLabel);
            newPeaks = currentPeaks.filter((_, i) => i !== existingIndex);
        } else {
            // Add
            // Try to find value from activePayload first (tooltip data)
            let valueToAdd: number | undefined;

            if (e.activePayload && e.activePayload.length > 0) {
                const payloadItem = e.activePayload.find((p: any) => {
                    if (editSeries === 'obs_flow' || editSeries === 'obs_depth') return p.dataKey === 'observed' || p.dataKey === 'obs_smoothed';
                    if (editSeries === 'pred_flow' || editSeries === 'pred_depth') return p.dataKey === 'predicted' || p.dataKey === 'pred_smoothed';
                    return false;
                });
                if (payloadItem) {
                    valueToAdd = Number(payloadItem.value);
                }
            }

            // Fallback: Look up in chart data directly using the resolved dataPoint
            if (valueToAdd === undefined && dataPoint) {
                if (editSeries === 'obs_flow' || editSeries === 'obs_depth') valueToAdd = (dataPoint.obs_smoothed as number) ?? (dataPoint.observed as number);
                if (editSeries === 'pred_flow' || editSeries === 'pred_depth') valueToAdd = (dataPoint.pred_smoothed as number) ?? (dataPoint.predicted as number);
            }

            if (valueToAdd !== undefined && valueToAdd !== null && clickedIso) {
                //console.log('Adding new peak:', { time: clickedIso, value: valueToAdd });
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

    const { flowChartData, depthChartData, velocityChartData, flowScatterData } = useMemo(() => {
        if (!data?.series) return { flowChartData: [], depthChartData: [], velocityChartData: [], flowScatterData: [] };

        // Helper to merge obs and pred series by timestamp (not index!)
        const mergeSeries = (obsData: { time: string[], values: number[] } | undefined,
            predData: { time: string[], values: number[] } | undefined,
            obsSmoothData?: { time: string[], values: number[] } | undefined,
            predSmoothData?: { time: string[], values: number[] } | undefined) => {
            const timeMap = new Map<string, any>();

            // Add observed data
            if (obsData) {
                obsData.time.forEach((t, i) => {
                    timeMap.set(t, {
                        time: formatTime(t),
                        iso_time: t,
                        timestamp: new Date(t).getTime(),
                        observed: obsData.values[i],
                        predicted: null,
                        obs_smoothed: null,
                        pred_smoothed: null
                    });
                });
            }

            // Add/merge predicted data
            if (predData) {
                predData.time.forEach((t, i) => {
                    if (timeMap.has(t)) {
                        timeMap.get(t).predicted = predData.values[i];
                    } else {
                        timeMap.set(t, {
                            time: formatTime(t),
                            iso_time: t,
                            timestamp: new Date(t).getTime(),
                            observed: null,
                            predicted: predData.values[i],
                            obs_smoothed: null,
                            pred_smoothed: null
                        });
                    }
                });
            }

            // Add smoothed observed
            if (obsSmoothData) {
                obsSmoothData.time.forEach((t, i) => {
                    if (timeMap.has(t)) {
                        timeMap.get(t).obs_smoothed = obsSmoothData.values[i];
                    }
                });
            }

            // Add smoothed predicted
            if (predSmoothData) {
                predSmoothData.time.forEach((t, i) => {
                    if (timeMap.has(t)) {
                        timeMap.get(t).pred_smoothed = predSmoothData.values[i];
                    }
                });
            }

            // Sort by timestamp and downsample
            const sorted = Array.from(timeMap.values()).sort((a, b) =>
                new Date(a.iso_time).getTime() - new Date(b.iso_time).getTime()
            );

            return downsample(sorted);
        };

        const flowChartData = mergeSeries(
            data.series.obs_flow,
            data.series.pred_flow,
            data.series.obs_flow_smoothed,
            data.series.pred_flow_smoothed
        );

        const depthChartData = mergeSeries(
            data.series.obs_depth,
            data.series.pred_depth,
            data.series.obs_depth_smoothed,
            data.series.pred_depth_smoothed
        );

        // Velocity data merged the same way
        const velocityChartData = mergeSeries(
            data.series.obs_velocity,
            data.series.pred_velocity
        );

        // Scatter data - only include points where both obs and pred exist
        const flowScatterData = flowChartData
            .filter(d => d.observed != null && d.predicted != null)
            .map(d => ({ observed: d.observed, predicted: d.predicted }));

        return { flowChartData, depthChartData, velocityChartData, flowScatterData };
    }, [data?.series]);

    // Peaks to display: Prioritize local manuals if mode is manual, otherwise use server peaks
    const displayPeaks = useMemo(() => {
        if (analysisSettings.peak_mode === 'manual') {
            const manual = analysisSettings.manual_peaks || {};
            return {
                obs_flow: manual.obs_flow || [],
                pred_flow: manual.pred_flow || [],
                obs_depth: manual.obs_depth || [],
                pred_depth: manual.pred_depth || [],
            };
        }
        // Auto mode or initial load: use server provided peaks (formatted with time string already?)
        // Server peaks have `time` as ISO? Check backend workspace.
        // Backend `get_run_workspace`: `peaks_data` items have `time` formatted as `strftime('%Y-%m-%dT%H:%M:%S')`.
        // This IS an ISO-like string. The Chart data `iso_time` matches this format.
        // So we can pass `p` directly, interpreting `p.time` as the `x` value.
        return {
            obs_flow: data?.peaks?.obs_flow || [],
            pred_flow: data?.peaks?.pred_flow || [],
            obs_depth: data?.peaks?.obs_depth || [],
            pred_depth: data?.peaks?.pred_depth || []
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
        const labels: Record<string, string> = {
            // Coefficients
            'nse': 'NSE',
            'kge': 'KGE',
            'cv_obs': 'CV (Obs)',

            // Flow metrics
            'peak_time_diff_hrs': 'Peak Time Diff (hrs)',
            'peak_flow_diff_pcnt': 'Peak Flow Diff (%)',
            'volume_diff_pcnt': 'Volume Diff (%)',

            // Depth metrics
            'peak_depth_diff_m': 'Peak Depth Diff (m)',
        };
        return labels[name] || name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

    const formatTooltipLabel = (value: number) => {
        if (!value) return '';
        return new Date(value).toLocaleString();
    };

    // Summary statistics for the summary table
    const summaryStats = useMemo(() => {
        if (!data?.series) return null;

        const calcStats = (values: number[] | undefined) => {
            if (!values || values.length === 0) return { min: null, max: null };
            const filtered = values.filter(v => v != null && !isNaN(v));
            if (filtered.length === 0) return { min: null, max: null };
            return {
                min: Math.min(...filtered),
                max: Math.max(...filtered)
            };
        };

        const calcVolume = (values: number[] | undefined, timestepMinutes: number) => {
            if (!values || values.length === 0) return null;
            const filtered = values.filter(v => v != null && !isNaN(v));
            if (filtered.length === 0) return null;
            // Volume = sum of flow * timestep (convert minutes to seconds)
            const timestepSeconds = timestepMinutes * 60;
            return filtered.reduce((sum, v) => sum + v * timestepSeconds, 0);
        };

        const detectTimestep = (times: string[] | undefined): number => {
            if (!times || times.length < 2) return data.timestep_minutes || 5;
            const t1 = new Date(times[0]).getTime();
            const t2 = new Date(times[1]).getTime();
            const diffMinutes = (t2 - t1) / 60000;
            return diffMinutes > 0 ? diffMinutes : (data.timestep_minutes || 5);
        };

        const obsTimestep = detectTimestep(data.series.obs_flow?.time);
        const predTimestep = detectTimestep(data.series.pred_flow?.time);

        const obsFlowStats = calcStats(data.series.obs_flow?.values);
        const predFlowStats = calcStats(data.series.pred_flow?.values);
        const obsDepthStats = calcStats(data.series.obs_depth?.values);
        const predDepthStats = calcStats(data.series.pred_depth?.values);
        const obsVelocityStats = calcStats(data.series.obs_velocity?.values);
        const predVelocityStats = calcStats(data.series.pred_velocity?.values);

        const obsVolume = calcVolume(data.series.obs_flow?.values, obsTimestep);
        const predVolume = calcVolume(data.series.pred_flow?.values, predTimestep);

        return {
            depth: {
                obs: obsDepthStats,
                pred: predDepthStats,
                diff: {
                    min: obsDepthStats.min != null && predDepthStats.min != null ? predDepthStats.min - obsDepthStats.min : null,
                    max: obsDepthStats.max != null && predDepthStats.max != null ? predDepthStats.max - obsDepthStats.max : null,
                    minPct: obsDepthStats.min != null && obsDepthStats.min !== 0 && predDepthStats.min != null
                        ? ((predDepthStats.min - obsDepthStats.min) / Math.abs(obsDepthStats.min)) * 100 : null,
                    maxPct: obsDepthStats.max != null && obsDepthStats.max !== 0 && predDepthStats.max != null
                        ? ((predDepthStats.max - obsDepthStats.max) / Math.abs(obsDepthStats.max)) * 100 : null,
                }
            },
            flow: {
                obs: { ...obsFlowStats, volume: obsVolume },
                pred: { ...predFlowStats, volume: predVolume },
                diff: {
                    min: obsFlowStats.min != null && predFlowStats.min != null ? predFlowStats.min - obsFlowStats.min : null,
                    max: obsFlowStats.max != null && predFlowStats.max != null ? predFlowStats.max - obsFlowStats.max : null,
                    volume: obsVolume != null && predVolume != null ? predVolume - obsVolume : null,
                    minPct: obsFlowStats.min != null && obsFlowStats.min !== 0 && predFlowStats.min != null
                        ? ((predFlowStats.min - obsFlowStats.min) / Math.abs(obsFlowStats.min)) * 100 : null,
                    maxPct: obsFlowStats.max != null && obsFlowStats.max !== 0 && predFlowStats.max != null
                        ? ((predFlowStats.max - obsFlowStats.max) / Math.abs(obsFlowStats.max)) * 100 : null,
                    volumePct: obsVolume != null && obsVolume !== 0 && predVolume != null
                        ? ((predVolume - obsVolume) / Math.abs(obsVolume)) * 100 : null,
                }
            },
            velocity: {
                obs: obsVelocityStats,
                pred: predVelocityStats,
                diff: {
                    min: obsVelocityStats.min != null && predVelocityStats.min != null ? predVelocityStats.min - obsVelocityStats.min : null,
                    max: obsVelocityStats.max != null && predVelocityStats.max != null ? predVelocityStats.max - obsVelocityStats.max : null,
                    minPct: obsVelocityStats.min != null && obsVelocityStats.min !== 0 && predVelocityStats.min != null
                        ? ((predVelocityStats.min - obsVelocityStats.min) / Math.abs(obsVelocityStats.min)) * 100 : null,
                    maxPct: obsVelocityStats.max != null && obsVelocityStats.max !== 0 && predVelocityStats.max != null
                        ? ((predVelocityStats.max - obsVelocityStats.max) / Math.abs(obsVelocityStats.max)) * 100 : null,
                }
            }
        };
    }, [data?.series, data?.timestep_minutes]);

    if (isLoading && !data) {
        return <div className="p-8 text-center text-gray-500">Loading analysis workspace...</div>;
    }
    if (error || (!isLoading && !data)) {
        return <div className="p-8 text-center text-red-500">Error loading workspace data</div>;
    }
    if (!data) return null;

    return (
        <div ref={workspaceRef} className="h-full flex flex-col bg-gray-50 overflow-y-auto">
            <div className="bg-white border-b border-gray-200 px-6 py-4 sticky top-0 z-10 shadow-sm">
                <div className="flex justify-between items-center">
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
                            {!effectiveDepthOnly && (
                                <button
                                    className={`px-3 py-1.5 text-sm font-medium ${viewMode === 'shapefit' ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-50'}`}
                                    onClick={() => setViewMode('shapefit')}
                                >
                                    Shape Fit
                                </button>
                            )}
                        </div>
                        <button
                            onClick={handleCapture}
                            disabled={isCapturing}
                            title="Capture Screen"
                            className="p-1.5 text-gray-500 hover:text-gray-900 bg-white hover:bg-gray-50 border border-gray-300 rounded-md transition-colors disabled:opacity-50"
                        >
                            {isCapturing ? <Loader2 size={20} className="animate-spin" /> : <Camera size={20} />}
                        </button>
                        <button
                            onClick={() => setShowControls(!showControls)}
                            className={`flex items-center gap-2 px-3 py-1.5 rounded-md border font-medium transition-colors ${showControls ? 'bg-blue-600 text-white border-blue-600' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'}`}
                        >
                            <Settings size={16} />
                            Analysis
                        </button>
                    </div>
                </div>

                {/* Analysis Controls Panel - Now in sticky header */}
                {showControls && (
                    <div className="mt-4">
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
            </div>

            {/* Content */}
            <div className="p-6">
                {viewMode === 'timeseries' ? (
                    <>
                        {/* Status Overrides */}
                        <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6">
                            <div className="flex items-center gap-4">
                                {isMonitorDepthOnly ? (
                                    <div className="flex items-center gap-2 bg-blue-50 text-blue-800 px-3 py-1.5 rounded-md border border-blue-200">
                                        <CheckCircle size={16} />
                                        <span className="font-medium text-sm">Depth Verification Only (Enforced by Monitor)</span>
                                    </div>
                                ) : (
                                    <label className="flex items-center gap-2 cursor-pointer select-none">
                                        <input
                                            type="checkbox"
                                            checked={isDepthOnly}
                                            onChange={(e) => handleDepthOverrideChange(e.target.checked)}
                                            className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                                        />
                                        <span className="font-medium text-gray-700">Depth Verification Only</span>
                                    </label>
                                )}

                                {effectiveDepthOnly && !isMonitorDepthOnly && (
                                    <div className="flex-1 flex items-center gap-2 animate-in fade-in slide-in-from-left-2 transition-all">
                                        <span className="text-sm text-gray-500 whitespace-nowrap">Reason:</span>
                                        <input
                                            type="text"
                                            value={depthOnlyComment}
                                            onChange={(e) => setDepthOnlyComment(e.target.value)}
                                            onBlur={handleDepthCommentSave}
                                            placeholder="e.g. Flow sensor failure..."
                                            className="w-full max-w-md px-3 py-1.5 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                        />
                                    </div>
                                )}
                            </div>
                            {effectiveDepthOnly && (
                                <p className="mt-2 text-xs text-amber-600 flex items-center gap-1">
                                    <AlertTriangle size={12} />
                                    Flow scores will be ignored. Overall verification status depends on Depth scores only.
                                </p>
                            )}
                        </div>
                        {/* Summary Statistics Table */}
                        {summaryStats && (
                            <div className="bg-white rounded-lg border border-gray-200 p-4 mb-6 overflow-x-auto">
                                <table className="w-full text-sm border-collapse">
                                    <thead>
                                        <tr className="border-b border-gray-300">
                                            <th className="py-2 px-3 text-left font-medium text-gray-600"></th>
                                            <th colSpan={2} className="py-2 px-3 text-center font-semibold text-gray-700 border-l border-gray-200">Depth</th>
                                            {!effectiveDepthOnly && (
                                                <>
                                                    <th colSpan={3} className="py-2 px-3 text-center font-semibold text-gray-700 border-l border-gray-200">Flow</th>
                                                    <th colSpan={2} className="py-2 px-3 text-center font-semibold text-gray-700 border-l border-gray-200">Velocity</th>
                                                </>
                                            )}
                                        </tr>
                                        <tr className="border-b border-gray-200 text-xs text-gray-500">
                                            <th className="py-1 px-3 text-left"></th>
                                            <th className="py-1 px-2 text-center border-l border-gray-200">Min (m)</th>
                                            <th className="py-1 px-2 text-center">Max (m)</th>
                                            {!effectiveDepthOnly && (
                                                <>
                                                    <th className="py-1 px-2 text-center border-l border-gray-200">Min (m³/s)</th>
                                                    <th className="py-1 px-2 text-center">Max (m³/s)</th>
                                                    <th className="py-1 px-2 text-center">Volume (m³)</th>
                                                    <th className="py-1 px-2 text-center border-l border-gray-200">Min (m/s)</th>
                                                    <th className="py-1 px-2 text-center">Max (m/s)</th>
                                                </>
                                            )}
                                        </tr>
                                    </thead>
                                    <tbody className="font-mono text-xs">
                                        <tr className="border-b border-gray-100 hover:bg-gray-50">
                                            <td className="py-2 px-3 font-medium text-gray-700">Observed</td>
                                            <td className="py-2 px-2 text-center border-l border-gray-200">{summaryStats.depth.obs.min?.toFixed(3) ?? '-'}</td>
                                            <td className="py-2 px-2 text-center">{summaryStats.depth.obs.max?.toFixed(3) ?? '-'}</td>
                                            {!effectiveDepthOnly && (
                                                <>
                                                    <td className="py-2 px-2 text-center border-l border-gray-200">{summaryStats.flow.obs.min?.toFixed(3) ?? '-'}</td>
                                                    <td className="py-2 px-2 text-center">{summaryStats.flow.obs.max?.toFixed(3) ?? '-'}</td>
                                                    <td className="py-2 px-2 text-center">{summaryStats.flow.obs.volume?.toFixed(1) ?? '-'}</td>
                                                    <td className="py-2 px-2 text-center border-l border-gray-200">{summaryStats.velocity.obs.min?.toFixed(3) ?? '-'}</td>
                                                    <td className="py-2 px-2 text-center">{summaryStats.velocity.obs.max?.toFixed(3) ?? '-'}</td>
                                                </>
                                            )}
                                        </tr>
                                        <tr className="border-b border-gray-100 hover:bg-gray-50">
                                            <td className="py-2 px-3 font-medium text-gray-700">Predicted</td>
                                            <td className="py-2 px-2 text-center border-l border-gray-200">{summaryStats.depth.pred.min?.toFixed(3) ?? '-'}</td>
                                            <td className="py-2 px-2 text-center">{summaryStats.depth.pred.max?.toFixed(3) ?? '-'}</td>
                                            {!effectiveDepthOnly && (
                                                <>
                                                    <td className="py-2 px-2 text-center border-l border-gray-200">{summaryStats.flow.pred.min?.toFixed(3) ?? '-'}</td>
                                                    <td className="py-2 px-2 text-center">{summaryStats.flow.pred.max?.toFixed(3) ?? '-'}</td>
                                                    <td className="py-2 px-2 text-center">{summaryStats.flow.pred.volume?.toFixed(1) ?? '-'}</td>
                                                    <td className="py-2 px-2 text-center border-l border-gray-200">{summaryStats.velocity.pred.min?.toFixed(3) ?? '-'}</td>
                                                    <td className="py-2 px-2 text-center">{summaryStats.velocity.pred.max?.toFixed(3) ?? '-'}</td>
                                                </>
                                            )}
                                        </tr>
                                        <tr className="bg-blue-50 text-blue-800 font-medium">
                                            <td className="py-2 px-3">Difference</td>
                                            <td className="py-2 px-2 text-center border-l border-gray-200">
                                                {summaryStats.depth.diff.min != null ? (
                                                    <>{summaryStats.depth.diff.min.toFixed(3)} {summaryStats.depth.diff.minPct != null && <span className="text-gray-500">({summaryStats.depth.diff.minPct.toFixed(0)}%)</span>}</>
                                                ) : '-'}
                                            </td>
                                            <td className="py-2 px-2 text-center">
                                                {summaryStats.depth.diff.max != null ? (
                                                    <>{summaryStats.depth.diff.max.toFixed(3)} {summaryStats.depth.diff.maxPct != null && <span className="text-gray-500">({summaryStats.depth.diff.maxPct.toFixed(0)}%)</span>}</>
                                                ) : '-'}
                                            </td>
                                            {!effectiveDepthOnly && (
                                                <>
                                                    <td className="py-2 px-2 text-center border-l border-gray-200">
                                                        {summaryStats.flow.diff.min != null ? (
                                                            <>{summaryStats.flow.diff.min.toFixed(3)} {summaryStats.flow.diff.minPct != null && <span className="text-gray-500">({summaryStats.flow.diff.minPct.toFixed(0)}%)</span>}</>
                                                        ) : '-'}
                                                    </td>
                                                    <td className="py-2 px-2 text-center">
                                                        {summaryStats.flow.diff.max != null ? (
                                                            <>{summaryStats.flow.diff.max.toFixed(3)} {summaryStats.flow.diff.maxPct != null && <span className="text-gray-500">({summaryStats.flow.diff.maxPct.toFixed(0)}%)</span>}</>
                                                        ) : '-'}
                                                    </td>
                                                    <td className="py-2 px-2 text-center">
                                                        {summaryStats.flow.diff.volume != null ? (
                                                            <>{summaryStats.flow.diff.volume.toFixed(1)} {summaryStats.flow.diff.volumePct != null && <span className="text-gray-500">({summaryStats.flow.diff.volumePct.toFixed(0)}%)</span>}</>
                                                        ) : '-'}
                                                    </td>
                                                    <td className="py-2 px-2 text-center border-l border-gray-200">
                                                        {summaryStats.velocity.diff.min != null ? (
                                                            <>{summaryStats.velocity.diff.min.toFixed(3)} {summaryStats.velocity.diff.minPct != null && <span className="text-gray-500">({summaryStats.velocity.diff.minPct.toFixed(0)}%)</span>}</>
                                                        ) : '-'}
                                                    </td>
                                                    <td className="py-2 px-2 text-center">
                                                        {summaryStats.velocity.diff.max != null ? (
                                                            <>{summaryStats.velocity.diff.max.toFixed(3)} {summaryStats.velocity.diff.maxPct != null && <span className="text-gray-500">({summaryStats.velocity.diff.maxPct.toFixed(0)}%)</span>}</>
                                                        ) : '-'}
                                                    </td>
                                                </>
                                            )}
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        )}

                        {/* Flow Chart */}
                        {flowChartData.length > 0 && !effectiveDepthOnly && (
                            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                                <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
                                    Flow Comparison
                                    {isFlowSeries && (
                                        <span className="text-xs font-medium px-2 py-1 bg-yellow-100 text-yellow-800 rounded animate-pulse border border-yellow-200 flex items-center gap-1">
                                            <MousePointer2 size={12} />
                                            Mode Active: Click chart to toggle {editSeries === 'obs_flow' ? 'Observed' : 'Predicted'} Peaks
                                        </span>
                                    )}
                                </h3>
                                <ResponsiveContainer width="100%" height={400}>
                                    <LineChart
                                        data={flowChartData}
                                        onClick={handleChartClick('flow')}
                                        className={isFlowSeries ? 'cursor-crosshair' : ''}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="timestamp"
                                            type="number"
                                            domain={['dataMin', 'dataMax']}
                                            tickFormatter={formatAxisDate}
                                            tick={{ fontSize: 10 }}
                                            interval="preserveStartEnd"
                                        />
                                        <YAxis label={{ value: 'Flow', angle: -90, position: 'insideLeft' }} />
                                        <Tooltip formatter={chartTooltipFormatter} labelFormatter={formatTooltipLabel} />
                                        <Legend />
                                        <Line
                                            type="monotone"
                                            dataKey="observed"
                                            stroke="#15803d" // Leaf Green
                                            strokeWidth={2}
                                            dot={false}
                                            connectNulls
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
                                            connectNulls
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
                                                connectNulls
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
                                                connectNulls
                                                name="Predicted (Smoothed)"
                                                isAnimationActive={false}
                                            />
                                        )}

                                        {displayPeaks.obs_flow?.map((peak: any, i: number) => (
                                            <ReferenceDot
                                                key={`obs-peak-${i}`}
                                                x={new Date(peak.time).getTime()}
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
                                                x={new Date(peak.time).getTime()}
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

                        {/* Depth Chart - Now with manual peak editing support */}
                        {depthChartData.length > 0 && (
                            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                                <h3 className="text-lg font-semibold mb-4 flex items-center justify-between">
                                    Depth Comparison
                                    {isDepthSeries && (
                                        <span className="text-xs font-medium px-2 py-1 bg-yellow-100 text-yellow-800 rounded animate-pulse border border-yellow-200 flex items-center gap-1">
                                            <MousePointer2 size={12} />
                                            Mode Active: Click chart to toggle {editSeries === 'obs_depth' ? 'Observed' : 'Predicted'} Peaks
                                        </span>
                                    )}
                                </h3>
                                <ResponsiveContainer width="100%" height={400}>
                                    <LineChart
                                        data={depthChartData}
                                        onClick={handleChartClick('depth')}
                                        className={isDepthSeries ? 'cursor-crosshair' : ''}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="timestamp"
                                            type="number"
                                            domain={['dataMin', 'dataMax']}
                                            tickFormatter={formatAxisDate}
                                            tick={{ fontSize: 10 }}
                                            interval="preserveStartEnd"
                                        />
                                        <YAxis label={{ value: 'Depth', angle: -90, position: 'insideLeft' }} />
                                        <Tooltip formatter={chartTooltipFormatter} labelFormatter={formatTooltipLabel} />
                                        <Legend />
                                        <Line
                                            type="monotone"
                                            dataKey="observed"
                                            stroke="#15803d"
                                            strokeWidth={2}
                                            dot={false}
                                            connectNulls
                                            name="Observed (Raw)"
                                            opacity={data.series.obs_depth_smoothed ? 0.3 : 1}
                                            isAnimationActive={false}
                                            activeDot={editSeries === 'obs_depth' ? { r: 6, stroke: '#22c55e', strokeWidth: 2 } : { r: 4 }}
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="predicted"
                                            stroke="#dc2626"
                                            strokeWidth={2}
                                            dot={false}
                                            connectNulls
                                            name="Predicted (Raw)"
                                            opacity={data.series.pred_depth_smoothed ? 0.3 : 1}
                                            isAnimationActive={false}
                                            activeDot={editSeries === 'pred_depth' ? { r: 6, stroke: '#ef4444', strokeWidth: 2 } : { r: 4 }}
                                        />
                                        {data.series.obs_depth_smoothed && (
                                            <Line
                                                type="monotone"
                                                dataKey="obs_smoothed"
                                                stroke="#15803d"
                                                strokeWidth={2}
                                                dot={false}
                                                connectNulls
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
                                                connectNulls
                                                name="Predicted (Smoothed)"
                                            />
                                        )}
                                        {displayPeaks.obs_depth?.map((peak: any, i: number) => (
                                            <ReferenceDot
                                                key={`obs-peak-${i}`}
                                                x={new Date(peak.time).getTime()}
                                                y={peak.value}
                                                r={6}
                                                fill="#15803d"
                                                stroke="#fff"
                                            />
                                        ))}
                                        {displayPeaks.pred_depth?.map((peak: any, i: number) => (
                                            <ReferenceDot
                                                key={`pred-peak-${i}`}
                                                x={new Date(peak.time).getTime()}
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

                        {/* Velocity Chart */}
                        {velocityChartData.length > 0 && !effectiveDepthOnly && (
                            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                                <h3 className="text-lg font-semibold mb-4">Velocity Comparison</h3>
                                <ResponsiveContainer width="100%" height={300}>
                                    <LineChart data={velocityChartData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="timestamp"
                                            type="number"
                                            domain={['dataMin', 'dataMax']}
                                            tickFormatter={formatAxisDate}
                                            fontSize={12}
                                            interval="preserveStartEnd"
                                            minTickGap={60}
                                        />
                                        <YAxis
                                            fontSize={12}
                                            tickFormatter={(value) => value.toFixed(2)}
                                            label={{ value: 'Velocity (m/s)', angle: -90, position: 'insideLeft', fontSize: 12 }}
                                        />
                                        <Tooltip
                                            labelFormatter={formatTooltipLabel}
                                            formatter={(value: number, name: string) => [value?.toFixed(3), name]}
                                        />
                                        <Legend />
                                        <Line
                                            type="monotone"
                                            dataKey="observed"
                                            stroke="#15803d"
                                            strokeWidth={2}
                                            dot={false}
                                            connectNulls
                                            name="Observed"
                                        />
                                        <Line
                                            type="monotone"
                                            dataKey="predicted"
                                            stroke="#dc2626"
                                            strokeWidth={2}
                                            dot={false}
                                            connectNulls
                                            name="Predicted"
                                        />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        )}

                        {/* Flow Metrics */}
                        {!effectiveDepthOnly && (
                            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                                <div className="flex items-center gap-2 mb-4">
                                    <Activity className="text-blue-600" />
                                    <h3 className="text-lg font-semibold">Flow Metrics</h3>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {data?.metrics?.flow?.map((metric) => (
                                        <div key={metric.name} className="p-4 bg-gray-50 rounded-lg">
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


                        {/* Depth Metrics */}
                        {data.metrics.depth && data.metrics.depth.length > 0 && (
                            <div className="bg-white rounded-lg border border-gray-200 p-6 mb-6">
                                <div className="flex items-center gap-2 mb-4">
                                    <Droplets className="text-cyan-600" />
                                    <h3 className="text-lg font-semibold">Depth Metrics</h3>
                                </div>
                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {data.metrics.depth.map((metric) => (
                                        <div key={metric.name} className="p-4 bg-gray-50 rounded-lg">
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
                    <div className="space-y-6">
                        {/* Scatter Plot with Tolerance Bands */}
                        <div className="bg-white rounded-lg border border-gray-200 p-6">
                            <div className="flex items-center justify-between mb-4">
                                <div className="flex items-center gap-2">
                                    <BarChart2 className="text-purple-600" />
                                    <h3 className="text-lg font-semibold">Shape Fit (Observed vs Predicted)</h3>
                                </div>
                                <div className="text-sm bg-gray-50 px-3 py-2 rounded-lg border flex gap-4">
                                    <span className="font-semibold" title="NSE">NSE: {data?.run?.nse?.toFixed(3)}</span>
                                    <span className="font-semibold" title="KGE">KGE: {data?.run?.kge?.toFixed(3)}</span>
                                    <span className="font-semibold" title="CV">CV: {data?.run?.cv_obs?.toFixed(3)}</span>
                                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${data?.monitor?.is_critical ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-700'}`}>
                                        {data?.monitor?.is_critical ? 'Critical: ±10%' : 'General: +25%/-15%'}
                                    </span>
                                </div>
                            </div>
                            {/* Square container for 1:1 aspect ratio */}
                            {(() => {
                                // Compute axis max to accommodate tolerance lines (add 30% margin for general, 15% for critical)
                                const axisMax = maxScatterVal * (data?.monitor?.is_critical ? 1.15 : 1.30);
                                // Generate nice tick values
                                const tickStep = axisMax / 5;
                                const ticks = [0, tickStep, tickStep * 2, tickStep * 3, tickStep * 4, axisMax];

                                return (
                                    <div className="flex flex-col items-center">
                                        <div style={{ width: '500px', height: '500px' }}>
                                            <ResponsiveContainer width="100%" height="100%">
                                                <ScatterChart margin={{ top: 20, right: 30, bottom: 50, left: 60 }}>
                                                    <CartesianGrid />
                                                    <XAxis
                                                        type="number"
                                                        dataKey="observed"
                                                        name="Observed"
                                                        label={{ value: 'Observed Flow (m³/s)', position: 'bottom', offset: 25 }}
                                                        domain={[0, axisMax]}
                                                        ticks={ticks}
                                                        tickFormatter={(v) => v.toFixed(4)}
                                                    />
                                                    <YAxis
                                                        type="number"
                                                        dataKey="predicted"
                                                        name="Predicted"
                                                        label={{ value: 'Predicted Flow (m³/s)', angle: -90, position: 'insideLeft', offset: -5 }}
                                                        domain={[0, axisMax]}
                                                        ticks={ticks}
                                                        tickFormatter={(v) => v.toFixed(4)}
                                                    />
                                                    <Tooltip cursor={{ strokeDasharray: '3 3' }} formatter={chartTooltipFormatter} />

                                                    {/* Upper tolerance band line */}
                                                    <ReferenceLine
                                                        segment={[
                                                            { x: 0, y: 0 },
                                                            { x: maxScatterVal, y: maxScatterVal * (data?.monitor?.is_critical ? 1.10 : 1.25) }
                                                        ]}
                                                        stroke="#f59e0b"
                                                        strokeDasharray="5 5"
                                                        strokeWidth={1.5}
                                                    />

                                                    {/* Lower tolerance band line */}
                                                    <ReferenceLine
                                                        segment={[
                                                            { x: 0, y: 0 },
                                                            { x: maxScatterVal, y: maxScatterVal * (data?.monitor?.is_critical ? 0.90 : 0.85) }
                                                        ]}
                                                        stroke="#f59e0b"
                                                        strokeDasharray="5 5"
                                                        strokeWidth={1.5}
                                                    />

                                                    {/* Perfect fit line */}
                                                    <ReferenceLine segment={[{ x: 0, y: 0 }, { x: maxScatterVal, y: maxScatterVal }]} stroke="#22c55e" strokeWidth={2} />

                                                    <Scatter name="Flow Correlation" data={flowScatterData} fill="#8884d8" />
                                                </ScatterChart>
                                            </ResponsiveContainer>
                                        </div>
                                        {/* Custom Legend */}
                                        <div className="flex justify-center gap-6 mt-4 text-sm">
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-0.5 bg-green-500"></div>
                                                <span>Perfect Fit (1:1)</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-0.5 border-t-2 border-dashed border-amber-500"></div>
                                                <span>Tolerance ({data?.monitor?.is_critical ? '±10%' : '+25% / -15%'})</span>
                                            </div>
                                            <div className="flex items-center gap-2">
                                                <div className="w-3 h-3 rounded-full bg-purple-400"></div>
                                                <span>Data Points</span>
                                            </div>
                                        </div>
                                    </div>
                                );
                            })()}
                        </div>

                        {/* KGE Components Bar Chart */}
                        {!effectiveDepthOnly && (data as any)?.kge_components && (
                            <div className="bg-white rounded-lg border border-gray-200 p-6">
                                <div className="flex items-center gap-2 mb-4">
                                    <Activity className="text-blue-600" />
                                    <h3 className="text-lg font-semibold">KGE Components</h3>
                                    <span className="ml-auto text-sm bg-blue-50 px-3 py-1 rounded font-semibold text-blue-700">
                                        KGE = {(data as any).kge_components.kge?.toFixed(3)}
                                    </span>
                                </div>
                                <div className="h-[200px]">
                                    <ResponsiveContainer width="100%" height="100%">
                                        <BarChart
                                            data={[
                                                { name: 'r (Correlation)', value: (data as any).kge_components.r, target: 1 },
                                                { name: 'α (Variability)', value: (data as any).kge_components.alpha, target: 1 },
                                                { name: 'β (Bias)', value: (data as any).kge_components.beta, target: 1 },
                                            ]}
                                            layout="vertical"
                                            margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
                                        >
                                            <CartesianGrid strokeDasharray="3 3" />
                                            <XAxis type="number" domain={[0, 2]} tickFormatter={(v) => v.toFixed(1)} />
                                            <YAxis type="category" dataKey="name" width={90} />
                                            <Tooltip formatter={(value: number) => value?.toFixed(4)} />
                                            <ReferenceLine x={1} stroke="#22c55e" strokeWidth={2} label={{ value: 'Target (1.0)', position: 'top', fill: '#22c55e', fontSize: 12 }} />
                                            <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                                                {[
                                                    { name: 'r', value: (data as any).kge_components.r },
                                                    { name: 'α', value: (data as any).kge_components.alpha },
                                                    { name: 'β', value: (data as any).kge_components.beta },
                                                ].map((entry, index) => {
                                                    const diff = Math.abs(entry.value - 1);
                                                    let color = '#22c55e'; // green - good
                                                    if (diff > 0.2) color = '#f59e0b'; // amber - fair
                                                    if (diff > 0.5) color = '#ef4444'; // red - poor
                                                    return <Cell key={`cell-${index}`} fill={color} />;
                                                })}
                                            </Bar>
                                        </BarChart>
                                    </ResponsiveContainer>
                                </div>
                            </div>
                        )}

                        {/* KGE Explanation Card */}
                        {!effectiveDepthOnly && (
                            <div className="bg-white rounded-lg border border-gray-200 p-6">
                                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                                    <Droplets className="text-purple-600" />
                                    KGE Component Reference
                                </h3>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
                                    {/* Correlation (r) */}
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <h4 className="font-bold text-gray-900 mb-2">Correlation (r)</h4>
                                        <p className="text-gray-600 mb-3">Pearson correlation between observed and predicted time series. Measures timing and shape, not magnitude.</p>
                                        <div className="space-y-1 text-xs">
                                            <div className="flex justify-between"><span className="text-gray-500">Range:</span><span className="font-mono">–1 to +1</span></div>
                                            <div className="flex justify-between"><span className="text-gray-500">Perfect:</span><span className="font-mono text-green-600">+1</span></div>
                                        </div>
                                        <div className="mt-3 pt-3 border-t border-gray-200">
                                            <p className="font-semibold text-gray-700 mb-1">Interpretation:</p>
                                            <ul className="text-xs text-gray-600 space-y-0.5">
                                                <li><span className="font-mono text-green-600">1.0:</span> Perfect timing and shape</li>
                                                <li><span className="font-mono text-green-600">0.8–0.9:</span> Good timing, some mismatch</li>
                                                <li><span className="font-mono text-amber-600">~0.5:</span> Weak pattern agreement</li>
                                                <li><span className="font-mono text-red-600">0:</span> No relationship</li>
                                                <li><span className="font-mono text-red-600">&lt; 0:</span> Actively wrong timing</li>
                                            </ul>
                                        </div>
                                    </div>

                                    {/* Variability ratio (α) */}
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <h4 className="font-bold text-gray-900 mb-2">Variability ratio (α)</h4>
                                        <p className="text-gray-600 mb-3">Ratio of standard deviations. Measures how "lively" the model response is.</p>
                                        <div className="space-y-1 text-xs">
                                            <div className="flex justify-between"><span className="text-gray-500">Range:</span><span className="font-mono">0 to ∞</span></div>
                                            <div className="flex justify-between"><span className="text-gray-500">Perfect:</span><span className="font-mono text-green-600">1</span></div>
                                        </div>
                                        <div className="mt-3 pt-3 border-t border-gray-200">
                                            <p className="font-semibold text-gray-700 mb-1">Interpretation:</p>
                                            <ul className="text-xs text-gray-600 space-y-0.5">
                                                <li><span className="font-mono text-amber-600">&lt;1:</span> Model too smooth / damped</li>
                                                <li><span className="font-mono text-green-600">1:</span> Correct variability</li>
                                                <li><span className="font-mono text-amber-600">&gt;1:</span> Model too jumpy / noisy</li>
                                            </ul>
                                            <p className="font-semibold text-gray-700 mt-2 mb-1">Indicative Values:</p>
                                            <ul className="text-xs text-gray-600 space-y-0.5">
                                                <li><span className="font-mono text-green-600">0.8–1.2:</span> Good / acceptable</li>
                                                <li><span className="font-mono text-amber-600">0.6–0.8 or 1.25–1.5:</span> Noticeable mismatch</li>
                                                <li><span className="font-mono text-red-600">&lt;0.6 or &gt;1.5:</span> Poor variability match</li>
                                            </ul>
                                        </div>
                                    </div>

                                    {/* Bias ratio (β) */}
                                    <div className="bg-gray-50 rounded-lg p-4">
                                        <h4 className="font-bold text-gray-900 mb-2">Bias ratio (β)</h4>
                                        <p className="text-gray-600 mb-3">Ratio of mean flows. Measures systematic offset.</p>
                                        <div className="space-y-1 text-xs">
                                            <div className="flex justify-between"><span className="text-gray-500">Range:</span><span className="font-mono">0 to ∞</span></div>
                                            <div className="flex justify-between"><span className="text-gray-500">Perfect:</span><span className="font-mono text-green-600">1</span></div>
                                        </div>
                                        <div className="mt-3 pt-3 border-t border-gray-200">
                                            <p className="font-semibold text-gray-700 mb-1">Interpretation:</p>
                                            <ul className="text-xs text-gray-600 space-y-0.5">
                                                <li><span className="font-mono text-amber-600">&lt;1:</span> Under-prediction</li>
                                                <li><span className="font-mono text-green-600">1.0:</span> Perfect mean match</li>
                                                <li><span className="font-mono text-red-600">≈0:</span> Model predicts almost nothing</li>
                                                <li><span className="font-mono text-amber-600">&gt;1:</span> Over-prediction</li>
                                                <li><span className="font-mono text-red-600">≫1:</span> Model massively overestimates</li>
                                            </ul>
                                            <p className="font-semibold text-gray-700 mt-2 mb-1">Indicative Values:</p>
                                            <ul className="text-xs text-gray-600 space-y-0.5">
                                                <li><span className="font-mono text-green-600">0.9–1.1:</span> Very good</li>
                                                <li><span className="font-mono text-amber-600">0.8–0.9 or 1.1–1.25:</span> Acceptable / minor bias</li>
                                                <li><span className="font-mono text-red-600">&lt;0.8 or &gt;1.25:</span> Significant bias</li>
                                                <li><span className="font-mono text-red-600">&lt;0.5 or &gt;2:</span> Poor</li>
                                            </ul>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* DEBUG OVERLAY - REMOVED */}
        </div>
    );
}
