import React, { useMemo } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, AreaChart, Area
} from 'recharts';
import { Loader2 } from 'lucide-react';
import { useInstallTimeseries } from '../../../api/hooks';

interface PumpLoggerChartProps {
    installId: number;
    startDate?: string;
    endDate?: string;
}

const COLORS = {
    on: '#22C55E',    // green
    off: '#E5E7EB',   // gray
};

const PumpLoggerChart: React.FC<PumpLoggerChartProps> = ({ installId, startDate, endDate }) => {
    const { data, isLoading, error } = useInstallTimeseries(
        installId,
        'Processed',
        startDate,
        endDate,
        10000
    );

    const { chartData, stats } = useMemo(() => {
        if (!data?.variables) return { chartData: [], stats: {} };

        const timeMap = new Map<number, any>();

        // Find pump state variable
        const pumpKey = Object.keys(data.variables).find(k =>
            k.toLowerCase().includes('pump') ||
            k.toLowerCase().includes('state') ||
            k.toLowerCase().includes('flow')
        );

        if (!pumpKey) return { chartData: [], stats: {} };

        const varData = data.variables[pumpKey] as any;
        let lastState = 0;
        let onCount = 0;
        let offCount = 0;
        let totalOnTime = 0;
        let lastOnTime: number | null = null;

        varData.data?.forEach((point: { time: string; value: number }, idx: number) => {
            const ts = new Date(point.time).getTime();
            const state = point.value > 0 ? 1 : 0;

            // Track state changes
            if (idx > 0 && state !== lastState) {
                if (state === 1) {
                    onCount++;
                    lastOnTime = ts;
                } else {
                    offCount++;
                    if (lastOnTime !== null) {
                        totalOnTime += (ts - lastOnTime) / 1000; // seconds
                        lastOnTime = null;
                    }
                }
            }

            timeMap.set(ts, {
                time: ts,
                state,
            });

            lastState = state;
        });

        const sortedData = Array.from(timeMap.values()).sort((a, b) => a.time - b.time);

        // Calculate duration stats
        const totalPeriod = sortedData.length > 1
            ? (sortedData[sortedData.length - 1].time - sortedData[0].time) / 1000
            : 0;
        const dutyCycle = totalPeriod > 0 ? (totalOnTime / totalPeriod) * 100 : 0;

        return {
            chartData: sortedData,
            stats: {
                dataPoints: sortedData.length,
                onCount,
                offCount,
                totalOnTime: totalOnTime / 3600, // hours
                dutyCycle,
            }
        };
    }, [data]);

    const formatDate = (timestamp: number) => {
        return new Date(timestamp).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
    };

    const formatDateTime = (timestamp: number) => {
        return new Date(timestamp).toLocaleString('en-GB', {
            day: '2-digit',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit'
        });
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

    return (
        <div className="space-y-4">
            {/* Pump State Chart */}
            <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-semibold text-gray-700 mb-3">Pump On/Off State</h4>

                <ResponsiveContainer width="100%" height={200}>
                    <AreaChart data={chartData} margin={{ top: 10, right: 20, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                        <XAxis
                            dataKey="time"
                            type="number"
                            domain={['dataMin', 'dataMax']}
                            tickFormatter={formatDate}
                            tick={{ fontSize: 9 }}
                        />
                        <YAxis
                            tick={{ fontSize: 9 }}
                            width={40}
                            domain={[0, 1.2]}
                            ticks={[0, 1]}
                            tickFormatter={(val) => val === 1 ? 'ON' : 'OFF'}
                        />
                        <Tooltip
                            labelFormatter={formatDateTime}
                            contentStyle={{ fontSize: 11 }}
                            formatter={(value: number) => [value === 1 ? 'ON' : 'OFF', 'Status']}
                        />

                        <Area
                            type="stepAfter"
                            dataKey="state"
                            stroke={COLORS.on}
                            fill={COLORS.on}
                            fillOpacity={0.6}
                            strokeWidth={2}
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </div>

            {/* Run Events Table */}
            <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="font-semibold text-gray-700 mb-3">Pump Run Events</h4>
                <PumpRunsTable data={chartData} />
            </div>

            {/* Statistics */}
            <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Pump Statistics</h4>
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                    <div>
                        <p className="text-gray-500 text-xs">Data Points</p>
                        <p className="font-semibold">{(stats as any).dataPoints?.toLocaleString()}</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Start Events</p>
                        <p className="font-semibold text-green-600">{(stats as any).onCount}</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Stop Events</p>
                        <p className="font-semibold text-gray-600">{(stats as any).offCount}</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Total Run Time</p>
                        <p className="font-semibold">{(stats as any).totalOnTime?.toFixed(1)} hrs</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Duty Cycle</p>
                        <p className="font-semibold">{(stats as any).dutyCycle?.toFixed(1)}%</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Helper component for pump runs table
const PumpRunsTable: React.FC<{ data: any[] }> = ({ data }) => {
    const runs = useMemo(() => {
        const events: { start: number; end: number | null; duration: number }[] = [];
        let runStart: number | null = null;

        data.forEach((point, idx) => {
            const prevState = idx > 0 ? data[idx - 1].state : 0;

            if (point.state === 1 && prevState === 0) {
                // Pump turned on
                runStart = point.time;
            } else if (point.state === 0 && prevState === 1 && runStart !== null) {
                // Pump turned off
                events.push({
                    start: runStart,
                    end: point.time,
                    duration: (point.time - runStart) / 1000 / 60, // minutes
                });
                runStart = null;
            }
        });

        // If pump is still running at end
        if (runStart !== null && data.length > 0) {
            const lastTime = data[data.length - 1].time;
            events.push({
                start: runStart,
                end: null,
                duration: (lastTime - runStart) / 1000 / 60,
            });
        }

        return events;
    }, [data]);

    if (runs.length === 0) {
        return <p className="text-gray-400 text-sm text-center py-4">No pump runs detected</p>;
    }

    const formatTime = (ts: number) => new Date(ts).toLocaleString('en-GB', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
    });

    return (
        <div className="max-h-48 overflow-y-auto">
            <table className="w-full text-sm">
                <thead className="bg-gray-100 sticky top-0">
                    <tr>
                        <th className="text-left p-2 font-medium text-gray-600">Start</th>
                        <th className="text-left p-2 font-medium text-gray-600">End</th>
                        <th className="text-right p-2 font-medium text-gray-600">Duration</th>
                    </tr>
                </thead>
                <tbody>
                    {runs.slice(-20).reverse().map((run, idx) => (
                        <tr key={idx} className="border-t border-gray-100">
                            <td className="p-2">{formatTime(run.start)}</td>
                            <td className="p-2">{run.end ? formatTime(run.end) : <span className="text-green-600">Running...</span>}</td>
                            <td className="p-2 text-right font-medium">
                                {run.duration < 60
                                    ? `${run.duration.toFixed(0)} min`
                                    : `${(run.duration / 60).toFixed(1)} hrs`
                                }
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
            {runs.length > 20 && (
                <p className="text-xs text-gray-400 text-center mt-2">Showing last 20 of {runs.length} runs</p>
            )}
        </div>
    );
};

export default PumpLoggerChart;
