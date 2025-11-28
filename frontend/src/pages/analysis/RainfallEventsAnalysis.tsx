import React, { useState } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    BarChart, Bar, ComposedChart, Area, ReferenceArea, Cell
} from 'recharts';
import { format } from 'date-fns';
import { ChevronDown, ChevronUp, Play, AlertCircle, Loader2 } from 'lucide-react';

interface RainfallEventsAnalysisProps {
    datasetId: number;
    datasetName: string;
}

interface AnalysisParams {
    rainfallDepthTolerance: number;
    precedingDryDays: number;
    consecZero: number;
    requiredDepth: number;
    requiredIntensity: number;
    requiredIntensityDuration: number;
    partialPercent: number;
    useConsecutiveIntensities: boolean;
}

interface EventResult {
    Start: string;
    End: string;
    Depth: number;
    Intensity_Count: number;
    Passed: number;
    Status: string;
}

interface AnalysisResult {
    events: EventResult[];
    dry_days: string[];
    timeseries: { time: string; value: number }[];
    stats: {
        total_events: number;
        total_rainfall_depth: number;
        analyzed_period_start: string;
        analyzed_period_end: string;
    };
}

const RainfallEventsAnalysis: React.FC<RainfallEventsAnalysisProps> = ({ datasetId, datasetName }) => {
    const [params, setParams] = useState<AnalysisParams>({
        rainfallDepthTolerance: 0,
        precedingDryDays: 4,
        consecZero: 5,
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

    // Chart State
    const [isEventCountsOpen, setIsEventCountsOpen] = useState(true);
    const [isGanttOpen, setIsGanttOpen] = useState(true);
    const [isIntensityOpen, setIsIntensityOpen] = useState(false); // Collapsed by default

    const handleParamChange = (key: keyof AnalysisParams, value: any) => {
        setParams(prev => ({ ...prev, [key]: value }));
    };

    const runAnalysis = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/analysis/rainfall/events?dataset_id=${datasetId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(params)
            });

            if (!response.ok) throw new Error('Analysis failed');

            const data = await response.json();
            setResult(data);
            setIsParamsOpen(false); // Auto-collapse on success
        } catch (err) {
            setError('Failed to run analysis. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    // Helper to format X-axis ticks
    const formatXAxis = (tickItem: number) => {
        return format(new Date(tickItem), 'MMM d');
    };

    // Prepare data for charts
    const prepareChartData = () => {
        if (!result) return { eventCounts: [], ganttData: [], intensityData: [] };

        // 1. Event Counts (Step Plot)
        // We need a time series of "Number of RGs passed". 
        // Since we only have 1 dataset here, it's either 0 or 1.
        // For multi-dataset (future), we'd sum them up.
        // For now, let's create a step function based on events.

        // 2. Gantt Data
        // We need start/end for each event and its status.
        const ganttData = result.events.map((e, i) => ({
            id: i,
            name: `Event ${i + 1}`,
            start: new Date(e.Start).getTime(),
            end: new Date(e.End).getTime(),
            status: e.Status, // Event, Partial Event, No Event
            depth: e.Depth,
            duration: (new Date(e.End).getTime() - new Date(e.Start).getTime()) / (1000 * 3600)
        }));

        // 3. Intensity Data
        const intensityData = result.timeseries ? result.timeseries.map((t: any) => ({
            time: new Date(t.time).getTime(),
            value: t.value
        })) : [];

        return { ganttData, intensityData };
    };

    const { ganttData, intensityData } = prepareChartData();

    return (
        <div className="h-full flex flex-col space-y-4 p-4 overflow-auto">
            {/* Parameters Section */}
            <div className="bg-white rounded-lg shadow border border-gray-200 flex-shrink-0">
                <button
                    onClick={() => setIsParamsOpen(!isParamsOpen)}
                    className="w-full flex justify-between items-center p-4 bg-gray-50 hover:bg-gray-100 rounded-t-lg transition-colors"
                >
                    <span className="font-semibold text-gray-700 flex items-center">
                        <span className="mr-2">Analysis Parameters</span>
                        {!isParamsOpen && result && (
                            <span className="text-xs font-normal text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                                {result.stats.total_events} events found
                            </span>
                        )}
                    </span>
                    {isParamsOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                </button>

                {isParamsOpen && (
                    <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Depth Tolerance (mm)</label>
                            <input
                                type="number"
                                value={params.rainfallDepthTolerance}
                                onChange={e => handleParamChange('rainfallDepthTolerance', parseFloat(e.target.value))}
                                className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Preceding Dry Days</label>
                            <input
                                type="number"
                                value={params.precedingDryDays}
                                onChange={e => handleParamChange('precedingDryDays', parseInt(e.target.value))}
                                className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Consecutive Zeros</label>
                            <input
                                type="number"
                                value={params.consecZero}
                                onChange={e => handleParamChange('consecZero', parseInt(e.target.value))}
                                className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Required Depth (mm)</label>
                            <input
                                type="number"
                                value={params.requiredDepth}
                                onChange={e => handleParamChange('requiredDepth', parseFloat(e.target.value))}
                                className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Req. Intensity (mm/hr)</label>
                            <input
                                type="number"
                                value={params.requiredIntensity}
                                onChange={e => handleParamChange('requiredIntensity', parseFloat(e.target.value))}
                                className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Req. Int. Duration (mins)</label>
                            <input
                                type="number"
                                value={params.requiredIntensityDuration}
                                onChange={e => handleParamChange('requiredIntensityDuration', parseInt(e.target.value))}
                                className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Partial Percent (%)</label>
                            <input
                                type="number"
                                value={params.partialPercent}
                                onChange={e => handleParamChange('partialPercent', parseInt(e.target.value))}
                                className="w-full p-2 border rounded focus:ring-2 focus:ring-purple-500"
                            />
                        </div>
                        <div className="flex items-center pt-6">
                            <label className="flex items-center cursor-pointer">
                                <input
                                    type="checkbox"
                                    checked={params.useConsecutiveIntensities}
                                    onChange={e => handleParamChange('useConsecutiveIntensities', e.target.checked)}
                                    className="mr-2 h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded"
                                />
                                <span className="text-sm font-medium text-gray-700">Use Consecutive Intensities</span>
                            </label>
                        </div>

                        <div className="col-span-full flex justify-end mt-2">
                            <button
                                onClick={runAnalysis}
                                disabled={isLoading}
                                className="flex items-center px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50 transition-colors"
                            >
                                {isLoading ? <Loader2 className="animate-spin mr-2" size={18} /> : <Play className="mr-2" size={18} />}
                                Run Analysis
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 p-4 rounded-lg flex items-center flex-shrink-0">
                    <AlertCircle className="mr-2" size={20} />
                    {error}
                </div>
            )}

            {/* Results Section */}
            {result && (
                <div className="flex-1 flex flex-col space-y-4 min-h-0">

                    {/* 1. Event Counts (Placeholder for now as we only have 1 dataset) */}
                    <div className="bg-white rounded-lg shadow border border-gray-200 flex-shrink-0">
                        <button
                            onClick={() => setIsEventCountsOpen(!isEventCountsOpen)}
                            className="w-full flex justify-between items-center p-3 bg-gray-50 hover:bg-gray-100 rounded-t-lg transition-colors"
                        >
                            <span className="font-semibold text-gray-700">Event Counts</span>
                            {isEventCountsOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </button>
                        {isEventCountsOpen && (
                            <div className="p-4 h-48">
                                <ResponsiveContainer width="100%" height="100%">
                                    <BarChart data={ganttData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="start"
                                            type="number"
                                            domain={['dataMin', 'dataMax']}
                                            tickFormatter={formatXAxis}
                                            scale="time"
                                        />
                                        <YAxis label={{ value: 'Count', angle: -90, position: 'insideLeft' }} />
                                        <Tooltip
                                            labelFormatter={(label) => format(new Date(label), 'MMM d HH:mm')}
                                        />
                                        <Legend />
                                        <Bar dataKey="passed" name="Events Passed" fill="#33FF33" />
                                    </BarChart>
                                </ResponsiveContainer>
                            </div>
                        )}
                    </div>

                    {/* 2. Gantt Chart */}
                    <div className="bg-white rounded-lg shadow border border-gray-200 flex-shrink-0">
                        <button
                            onClick={() => setIsGanttOpen(!isGanttOpen)}
                            className="w-full flex justify-between items-center p-3 bg-gray-50 hover:bg-gray-100 rounded-t-lg transition-colors"
                        >
                            <span className="font-semibold text-gray-700">Rainfall Gantt Chart</span>
                            {isGanttOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </button>
                        {isGanttOpen && (
                            <div className="p-4 h-64 overflow-y-auto">
                                {/* Custom Gantt Visualization using Scatter Chart for flexibility */}
                                <ResponsiveContainer width="100%" height="100%">
                                    <ComposedChart
                                        layout="vertical"
                                        data={ganttData}
                                        margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
                                    >
                                        <CartesianGrid stroke="#f5f5f5" />
                                        <XAxis type="number" domain={['dataMin', 'dataMax']} tickFormatter={formatXAxis} scale="time" />
                                        <YAxis dataKey="name" type="category" width={80} />
                                        <Tooltip
                                            content={({ active, payload }) => {
                                                if (active && payload && payload.length) {
                                                    const data = payload[0].payload;
                                                    return (
                                                        <div className="bg-white p-2 border border-gray-200 shadow rounded z-50">
                                                            <p className="font-bold">{data.name}</p>
                                                            <p>Status: {data.status}</p>
                                                            <p>Start: {format(new Date(data.start), 'MMM d HH:mm')}</p>
                                                            <p>End: {format(new Date(data.end), 'MMM d HH:mm')}</p>
                                                            <p>Depth: {data.depth.toFixed(2)} mm</p>
                                                        </div>
                                                    );
                                                }
                                                return null;
                                            }}
                                        />
                                        <Bar dataKey="duration" barSize={20} background={{ fill: '#eee' }}>
                                            {ganttData.map((entry, index) => {
                                                let color = '#E57373'; // No Event (Red)
                                                if (entry.status === 'Event') color = '#33FF33'; // Event (Green)
                                                else if (entry.status === 'Partial Event') color = '#FFA726'; // Partial (Orange)

                                                return <Cell key={`cell-${index}`} fill={color} />;
                                            })}
                                        </Bar>
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </div>
                        )}
                    </div>

                    {/* 3. Rainfall Intensity (Collapsed by Default) */}
                    <div className="bg-white rounded-lg shadow border border-gray-200 flex-shrink-0">
                        <button
                            onClick={() => setIsIntensityOpen(!isIntensityOpen)}
                            className="w-full flex justify-between items-center p-3 bg-gray-50 hover:bg-gray-100 rounded-t-lg transition-colors"
                        >
                            <span className="font-semibold text-gray-700">Rainfall Intensity</span>
                            {isIntensityOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                        </button>
                        {isIntensityOpen && (
                            <div className="p-4 h-64">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={intensityData}>
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="time"
                                            type="number"
                                            domain={['dataMin', 'dataMax']}
                                            tickFormatter={formatXAxis}
                                            scale="time"
                                        />
                                        <YAxis label={{ value: 'Intensity (mm/hr)', angle: -90, position: 'insideLeft' }} />
                                        <Tooltip
                                            labelFormatter={(label) => format(new Date(label), 'MMM d HH:mm')}
                                        />
                                        <Line type="monotone" dataKey="value" stroke="#8884d8" dot={false} strokeWidth={1.5} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default RainfallEventsAnalysis;
