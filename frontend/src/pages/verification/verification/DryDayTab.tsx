import React, { useState, useMemo, useEffect } from 'react';
import { Upload, CloudRain, Sun, X, RefreshCw, Trash2, ChevronDown, ChevronRight, AlertCircle, CheckCircle, Search, Activity, Droplets, Wind, Save } from 'lucide-react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import {
    useFullPeriodImports,
    usePreviewFullPeriodImport,
    useImportFullPeriod,
    useDeleteFullPeriodImport,
    useDetectDryDays,
    useFPMonitors,
    useMonitorDryDays,
    useUpdateDryDay,
    useMonitor24hrChart,
    useSaveDWFProfiles,
    type FullPeriodImportPreview,
    type DryDay,
    type FPMonitor
} from '../../../api/hooks';

interface DryDayTabProps {
    projectId: number;
}

// Sub-component for Monitor List Item
const MonitorListItem = ({
    monitor,
    isSelected,
    onClick
}: {
    monitor: FPMonitor;
    isSelected: boolean;
    onClick: () => void;
}) => {
    return (
        <div
            onClick={onClick}
            className={`
                pl-8 pr-3 py-2 text-sm cursor-pointer flex items-center justify-between
                ${isSelected
                    ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-500'
                    : 'text-gray-600 hover:bg-gray-50'
                }
            `}
        >
            <div className="flex items-center gap-2 truncate">
                <Activity size={14} className={isSelected ? 'text-blue-500' : 'text-gray-400'} />
                <span className="truncate">{monitor.monitor_name || `Monitor ${monitor.monitor_id}`}</span>
            </div>
            <div className="flex gap-1">
                {monitor.has_flow && <div className="w-1.5 h-1.5 rounded-full bg-green-500" title="Flow" />}
                {monitor.has_depth && <div className="w-1.5 h-1.5 rounded-full bg-blue-500" title="Depth" />}
                {monitor.has_rainfall && <div className="w-1.5 h-1.5 rounded-full bg-amber-500" title="Rainfall" />}
            </div>
        </div>
    );
};

// Sub-component for Import Item (Collapsible)
const ImportGroup = ({
    importItem,
    isExpanded,
    isSelectedImport,
    onToggle,
    selectedMonitorId,
    onSelectMonitor,
    onDelete
}: {
    importItem: any;
    isExpanded: boolean;
    isSelectedImport: boolean;
    onToggle: () => void;
    selectedMonitorId: number | null;
    onSelectMonitor: (id: number) => void;
    onDelete: () => void;
}) => {
    const { data: monitors } = useFPMonitors(importItem.id);

    return (
        <div className="border-b border-gray-100 last:border-0">
            <div
                className={`
                    flex items-center justify-between p-3 cursor-pointer hover:bg-gray-50 transition-colors
                    ${isSelectedImport ? 'bg-gray-50' : ''}
                `}
                onClick={onToggle}
            >
                <div className="flex items-center gap-2 overflow-hidden">
                    {isExpanded ? <ChevronDown size={16} className="text-gray-400" /> : <ChevronRight size={16} className="text-gray-400" />}
                    <CloudRain size={16} className="text-blue-500 flex-shrink-0" />
                    <div className="truncate">
                        <div className="font-medium text-sm text-gray-900 truncate">{importItem.name}</div>
                        <div className="text-xs text-gray-500">
                            {new Date(importItem.start_time).toLocaleDateString()}
                        </div>
                    </div>
                </div>
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        onDelete();
                    }}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded"
                >
                    <Trash2 size={14} />
                </button>
            </div>

            {isExpanded && monitors && (
                <div className="bg-white pb-2">
                    {monitors.length > 0 ? (
                        monitors.map(m => (
                            <MonitorListItem
                                key={m.id}
                                monitor={m}
                                isSelected={selectedMonitorId === m.id}
                                onClick={() => onSelectMonitor(m.id)}
                            />
                        ))
                    ) : (
                        <div className="pl-8 py-2 text-xs text-gray-400 italic">No monitors found</div>
                    )}
                </div>
            )}
        </div>
    );
};

