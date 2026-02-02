import React, { useMemo, useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';
import { Loader2, Download, RefreshCw, X } from 'lucide-react';
import { useDWFAnalysis, useDWFDryDays, useToggleDWFDryDay, useDWFSGSettings, useUpdateDWFSGSettings } from '../../api/hooks';

interface DWFAnalysisProps {
    datasetId: number;
    projectId: number;
    candidateEventIds?: number[]; // From sidebar selection
    onExport?: () => void;
}

// Helper to format seconds to HH:MM
const formatTime = (seconds: number) => {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}`;
};

// Event traces should be grey
const EVENT_COLOR = '#888888';
// Profile colors
const AVG_COLOR = '#0000FF'; // Blue
const MIN_COLOR = '#00AA00'; // Green
const MAX_COLOR = '#FF0000'; // Red

// Custom hook for debouncing values
function useDebounce<T>(value: T, delay: number): T {
    const [debouncedValue, setDebouncedValue] = useState(value);

    useEffect(() => {
        const timer = setTimeout(() => setDebouncedValue(value), delay);
        return () => clearTimeout(timer);
    }, [value, delay]);

    return debouncedValue;
}

const DWFAnalysis: React.FC<DWFAnalysisProps> = ({ datasetId, projectId: _projectId, candidateEventIds, onExport }) => {
    // 1. Fetch Data
    const { data: dryDays, isLoading: isLoadingStatus } = useDWFDryDays(datasetId);

    // Load saved SG settings for this monitor
    const { data: savedSettings, isLoading: isLoadingSettings } = useDWFSGSettings(datasetId);
    const updateSettings = useUpdateDWFSGSettings();

    // SG Filter State (UI state, updates immediately)
    const [sgEnabled, setSgEnabled] = useState(false);
    const [sgWindow, setSgWindow] = useState(21);
    const [sgOrder, setSgOrder] = useState(3);
    const [settingsInitialized, setSettingsInitialized] = useState(false);

    // Initialize state from saved settings once loaded
    useEffect(() => {
        if (savedSettings && !settingsInitialized) {
            setSgEnabled(savedSettings.sg_enabled);
            setSgWindow(savedSettings.sg_window);
            setSgOrder(savedSettings.sg_order);
            setSettingsInitialized(true);
        }
    }, [savedSettings, settingsInitialized]);

    // Reset initialization when dataset changes
    useEffect(() => {
        setSettingsInitialized(false);
    }, [datasetId]);

    // Debounced values for API calls (delays by 300ms to avoid spam)
    const debouncedWindow = useDebounce(sgWindow, 300);
    const debouncedOrder = useDebounce(sgOrder, 300);

    // Auto-save settings when debounced values change (only after initialized)
    useEffect(() => {
        if (settingsInitialized) {
            updateSettings.mutate({
                datasetId,
                sgEnabled,
                sgWindow: debouncedWindow,
                sgOrder: debouncedOrder
            });
        }
    }, [sgEnabled, debouncedWindow, debouncedOrder, settingsInitialized, datasetId]);

    const { data: analysis, isLoading: isLoadingAnalysis, isFetching: isFetchingAnalysis, refetch: refetchAnalysis } = useDWFAnalysis(
        datasetId,
        candidateEventIds,
        { enabled: sgEnabled, window: debouncedWindow, order: debouncedOrder }
    );
    const toggleMutation = useToggleDWFDryDay();
    const [hoveredEventId, setHoveredEventId] = useState<number | null>(null);
    const [variable, setVariable] = useState<'Flow' | 'Depth' | 'Velocity'>('Flow');

    // 2. Prepare Data for Chart
    const { chartData, series } = useMemo(() => {
        if (!analysis || !dryDays) return { chartData: [], series: [] };

        // Create time grid (0 to 86400 step 120s usually, or whatever is in data)
        // We iterate through profile to get times
        const timeMap = new Map<number, any>();

        // Add profile data (Avg/Min/Max)

        const field = variable.toLowerCase();
        analysis.profile.forEach((p: any) => {
            const t = p.time_of_day_seconds;
            if (!timeMap.has(t)) {
                timeMap.set(t, { time: t, label: formatTime(t) });
            }
            const entry = timeMap.get(t);
            entry['avg'] = p[`${field}_mean`];
            entry['min'] = p[`${field}_min`];
            entry['max'] = p[`${field}_max`];
        });

        // Add individual traces
        // We need to map traces to event IDs.
        // The analysis result has 'traces' with 'date'. We need to match date to dryDays to get ID.
        // Or simpler: The backend just sends dates.
        // Wait, backend `traces` structure: { date: "YYYY-MM-DD", data: [...] }
        // We match `date` to `dryDays` (start_time).

        const traceSeries: any[] = [];

        analysis.traces.forEach((trace: any) => {
            // Find event for this date
            const textDate = trace.date;
            const traceEventId = trace.event_id;

            // Improve matching if needed (timezone issues?)
            // Assuming simplified matching
            const event = traceEventId
                ? dryDays.find(d => d.id === traceEventId)
                : dryDays.find(d => d.start_time.startsWith(textDate));

            // Should we filter by candidateEventIds here?
            // The backend computed it based on candidateEventIds, so traces returned should match.
            // But if candidateEventIds changed, query refetches.
            // However, dryDays contains ALL events.

            // If we can't find event, skipped (maybe excluded by sidebar? or mismatch)
            if (!event) return;

            // Check if in candidate list (double check)
            if (candidateEventIds && !candidateEventIds.includes(event.id)) return;

            const exclude = !event.enabled;
            const key = `event_${event.id}`;
            const color = EVENT_COLOR;

            traceSeries.push({
                id: event.id,
                name: event.name || event.start_time.split('T')[0],
                key,
                color,
                strokeDasharray: exclude ? "5 5" : undefined,
                opacity: exclude ? 0.4 : 0.6, // Semi-transparent for all events to see density
                strokeWidth: 1
            });

            // Add data to time map
            trace.data.forEach((d: any) => {
                const t = d.time_of_day_seconds;
                if (!timeMap.has(t)) timeMap.set(t, { time: t, label: formatTime(t) });
                const entry = timeMap.get(t);
                entry[key] = d[field];
            });
        });

        const sortedData = Array.from(timeMap.values()).sort((a, b) => a.time - b.time);
        return { chartData: sortedData, series: traceSeries };

    }, [analysis, dryDays, candidateEventIds, variable]);

    const handleLegendClick = (data: any) => {
        // data has payload with our series config? Recharts passes payload.
        // We stored id in series.
        // Recharts payload structure: { value, id, type, color, payload: { id, key ... } }
        // The `data` argument in onClick is the payload object.
        const eventId = data.payload?.id;
        if (eventId) {
            // Check current status
            const event = dryDays?.find(d => d.id === eventId);
            if (event) {
                // If currently enabled => exclude it.
                // If disabled => include it.
                // Note: Enabled = !Excluded.
                toggleMutation.mutate({
                    datasetId,
                    eventId,
                    exclude: event.enabled // if enabled, we exclude.
                });
            }
        }
    }


    const traceLines = useMemo(() => series.map(s => (
        <Line
            key={s.id}
            type="monotone"
            dataKey={s.key}
            stroke={s.color}
            strokeWidth={s.strokeWidth}
            strokeDasharray={s.strokeDasharray}
            opacity={s.opacity}
            dot={false}
            name={s.name}
            activeDot={{ r: 4 }}
            isAnimationActive={false}
        />
    )), [series]);

    // Only show full loading screen on initial load (no existing data)
    const isInitialLoading = (isLoadingStatus && !dryDays) || (isLoadingAnalysis && !analysis);

    if (isInitialLoading) {
        return <div className="h-64 flex items-center justify-center"><Loader2 className="animate-spin text-purple-600" /></div>;
    }

    return (
        <div className="space-y-4 h-full flex flex-col">
            <div className="flex justify-between items-center px-2">
                <div className="flex items-center gap-4">
                    <h3 className="font-semibold text-gray-800">Dry Weather Flow Analysis</h3>
                    {isFetchingAnalysis && <Loader2 className="animate-spin text-purple-400" size={16} />}
                    <div className="flex bg-gray-100 p-1 rounded-lg">
                        {(['Flow', 'Depth', 'Velocity'] as const).map(v => (
                            <button
                                key={v}
                                onClick={() => setVariable(v)}
                                className={`px-3 py-1 text-xs font-medium rounded-md transition-colors ${variable === v ? 'bg-white text-purple-600 shadow-sm' : 'text-gray-500 hover:text-gray-700'}`}
                            >
                                {v}
                            </button>
                        ))}
                    </div>
                </div>

                {/* SG Filter Controls */}
                <div className="flex items-center gap-3 bg-gray-50 px-3 py-1.5 rounded-lg border border-gray-200">
                    <div className="flex items-center gap-2">
                        <input
                            type="checkbox"
                            checked={sgEnabled}
                            onChange={e => setSgEnabled(e.target.checked)}
                            id="sg-toggle"
                            className="rounded text-purple-600 focus:ring-purple-500 w-4 h-4 cursor-pointer"
                        />
                        <label htmlFor="sg-toggle" className="text-xs font-medium text-gray-700 cursor-pointer select-none">SG Filter</label>
                    </div>
                    {sgEnabled && (
                        <>
                            <div className="w-px h-4 bg-gray-300 mx-1"></div>
                            <div className="flex items-center gap-1">
                                <label className="text-[10px] text-gray-500 uppercase font-bold">Win</label>
                                <input
                                    type="number"
                                    value={sgWindow}
                                    onChange={e => {
                                        let val = parseInt(e.target.value);
                                        // Simple validation, effect will clamp in hook/backend but UI feedback good
                                        setSgWindow(val);
                                    }}
                                    onBlur={() => {
                                        // Enforce odd on blur
                                        let val = sgWindow;
                                        if (val % 2 === 0) val += 1;
                                        if (val < 3) val = 3;
                                        setSgWindow(val);
                                    }}
                                    step={2}
                                    className="w-12 px-1 py-0.5 text-xs border border-gray-300 rounded text-center"
                                />
                            </div>
                            <div className="flex items-center gap-1">
                                <label className="text-[10px] text-gray-500 uppercase font-bold">Poly</label>
                                <input
                                    type="number"
                                    value={sgOrder}
                                    onChange={e => setSgOrder(Math.max(1, Math.min(5, parseInt(e.target.value))))}
                                    min={1} max={5}
                                    className="w-10 px-1 py-0.5 text-xs border border-gray-300 rounded text-center"
                                />
                            </div>
                        </>
                    )}
                </div>

                <div className="flex gap-2">
                    <button onClick={() => refetchAnalysis()} className="p-2 text-gray-500 hover:text-purple-600 rounded">
                        <RefreshCw size={18} />
                    </button>
                    <button onClick={onExport} className="p-2 text-gray-500 hover:text-purple-600 rounded">
                        <Download size={18} />
                    </button>
                </div>
            </div>

            <div className="flex-1 min-h-0 flex gap-4">
                {/* Main Chart */}
                <div className="flex-1 bg-white border border-gray-200 rounded-lg p-4 flex flex-col">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis
                                dataKey="label"
                                tick={{ fontSize: 10 }}
                                minTickGap={30}
                            />
                            <YAxis
                                label={{ value: `${variable} (${variable === 'Flow' ? 'l/s' : variable === 'Depth' ? 'mm' : 'm/s'})`, angle: -90, position: 'insideLeft' }}
                                tick={{ fontSize: 10 }}
                            />
                            <Tooltip />
                            <Legend onClick={handleLegendClick} wrapperStyle={{ cursor: 'pointer' }} />

                            {/* Avg/Min/Max Profile */}
                            <Line type="monotone" dataKey="avg" stroke={AVG_COLOR} strokeWidth={3} dot={false} name="Average" />
                            <Line type="monotone" dataKey="min" stroke={MIN_COLOR} strokeWidth={2} dot={false} name="Min" />
                            <Line type="monotone" dataKey="max" stroke={MAX_COLOR} strokeWidth={2} dot={false} name="Max" legendType="none" />

                            {/* Individual Events (Memoized for performance) */}
                            {traceLines}

                            {/* Halo Line for Hovered Event (Rendered on top but behind others in z-order? No, Recharts renders in order. 
                               If we want Halo BEHIND, it must be rendered BEFORE traces. 
                               But invalidating traces to render Halo behind might cause flicker.
                               Visuals: Halo on TOP is fine or just around.
                               Actually, standard SVG: last one is on top. Halo should be active/highlighted.
                               User asked for highlight. Halo on top is good.
                            */}
                            {hoveredEventId && (() => {
                                const s = series.find(s => s.id === hoveredEventId);
                                if (s) {
                                    return (
                                        <Line
                                            key={`halo-${s.id}`}
                                            type="monotone"
                                            dataKey={s.key}
                                            stroke="#FFD700"
                                            strokeWidth={6}
                                            strokeOpacity={0.6}
                                            dot={false}
                                            activeDot={false}
                                            legendType="none"
                                            isAnimationActive={false}
                                        />
                                    );
                                }
                                return null;
                            })()}
                        </LineChart>
                    </ResponsiveContainer>
                </div>

                {/* Stats Panel */}
                <div className="w-64 bg-gray-50 border border-gray-200 rounded-lg p-4 overflow-y-auto">
                    <h4 className="font-medium text-gray-700 mb-2">Statistics</h4>
                    <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-gray-500">Total Days:</span>
                            <span className="font-medium">{analysis?.stats?.total_days}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-500">Avg {variable}:</span>
                            <span className="font-medium">{analysis?.stats?.[`${variable.toLowerCase()}_avg`]?.toFixed(3)} {variable === 'Flow' ? 'l/s' : variable === 'Depth' ? 'mm' : 'm/s'}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-500">Peak {variable}:</span>
                            <span className="font-medium">{analysis?.stats?.[`${variable.toLowerCase()}_max`]?.toFixed(3)} {variable === 'Flow' ? 'l/s' : variable === 'Depth' ? 'mm' : 'm/s'}</span>
                        </div>
                    </div>

                    <div className="mt-6">
                        <h4 className="font-medium text-gray-700 mb-2">Events</h4>
                        <div className="space-y-1 max-h-96 overflow-y-auto pr-2">
                            {series.map(s => (
                                <div
                                    key={s.id}
                                    onClick={() => handleLegendClick({ payload: { id: s.id } })}
                                    onMouseEnter={() => setHoveredEventId(s.id)}
                                    onMouseLeave={() => setHoveredEventId(null)}
                                    className={`flex items-center justify-between text-xs p-1.5 rounded cursor-pointer transition-colors ${s.strokeDasharray ? 'bg-gray-100 text-gray-500' : 'bg-white shadow-sm text-gray-900 border border-gray-200'} ${hoveredEventId === s.id ? 'ring-2 ring-yellow-400 bg-yellow-50' : ''}`}
                                >
                                    <div className="flex items-center gap-2">
                                        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: s.color }}></div>
                                        <span className={s.strokeDasharray ? 'text-gray-400' : ''}>{s.name}</span>
                                    </div>
                                    <span className={s.strokeDasharray ? 'text-red-500' : 'text-green-600 font-bold'}>
                                        {s.strokeDasharray ? <X size={14} /> : '✓'}
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DWFAnalysis;
