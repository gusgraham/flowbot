import React, { useState, useMemo } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    ScatterChart, Scatter, ZAxis
} from 'recharts';
import { format } from 'date-fns';
import { ChevronDown, ChevronUp, Play, AlertCircle, Loader2 } from 'lucide-react';

interface RainfallEventsAnalysisProps {
    datasetIds: number[];
}

interface AnalysisParams {
    rainfallDepthTolerance: number;
    precedingDryDays: number;
    consecZero: number;
    interEventGap: number;
    requiredDepth: number;
    requiredIntensity: number;
    requiredIntensityDuration: number;
    partialPercent: number;
    useConsecutiveIntensities: boolean;
}

interface EventResult {
    event_id: number;
    dataset_id: number;
    dataset_name: string;
    start_time: string;
    end_time: string;
    total_mm: number;
    duration_hours: number;
    peak_intensity: number;
    status: string;
    passed: number;
}

interface DryDayResult {
    dataset_id: number;
    dataset_name: string;
    date: string;
    total_mm: number;
}

interface AnalysisResult {
    events: EventResult[];
    dry_days: DryDayResult[];
}

const RainfallEventsAnalysis: React.FC<RainfallEventsAnalysisProps> = ({ datasetIds }) => {
    const [params, setParams] = useState<AnalysisParams>({
        rainfallDepthTolerance: 0.1,
        precedingDryDays: 4,
        consecZero: 5,
        interEventGap: 360, // 6 hours default
        requiredDepth: 5,
        requiredIntensity: 6,
        requiredIntensityDuration: 4,
        partialPercent: 20,
        useConsecutiveIntensities: true
    });

    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isParamsOpen, setIsParamsOpen] = useState(true);

    const handleParamChange = (key: keyof AnalysisParams, value: any) => {
        setParams(prev => ({ ...prev, [key]: value }));
    };

    const runAnalysis = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/fsa/rainfall/events`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dataset_ids: datasetIds,
                    params: params
                })
            });

            if (!response.ok) throw new Error('Analysis failed');

            const data = await response.json();
            setResult(data);
            setIsParamsOpen(false);
        } catch (err) {
            setError('Failed to run analysis. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    // Prepare Gantt Data with numeric Y-axis
    const { ganttData, datasetMap } = useMemo(() => {
        if (!result?.events) return { ganttData: [], datasetMap: new Map() };

        // Create a map of dataset names to numeric indices
        const uniqueDatasets = Array.from(new Set(result.events.map(e => e.dataset_name))).sort();
        const map = new Map(uniqueDatasets.map((name, idx) => [name, idx]));

        const data = result.events.map(e => ({
            ...e,
            x: new Date(e.start_time).getTime(),
            y: map.get(e.dataset_name) ?? 0, // Numeric Y value
            duration: e.duration_hours
        }));

        return { ganttData: data, datasetMap: map };
    }, [result]);

    // Get dataset names in order for Y-axis labels
    const datasetNames = useMemo(() => {
        return Array.from(datasetMap.entries())
            .sort((a, b) => a[1] - b[1])
            .map(([name]) => name);
    }, [datasetMap]);

    const CustomGanttShape = (props: any) => {
        const { cx, cy, payload } = props;
        if (!payload) return null;

        const startX = new Date(payload.start_time).getTime();
        const endX = new Date(payload.end_time).getTime();

        // Get the scale from the chart context
        const chart = props.xAxis;
        if (!chart || !chart.scale) return null;

        const x1 = chart.scale(startX);
        const x2 = chart.scale(endX);
        const width = Math.max(x2 - x1, 4);
        const height = 20;

        let fill = '#9ca3af';
        if (payload.status === 'Event') fill = '#22c55e';
        if (payload.status === 'Partial Event') fill = '#f59e0b';
        if (payload.status === 'No Event') fill = '#ef4444';

        return (
            <rect
                x={x1}
                y={cy - height / 2}
                width={width}
                height={height}
                fill={fill}
                rx={2}
                opacity={0.8}
            />
        );
    };

    return (
        <div className="h-full flex flex-col space-y-4 p-4 overflow-y-auto">
            {/* Parameters Section */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                <button
                    onClick={() => setIsParamsOpen(!isParamsOpen)}
                    className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 rounded-t-lg hover:bg-gray-100 transition-colors"
                >
                    <span className="font-semibold text-gray-700">Analysis Parameters</span>
                    {isParamsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>

                {isParamsOpen && (
                    <div className="p-4 space-y-6">
                        {/* Storm Event Detection */}
                        <div>
                            <h4 className="text-sm font-semibold text-gray-900 mb-3 border-b pb-1">Storm Event Detection</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Required Depth (mm)</label>
                                    <input
                                        type="number"
                                        value={params.requiredDepth}
                                        onChange={e => handleParamChange('requiredDepth', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Required Intensity (mm/hr)</label>
                                    <input
                                        type="number"
                                        value={params.requiredIntensity}
                                        onChange={e => handleParamChange('requiredIntensity', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Req. Intensity Duration (min)</label>
                                    <input
                                        type="number"
                                        value={params.requiredIntensityDuration}
                                        onChange={e => handleParamChange('requiredIntensityDuration', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Partial Event %</label>
                                    <input
                                        type="number"
                                        value={params.partialPercent}
                                        onChange={e => handleParamChange('partialPercent', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Inter-event Gap (min)</label>
                                    <input
                                        type="number"
                                        value={params.interEventGap}
                                        onChange={e => handleParamChange('interEventGap', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Dry Day Detection */}
                        <div>
                            <h4 className="text-sm font-semibold text-gray-900 mb-3 border-b pb-1">Dry Day Detection</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Rainfall Depth Tolerance (mm)</label>
                                    <input
                                        type="number"
                                        value={params.rainfallDepthTolerance}
                                        onChange={e => handleParamChange('rainfallDepthTolerance', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Preceding Dry Days</label>
                                    <input
                                        type="number"
                                        value={params.precedingDryDays}
                                        onChange={e => handleParamChange('precedingDryDays', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end pt-2">
                            <button
                                onClick={runAnalysis}
                                disabled={isLoading}
                                className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center disabled:opacity-50"
                            >
                                {isLoading ? <Loader2 className="animate-spin mr-2" /> : <Play size={18} className="mr-2" />}
                                Run Analysis
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {error && (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center">
                    <AlertCircle size={20} className="mr-2" />
                    {error}
                </div>
            )}

            {/* Results */}
            {result && (
                <div className="space-y-6">
                    {/* Gantt Chart */}
                    <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm" style={{ height: '400px' }}>
                        <h3 className="text-lg font-semibold mb-4">Rainfall Events Gantt Chart</h3>
                        <ResponsiveContainer width="100%" height="90%">
                            <ScatterChart margin={{ top: 20, right: 30, bottom: 20, left: 120 }}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    type="number"
                                    dataKey="x"
                                    domain={['auto', 'auto']}
                                    tickFormatter={(unixTime) => format(new Date(unixTime), 'MMM d HH:mm')}
                                    name="Time"
                                />
                                <YAxis
                                    type="number"
                                    dataKey="y"
                                    domain={[0, Math.max(0, datasetNames.length - 1)]}
                                    ticks={Array.from({ length: datasetNames.length }, (_, i) => i)}
                                    tickFormatter={(value) => datasetNames[value] || ''}
                                    width={100}
                                    name="Dataset"
                                />
                                <Tooltip
                                    cursor={{ strokeDasharray: '3 3' }}
                                    content={({ active, payload }) => {
                                        if (active && payload && payload.length) {
                                            const data = payload[0].payload;
                                            return (
                                                <div className="bg-white p-2 border border-gray-200 shadow-lg rounded text-sm">
                                                    <p className="font-semibold">{data.dataset_name}</p>
                                                    <p>Status: <span className={
                                                        data.status === 'Event' ? 'text-green-600 font-bold' :
                                                            data.status === 'Partial Event' ? 'text-orange-500 font-bold' : 'text-red-500'
                                                    }>{data.status}</span></p>
                                                    <p>Start: {format(new Date(data.start_time), 'MMM d HH:mm')}</p>
                                                    <p>End: {format(new Date(data.end_time), 'MMM d HH:mm')}</p>
                                                    <p>Total: {data.total_mm} mm</p>
                                                    <p>Peak: {data.peak_intensity} mm/hr</p>
                                                </div>
                                            );
                                        }
                                        return null;
                                    }}
                                />
                                <Legend
                                    payload={[
                                        { value: 'Event', type: 'rect', color: '#22c55e' },
                                        { value: 'Partial Event', type: 'rect', color: '#f59e0b' },
                                        { value: 'No Event', type: 'rect', color: '#ef4444' }
                                    ]}
                                />
                                <Scatter
                                    data={ganttData}
                                    shape={<CustomGanttShape />}
                                />
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Event Table */}
                    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
                        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                            <h3 className="font-semibold text-gray-700">Detected Events ({result.events.length})</h3>
                        </div>
                        <div className="overflow-x-auto max-h-96">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50 sticky top-0">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dataset</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration (hr)</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total (mm)</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Peak (mm/hr)</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {result.events.map((event, idx) => (
                                        <tr key={`${event.dataset_id}-${event.event_id}-${idx}`} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {event.dataset_name}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${event.status === 'Event' ? 'bg-green-100 text-green-800' :
                                                        event.status === 'Partial Event' ? 'bg-orange-100 text-orange-800' :
                                                            'bg-red-100 text-red-800'
                                                    }`}>
                                                    {event.status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {format(new Date(event.start_time), 'MMM d HH:mm')}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {event.duration_hours}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {event.total_mm}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {event.peak_intensity}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>

                    {/* Dry Days Table */}
                    {result.dry_days && result.dry_days.length > 0 && (
                        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
                            <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
                                <h3 className="font-semibold text-gray-700">Dry Days ({result.dry_days.length})</h3>
                            </div>
                            <div className="overflow-x-auto max-h-96">
                                <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50 sticky top-0">
                                        <tr>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dataset</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total (mm)</th>
                                        </tr>
                                    </thead>
                                    <tbody className="bg-white divide-y divide-gray-200">
                                        {result.dry_days.map((day, idx) => (
                                            <tr key={`${day.dataset_id}-${day.date}-${idx}`} className="hover:bg-gray-50">
                                                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                    {day.dataset_name}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                    {day.date}
                                                </td>
                                                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                    {day.total_mm}
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default RainfallEventsAnalysis;