export default function DryDayTab({ projectId }: DryDayTabProps) {
    // Import Dialog State
    const [showImportDialog, setShowImportDialog] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [previewResult, setPreviewResult] = useState<FullPeriodImportPreview | null>(null);
    const [importName, setImportName] = useState('');
    const [previewLoading, setPreviewLoading] = useState(false);

    // Selection State
    const [expandedImportId, setExpandedImportId] = useState<number | null>(null);
    const [selectedFPMonitorId, setSelectedFPMonitorId] = useState<number | null>(null);

    // Analysis State
    const [dayThreshold, setDayThreshold] = useState(0.0);
    const [antecedentThreshold, setAntecedentThreshold] = useState(1.0);
    const [smoothing, setSmoothing] = useState(0);
    const [chartSeriesType, setChartSeriesType] = useState('flow'); // flow, depth, velocity
    const [dayFilter, setDayFilter] = useState('all'); // all, weekday, weekend
    const [hoveredDryDayDate, setHoveredDryDayDate] = useState<string | null>(null);

    // Hooks
    const { data: imports, isLoading: importsLoading } = useFullPeriodImports(projectId);
    const previewImport = usePreviewFullPeriodImport();
    const createImport = useImportFullPeriod();
    const deleteImport = useDeleteFullPeriodImport();
    const detectDryDays = useDetectDryDays();

    // Monitor Data Hooks
    const { data: dryDays, isLoading: dryDaysLoading } = useMonitorDryDays(selectedFPMonitorId);
    const updateDryDay = useUpdateDryDay();
    const saveProfiles = useSaveDWFProfiles();
    const { data: chartData, isLoading: chartLoading } = useMonitor24hrChart(selectedFPMonitorId, chartSeriesType, smoothing, dayFilter);

    // Derived State
    const selectedImport = useMemo(() =>
        imports?.find(i => i.id === expandedImportId),
        [imports, expandedImportId]);

    const { data: selectedMonitorList } = useFPMonitors(expandedImportId);

    const selectedMonitor = useMemo(() =>
        selectedMonitorList?.find(m => m.id === selectedFPMonitorId),
        [selectedMonitorList, selectedFPMonitorId]);

    // Update local thresholds when import changes
    useEffect(() => {
        if (selectedImport) {
            setDayThreshold(selectedImport.day_rainfall_threshold_mm);
            setAntecedentThreshold(selectedImport.antecedent_threshold_mm);
        }
    }, [selectedImport]);

    // Handlers
    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        setSelectedFile(file);
        setImportName(file.name.replace('.csv', ''));
        setPreviewLoading(true);

        try {
            const result = await previewImport.mutateAsync({ projectId, file });
            setPreviewResult(result);
        } catch (error) {
            console.error('Preview failed:', error);
        } finally {
            setPreviewLoading(false);
        }
    };

    const handleImport = async () => {
        if (!selectedFile || !importName) return;

        try {
            const result = await createImport.mutateAsync({
                projectId,
                file: selectedFile,
                name: importName,
                dayRainfallThreshold: 0,
                antecedentThreshold: 1
            });

            // Reset and close dialog
            setSelectedFile(null);
            setPreviewResult(null);
            setImportName('');
            setShowImportDialog(false);

            // Expand new import
            setExpandedImportId(result.id);
        } catch (error) {
            console.error('Import failed:', error);
        }
    };

    const handleDetectDryDays = async () => {
        if (!expandedImportId) return;

        try {
            await detectDryDays.mutateAsync({
                importId: expandedImportId,
                dayThresholdMm: dayThreshold,
                antecedentThresholdMm: antecedentThreshold
            });
        } catch (error) {
            console.error('Dry day detection failed:', error);
        }
    };

    const handleToggleDryDay = async (dryDay: DryDay) => {
        if (!selectedFPMonitorId || !expandedImportId) return;

        await updateDryDay.mutateAsync({
            dryDayId: dryDay.id,
            update: { is_included: !dryDay.is_included },
            fpMonitorId: selectedFPMonitorId
        });
    };

    // Chart Data Formatting
    const formattedChartData = useMemo(() => {
        if (!chartData?.envelope?.minutes) return [];

        const dataMap = new Map<number, any>();

        // Initialize with envelope data
        chartData.envelope.minutes.forEach((min, idx) => {
            dataMap.set(min, {
                time: `${Math.floor(min / 60).toString().padStart(2, '0')}:${(min % 60).toString().padStart(2, '0')}`,
                minutes: min,
                min: chartData.envelope.min[idx],
                max: chartData.envelope.max[idx],
                mean: chartData.envelope.mean[idx]
            });
        });

        // Add individual traces
        if (chartData.day_traces) {
            chartData.day_traces.forEach((trace, tIdx) => {
                trace.values.forEach(pt => {
                    const d = dataMap.get(pt.minutes);
                    if (d) {
                        d[`trace_${tIdx}`] = pt.value;
                    }
                });
            });
        }

        return Array.from(dataMap.values()).sort((a, b) => a.minutes - b.minutes);
    }, [chartData]);

    // Axis formatter
    const formatAxisTick = (value: string) => {
        const hour = parseInt(value.split(':')[0]);
        return hour % 4 === 0 ? value : '';
    };

    return (
        <div className="flex h-[calc(100vh-12rem)] bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            {/* LEFT PANE: Monitor List */}
            <div className="w-80 border-r border-gray-200 flex flex-col bg-gray-50/50">
                <div className="p-4 border-b border-gray-200 bg-white">
                    <button
                        onClick={() => setShowImportDialog(true)}
                        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors shadow-sm"
                    >
                        <Upload size={16} />
                        <span className="font-medium">Import Full Period</span>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto">
                    {importsLoading ? (
                        <div className="p-4 text-center text-gray-500">Loading...</div>
                    ) : imports && imports.length > 0 ? (
                        <div className="divide-y divide-gray-100">
                            {imports.map(imp => (
                                <ImportGroup
                                    key={imp.id}
                                    importItem={imp}
                                    isExpanded={expandedImportId === imp.id}
                                    isSelectedImport={expandedImportId === imp.id}
                                    onToggle={() => setExpandedImportId(expandedImportId === imp.id ? null : imp.id)}
                                    selectedMonitorId={selectedFPMonitorId}
                                    onSelectMonitor={setSelectedFPMonitorId}
                                    onDelete={() => {
                                        if (confirm('Delete this import and all its data?')) {
                                            deleteImport.mutate({ importId: imp.id, projectId });
                                        }
                                    }}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="p-8 text-center text-gray-400">
                            <CloudRain size={32} className="mx-auto mb-2 opacity-50" />
                            <p className="text-sm">No imports yet</p>
                        </div>
                    )}
                </div>
            </div>

            {/* RIGHT PANE: Workspace */}
            <div className="flex-1 flex flex-col overflow-hidden bg-white">
                {selectedImport ? (
                    <>
                        {/* Header Toolbar */}
                        <div className="h-16 border-b border-gray-200 flex items-center justify-between px-6 bg-white shrink-0 z-10">
                            <div className="flex items-center gap-4">
                                <h3 className="font-semibold text-gray-900 truncate max-w-[200px]" title={selectedMonitor?.monitor_name || "Select Monitor"}>
                                    {selectedMonitor ? (selectedMonitor.monitor_name || `Monitor ${selectedMonitor.monitor_id}`) : 'No Monitor Selected'}
                                </h3>
                                {selectedMonitor && (
                                    <div className="flex bg-gray-100 p-1 rounded-lg">
                                        {[
                                            { id: 'flow', icon: Activity, label: 'Flow' },
                                            { id: 'depth', icon: Droplets, label: 'Depth' },
                                            { id: 'velocity', icon: Wind, label: 'Vel' }
                                        ].map(type => (
                                            <button
                                                key={type.id}
                                                onClick={() => setChartSeriesType(type.id)}
                                                className={`
                                                    px-3 py-1 text-xs font-medium rounded-md flex items-center gap-1.5 transition-all
                                                    ${chartSeriesType === type.id
                                                        ? 'bg-white text-gray-900 shadow-sm'
                                                        : 'text-gray-500 hover:text-gray-900 hover:bg-gray-200'
                                                    }
                                                `}
                                            >
                                                <type.icon size={12} />
                                                {type.label}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            <div className="flex items-center gap-4">
                                <div className="flex items-center gap-2 text-sm bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
                                    <span className="text-gray-500">Thresholds:</span>
                                    <input
                                        type="number"
                                        className="w-12 px-1 py-0.5 text-right border-gray-300 rounded text-xs"
                                        value={dayThreshold}
                                        onChange={e => setDayThreshold(parseFloat(e.target.value) || 0)}
                                    />
                                    <span className="text-gray-400 text-xs">mm</span>
                                    <span className="text-gray-300">|</span>
                                    <span className="text-gray-500 text-xs">Ant:</span>
                                    <input
                                        type="number"
                                        className="w-12 px-1 py-0.5 text-right border-gray-300 rounded text-xs"
                                        value={antecedentThreshold}
                                        onChange={e => setAntecedentThreshold(parseFloat(e.target.value) || 0)}
                                    />
                                    <span className="text-gray-400 text-xs">mm</span>
                                </div>

                                <button
                                    onClick={handleDetectDryDays}
                                    disabled={detectDryDays.isPending}
                                    className="px-3 py-1.5 bg-blue-50 text-blue-600 text-sm font-medium rounded-lg hover:bg-blue-100 disabled:opacity-50 transition-colors flex items-center gap-2"
                                >
                                    <RefreshCw size={14} className={detectDryDays.isPending ? 'animate-spin' : ''} />
                                    {detectDryDays.isPending ? 'Detecting...' : 'Re-detect'}
                                </button>
                            </div>
                        </div>

                        {/* Content Area */}
                        <div className="flex-1 overflow-y-auto p-6">
                            {selectedFPMonitorId && selectedMonitor ? (
                                <div className="space-y-6 max-w-5xl mx-auto">

                                    {/* Warnings if data missing */}
                                    {chartSeriesType === 'flow' && !selectedMonitor.has_flow && (
                                        <div className="bg-amber-50 text-amber-800 p-3 rounded-lg text-sm flex items-center gap-2">
                                            <AlertCircle size={16} /> No flow data available for this monitor.
                                        </div>
                                    )}

                                    {/* Chart Section */}
                                    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
                                        <div className="flex items-center justify-between mb-4">
                                            <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                                                24-Hour Profile
                                                <span className="text-xs font-normal text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
                                                    {chartSeriesType.charAt(0).toUpperCase() + chartSeriesType.slice(1)}
                                                </span>
                                            </h4>
                                            <div className="flex items-center gap-3">
                                                {/* Day Filter */}
                                                <div className="flex bg-gray-100 p-0.5 rounded-lg text-xs font-medium">
                                                    {['all', 'weekday', 'weekend'].map(f => (
                                                        <button
                                                            key={f}
                                                            onClick={() => setDayFilter(f)}
                                                            className={`
                                                                px-3 py-1 rounded-md transition-all
                                                                ${dayFilter === f
                                                                    ? 'bg-white text-gray-900 shadow-sm'
                                                                    : 'text-gray-500 hover:text-gray-900'
                                                                }
                                                            `}
                                                        >
                                                            {f.charAt(0).toUpperCase() + f.slice(1)}
                                                        </button>
                                                    ))}
                                                </div>

                                                <div className="h-4 w-px bg-gray-200" />

                                                <span className="text-xs text-gray-500">Smoothing</span>
                                                <input
                                                    type="number"
                                                    min="0"
                                                    max="0.99"
                                                    step="0.01"
                                                    value={smoothing}
                                                    onChange={(e) => setSmoothing(Math.min(0.99, Math.max(0, parseFloat(e.target.value) || 0)))}
                                                    className="w-14 px-2 py-1 border border-gray-300 rounded text-xs focus:ring-blue-500 focus:border-blue-500"
                                                />

                                                <div className="h-4 w-px bg-gray-200" />

                                                <button
                                                    onClick={() => selectedFPMonitorId && saveProfiles.mutate(selectedFPMonitorId)}
                                                    disabled={saveProfiles.isPending}
                                                    className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors disabled:opacity-50"
                                                    title="Save DWF Benchmarks"
                                                >
                                                    <Save size={16} className={saveProfiles.isPending ? 'animate-spin' : ''} />
                                                </button>
                                            </div>
                                        </div>

                                        {chartLoading ? (
                                            <div className="h-[300px] flex items-center justify-center text-gray-400">Loading chart...</div>
                                        ) : formattedChartData.length > 0 ? (
                                            <div className="h-[300px] w-full">
                                                <ResponsiveContainer width="100%" height="100%">
                                                    <LineChart data={formattedChartData} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                                                        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" vertical={false} />
                                                        <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#6b7280' }} tickFormatter={formatAxisTick} axisLine={false} tickLine={false} />
                                                        <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} axisLine={false} tickLine={false} width={40} />
                                                        <Tooltip
                                                            contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                                            labelStyle={{ color: '#6b7280', fontSize: '12px', marginBottom: '4px' }}
                                                            formatter={(value: number, name: string | number) => {
                                                                if (String(name).startsWith('trace_')) return undefined;
                                                                return [value.toFixed(3), name];
                                                            }}
                                                            labelFormatter={(label) => `Time: ${label}`}
                                                        />
                                                        <Legend content={() => (
                                                            <div className="flex flex-wrap justify-center gap-4 mt-2 text-xs">
                                                                <div className="flex items-center gap-1.5">
                                                                    <div className="w-4 h-0.5 bg-gray-400 opacity-30" />
                                                                    <span className="text-gray-500">Dry Days</span>
                                                                </div>
                                                                <div className="flex items-center gap-1.5">
                                                                    <div className="w-4 border-t-2 border-dashed border-blue-500" />
                                                                    <span className="text-gray-900">Min</span>
                                                                </div>
                                                                <div className="flex items-center gap-1.5">
                                                                    <div className="w-4 border-t-2 border-dashed border-red-300" />
                                                                    <span className="text-gray-900">Max</span>
                                                                </div>
                                                                <div className="flex items-center gap-1.5">
                                                                    <div className="w-4 h-0.5 bg-green-600" />
                                                                    <span className="text-gray-900">Mean</span>
                                                                </div>
                                                            </div>
                                                        )} />

                                                        {/* Individual Dry Day Traces */}
                                                        {/* Individual Dry Day Traces (Background) */}
                                                        {chartData && chartData.day_traces && chartData.day_traces.map((_, idx) => (
                                                            <Line
                                                                key={`trace_${idx}`}
                                                                type="monotone"
                                                                dataKey={`trace_${idx}`}
                                                                stroke="#9ca3af"
                                                                strokeWidth={1}
                                                                strokeOpacity={0.15}
                                                                dot={false}
                                                                isAnimationActive={false}
                                                                activeDot={false}
                                                                legendType="none"
                                                            />
                                                        ))}

                                                        <Line type="monotone" dataKey="min" stroke="#3b82f6" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Min" />
                                                        <Line type="monotone" dataKey="max" stroke="#fca5a5" strokeWidth={2} strokeDasharray="5 5" dot={false} name="Max" />
                                                        <Line type="monotone" dataKey="mean" stroke="#16a34a" strokeWidth={3} dot={false} name="Mean" />

                                                        {/* Highlighted Trace (On Top) */}
                                                        {hoveredDryDayDate && chartData?.day_traces && (() => {
                                                            const target = hoveredDryDayDate.split('T')[0];
                                                            const highlightIdx = chartData.day_traces.findIndex(t => t.date.split('T')[0] === target);
                                                            if (highlightIdx >= 0) {
                                                                return (
                                                                    <Line
                                                                        type="monotone"
                                                                        dataKey={`trace_${highlightIdx}`}
                                                                        stroke="#3b82f6"
                                                                        strokeWidth={3}
                                                                        strokeOpacity={1}
                                                                        dot={false}
                                                                        activeDot={{ r: 4, stroke: "#3b82f6" }}
                                                                        isAnimationActive={false}
                                                                        legendType="none"
                                                                    />
                                                                );
                                                            }
                                                            return null;
                                                        })()}
                                                    </LineChart>
                                                </ResponsiveContainer>
                                            </div>
                                        ) : (
                                            <div className="h-[300px] flex flex-col items-center justify-center text-gray-400 bg-gray-50 rounded-lg border-2 border-dashed border-gray-100">
                                                <Activity size={32} className="mb-2 opacity-50" />
                                                <p className="text-sm">No data for this series type</p>
                                            </div>
                                        )}

                                        {chartData && (
                                            <div className="mt-3 pt-3 border-t border-gray-100 flex justify-center">
                                                <span className="text-xs text-gray-500 bg-gray-50 px-3 py-1 rounded-full">
                                                    Based on {chartData.dry_day_count} detected dry days
                                                </span>
                                            </div>
                                        )}
                                    </div>

                                    {/* Dry Days Table */}
                                    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
                                        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50/50 flex items-center justify-between">
                                            <h4 className="font-semibold text-gray-900 text-sm">Detected Dry Days</h4>
                                            <span className="text-xs text-gray-500">
                                                {dryDays?.filter(d => d.is_included).length || 0} included
                                            </span>
                                        </div>

                                        {dryDaysLoading ? (
                                            <div className="p-4 text-center text-gray-500">Loading days...</div>
                                        ) : dryDays && dryDays.length > 0 ? (
                                            <div className="max-h-[400px] overflow-y-auto">
                                                <table className="w-full text-sm">
                                                    <thead className="bg-gray-50 sticky top-0 z-10 text-xs uppercase text-gray-500 font-medium">
                                                        <tr>
                                                            <th className="px-4 py-2 text-left bg-gray-50">Date</th>
                                                            <th className="px-4 py-2 text-right bg-gray-50">Day Rain</th>
                                                            <th className="px-4 py-2 text-right bg-gray-50">Ant. Rain</th>
                                                            <th className="px-4 py-2 text-center bg-gray-50">Status</th>
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-gray-100">
                                                        {dryDays.map((dd) => (
                                                            <tr
                                                                key={dd.id}
                                                                onMouseEnter={() => setHoveredDryDayDate(dd.date)}
                                                                onMouseLeave={() => setHoveredDryDayDate(null)}
                                                                className={`hover:bg-gray-50 transition-colors cursor-default ${!dd.is_included ? 'opacity-60 bg-gray-50/50' : ''}`}
                                                            >
                                                                <td className="px-4 py-2 font-mono text-gray-900">
                                                                    {new Date(dd.date).toLocaleDateString(undefined, { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' })}
                                                                </td>
                                                                <td className="px-4 py-2 text-right font-mono text-gray-600">{dd.day_rainfall_mm.toFixed(2)}</td>
                                                                <td className="px-4 py-2 text-right font-mono text-gray-600">{dd.antecedent_rainfall_mm.toFixed(2)}</td>
                                                                <td className="px-4 py-2 text-center">
                                                                    <button
                                                                        onClick={() => handleToggleDryDay(dd)}
                                                                        className={`
                                                                            p-1 rounded-md transition-colors
                                                                            ${dd.is_included
                                                                                ? 'text-green-600 bg-green-50 hover:bg-green-100'
                                                                                : 'text-gray-400 bg-gray-100 hover:bg-gray-200 hover:text-gray-600'
                                                                            }
                                                                        `}
                                                                    >
                                                                        {dd.is_included ? <CheckCircle size={14} /> : <X size={14} />}
                                                                    </button>
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        ) : (
                                            <div className="p-8 text-center text-gray-400">
                                                <Sun size={24} className="mx-auto mb-2 opacity-50" />
                                                <p className="text-sm">No dry days found</p>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-gray-400">
                                    <div className="bg-gray-50 p-6 rounded-2xl border-2 border-dashed border-gray-200 text-center max-w-sm">
                                        <Search size={48} className="mx-auto mb-4 text-gray-300" />
                                        <h3 className="font-medium text-gray-900 mb-1">Select a Monitor</h3>
                                        <p className="text-sm text-gray-500">
                                            Choose an import from the left sidebar and select a monitor to view its dry day analysis.
                                        </p>
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-gray-400">
                        <div className="bg-gray-50 p-6 rounded-2xl border-2 border-dashed border-gray-200 text-center max-w-sm">
                            <CloudRain size={48} className="mx-auto mb-4 text-gray-300" />
                            <h3 className="font-medium text-gray-900 mb-1">No Import Selected</h3>
                            <p className="text-sm text-gray-500">
                                Select an import from the list or upload a new file to get started.
                            </p>
                        </div>
                    </div>
                )}
            </div>

            {/* Import Dialog Overlay */}
            {showImportDialog && (
                <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                    <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full p-6">
                        <h3 className="text-xl font-bold text-gray-900 mb-6">Import Full Period Data</h3>

                        <div className="space-y-6">
                            <div className="space-y-2">
                                <label className="block text-sm font-medium text-gray-700">CSV File</label>
                                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 hover:border-green-500 hover:bg-green-50 transition-colors text-center cursor-pointer relative">
                                    <input
                                        type="file"
                                        accept=".csv"
                                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                                        onChange={handleFileSelect}
                                    />
                                    <Upload className="mx-auto text-gray-400 mb-2" />
                                    <p className="text-sm text-gray-600">
                                        {selectedFile ? selectedFile.name : "Click to select or drag file here"}
                                    </p>
                                </div>
                            </div>

                            {previewLoading && (
                                <div className="text-center text-sm text-gray-500">Analyzing file...</div>
                            )}

                            {previewResult && (
                                <div className="space-y-4">
                                    <div className="bg-gray-50 rounded-lg p-4 grid grid-cols-4 gap-4 text-sm">
                                        <div className={`flex items-center gap-2 ${previewResult.has_flow ? 'text-green-600' : 'text-gray-400'}`}>
                                            {previewResult.has_flow ? <CheckCircle size={16} /> : <X size={16} />} Flow
                                        </div>
                                        <div className={`flex items-center gap-2 ${previewResult.has_depth ? 'text-green-600' : 'text-gray-400'}`}>
                                            {previewResult.has_depth ? <CheckCircle size={16} /> : <X size={16} />} Depth
                                        </div>
                                        <div className={`flex items-center gap-2 ${previewResult.has_velocity ? 'text-green-600' : 'text-gray-400'}`}>
                                            {previewResult.has_velocity ? <CheckCircle size={16} /> : <X size={16} />} Velocity
                                        </div>
                                        <div className={`flex items-center gap-2 ${previewResult.has_rainfall ? 'text-green-600' : 'text-gray-400'}`}>
                                            {previewResult.has_rainfall ? <CheckCircle size={16} /> : <X size={16} />} Rainfall
                                        </div>
                                    </div>

                                    {!previewResult.has_rainfall && (
                                        <div className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg flex items-center gap-2">
                                            <AlertCircle size={16} /> Rainfall data is required for dry day detection.
                                        </div>
                                    )}

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Import Name</label>
                                        <input
                                            type="text"
                                            className="w-full border-gray-300 rounded-lg shadow-sm focus:ring-green-500 focus:border-green-500"
                                            value={importName}
                                            onChange={e => setImportName(e.target.value)}
                                        />
                                    </div>
                                </div>
                            )}

                            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                                <button
                                    onClick={() => {
                                        setShowImportDialog(false);
                                        setSelectedFile(null);
                                        setPreviewResult(null);
                                    }}
                                    className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg font-medium"
                                >
                                    Cancel
                                </button>
                                <button
                                    onClick={handleImport}
                                    disabled={!selectedFile || !importName || !previewResult?.has_rainfall || createImport.isPending}
                                    className="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    {createImport.isPending ? 'Importing...' : 'Import Data'}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
