import React, { useMemo, useState } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    Legend, ResponsiveContainer, BarChart, Bar, ComposedChart, Area,
    ScatterChart, Scatter, ZAxis, Cell
} from 'recharts';
import { Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import { useInstallTimeseries } from '../../../api/hooks';

interface FlowMonitorChartProps {
    installId: number;
    startDate?: string;
    endDate?: string;
    pipeHeight?: number;
}

const COLORS = {
    depth: '#EF4444',      // red
    velocity: '#22C55E',   // green
    flow: '#3B82F6',       // blue
    rain: '#0EA5E9',       // cyan
    soffit: '#1E3A8A',     // dark blue
};

const FlowMonitorChart: React.FC<FlowMonitorChartProps> = ({ installId, startDate, endDate, pipeHeight = 225 }) => {
    const [showFdv, setShowFdv] = useState(true);
    const [showDwf, setShowDwf] = useState(false);

    const { data, isLoading, error } = useInstallTimeseries(
        installId,
        'Processed',
        startDate,
        endDate,
        10000
    );

    const { chartData, dwfData, stats } = useMemo(() => {
        if (!data?.variables) return { chartData: [], dwfData: [], stats: {} };

        const timeMap = new Map<number, any>();
        const dwfMap = new Map<number, any[]>(); // Time of day -> values per day

        Object.entries(data.variables).forEach(([varName, varData]) => {
            (varData as any).data?.forEach((point: { time: string; value: number }) => {
                const date = new Date(point.time);
                const ts = date.getTime();

                if (!timeMap.has(ts)) {
                    timeMap.set(ts, { time: ts });
                }
                timeMap.get(ts)![varName] = point.value;

                // For DWF: group by time of day (minutes since midnight)
                const timeOfDay = date.getHours() * 60 + date.getMinutes();
                if (!dwfMap.has(timeOfDay)) {
                    dwfMap.set(timeOfDay, []);
                }
                dwfMap.get(timeOfDay)!.push({ [varName]: point.value });
            });
        });

        const sortedData = Array.from(timeMap.values()).sort((a, b) => a.time - b.time);

        // Calculate DWF averages
        const dwfAvg: any[] = [];
        dwfMap.forEach((values, timeOfDay) => {
            const avgPoint: any = { timeOfDay };
            ['Depth', 'Velocity', 'Flow'].forEach(varName => {
                const vals = values.map(v => v[varName]).filter(v => v !== undefined);
                if (vals.length > 0) {
                    avgPoint[varName] = vals.reduce((a, b) => a + b, 0) / vals.length;
                }
            });
            dwfAvg.push(avgPoint);
        });
        dwfAvg.sort((a, b) => a.timeOfDay - b.timeOfDay);

        // Calculate stats
        const flowVals = sortedData.map(d => d.Flow).filter(v => v !== undefined);
        const depthVals = sortedData.map(d => d.Depth).filter(v => v !== undefined);

        const statistics = {
            dataPoints: sortedData.length,
            flowMax: flowVals.length > 0 ? Math.max(...flowVals) : 0,
            flowAvg: flowVals.length > 0 ? flowVals.reduce((a, b) => a + b, 0) / flowVals.length : 0,
            depthMax: depthVals.length > 0 ? Math.max(...depthVals) : 0,
            depthAvg: depthVals.length > 0 ? depthVals.reduce((a, b) => a + b, 0) / depthVals.length : 0,
        };

        return { chartData: sortedData, dwfData: dwfAvg, stats: statistics };
    }, [data]);

    const formatDate = (timestamp: number) => {
        return new Date(timestamp).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
    };

    const formatTime = (minutes: number) => {
        const hrs = Math.floor(minutes / 60);
        const mins = minutes % 60;
        return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-blue-500" size={32} />
            </div>
        );
    }

    if (error || !data || chartData.length === 0) {
        return (
            <div className="text-center text-gray-500 py-8">
                No processed data available. Run data processing first.
            </div>
        );
    }

    const variables = Object.keys(data.variables || {});

    return (
        <div className="space-y-4">
            {/* FDV Chart Section */}
            <div className="bg-gray-50 rounded-lg overflow-hidden">
                <button
                    onClick={() => setShowFdv(!showFdv)}
                    className="w-full p-3 flex items-center justify-between text-left hover:bg-gray-100"
                >
                    <span className="font-semibold text-gray-700">Flow, Depth & Velocity</span>
                    {showFdv ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                </button>

                {showFdv && (
                    <div className="p-4 pt-0 space-y-2">
                        {/* Flow */}
                        {variables.includes('Flow') && (
                            <div>
                                <h5 className="text-xs font-medium text-blue-600 mb-1">Flow (L/s)</h5>
                                <ResponsiveContainer width="100%" height={120}>
                                    <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                        <XAxis dataKey="time" type="number" domain={['dataMin', 'dataMax']} tick={false} />
                                        <YAxis tick={{ fontSize: 9 }} width={50} />
                                        <Tooltip labelFormatter={(val) => new Date(val).toLocaleString()} contentStyle={{ fontSize: 11 }} />
                                        <Line type="monotone" dataKey="Flow" stroke={COLORS.flow} dot={false} strokeWidth={1} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        )}

                        {/* Depth with Soffit */}
                        {variables.includes('Depth') && (
                            <div>
                                <h5 className="text-xs font-medium text-red-600 mb-1">Depth (mm) - Soffit: {pipeHeight}mm</h5>
                                <ResponsiveContainer width="100%" height={120}>
                                    <ComposedChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 0 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                        <XAxis dataKey="time" type="number" domain={['dataMin', 'dataMax']} tick={false} />
                                        <YAxis tick={{ fontSize: 9 }} width={50} domain={[0, Math.max(pipeHeight * 1.1, (stats as any).depthMax * 1.1)]} />
                                        <Tooltip labelFormatter={(val) => new Date(val).toLocaleString()} contentStyle={{ fontSize: 11 }} />
                                        <Line type="monotone" dataKey="Depth" stroke={COLORS.depth} dot={false} strokeWidth={1} />
                                        {/* Soffit reference line */}
                                        <Line
                                            type="monotone"
                                            dataKey={() => pipeHeight}
                                            stroke={COLORS.soffit}
                                            strokeDasharray="5 5"
                                            dot={false}
                                            strokeWidth={2}
                                            name="Soffit"
                                        />
                                    </ComposedChart>
                                </ResponsiveContainer>
                            </div>
                        )}

                        {/* Velocity */}
                        {variables.includes('Velocity') && (
                            <div>
                                <h5 className="text-xs font-medium text-green-600 mb-1">Velocity (m/s)</h5>
                                <ResponsiveContainer width="100%" height={120}>
                                    <LineChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                        <XAxis dataKey="time" type="number" domain={['dataMin', 'dataMax']} tickFormatter={formatDate} tick={{ fontSize: 9 }} />
                                        <YAxis tick={{ fontSize: 9 }} width={50} />
                                        <Tooltip labelFormatter={(val) => new Date(val).toLocaleString()} contentStyle={{ fontSize: 11 }} />
                                        <Line type="monotone" dataKey="Velocity" stroke={COLORS.velocity} dot={false} strokeWidth={1} />
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* DWF Chart Section */}
            <div className="bg-gray-50 rounded-lg overflow-hidden">
                <button
                    onClick={() => setShowDwf(!showDwf)}
                    className="w-full p-3 flex items-center justify-between text-left hover:bg-gray-100"
                >
                    <span className="font-semibold text-gray-700">Dry Weather Flow Profile</span>
                    {showDwf ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                </button>

                {showDwf && dwfData.length > 0 && (
                    <div className="p-4 pt-0">
                        <p className="text-xs text-gray-500 mb-2">Average values by time of day across all days</p>
                        <ResponsiveContainer width="100%" height={200}>
                            <LineChart data={dwfData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                                <XAxis dataKey="timeOfDay" tickFormatter={formatTime} tick={{ fontSize: 9 }} />
                                <YAxis tick={{ fontSize: 9 }} width={50} />
                                <Tooltip labelFormatter={formatTime} contentStyle={{ fontSize: 11 }} />
                                <Legend wrapperStyle={{ fontSize: 10 }} />
                                {variables.includes('Flow') && <Line type="monotone" dataKey="Flow" stroke={COLORS.flow} dot={false} strokeWidth={1.5} />}
                                {variables.includes('Depth') && <Line type="monotone" dataKey="Depth" stroke={COLORS.depth} dot={false} strokeWidth={1.5} />}
                                {variables.includes('Velocity') && <Line type="monotone" dataKey="Velocity" stroke={COLORS.velocity} dot={false} strokeWidth={1.5} />}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>

            {/* Statistics */}
            <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Data Summary</h4>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                    <div>
                        <p className="text-gray-500 text-xs">Data Points</p>
                        <p className="font-semibold">{(stats as any).dataPoints?.toLocaleString()}</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Max Flow</p>
                        <p className="font-semibold text-blue-600">{(stats as any).flowMax?.toFixed(1)} L/s</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Avg Flow</p>
                        <p className="font-semibold text-blue-600">{(stats as any).flowAvg?.toFixed(1)} L/s</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Max Depth</p>
                        <p className="font-semibold text-red-600">{(stats as any).depthMax?.toFixed(0)} mm</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Avg Depth</p>
                        <p className="font-semibold text-red-600">{(stats as any).depthAvg?.toFixed(0)} mm</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default FlowMonitorChart;
