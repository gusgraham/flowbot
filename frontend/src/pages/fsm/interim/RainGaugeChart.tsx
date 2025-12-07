import React, { useMemo, useState } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
    Legend, ResponsiveContainer, BarChart, Bar, ComposedChart, Area
} from 'recharts';
import { Loader2, ChevronDown, ChevronRight } from 'lucide-react';
import { useInstallTimeseries } from '../../../api/hooks';

interface RainGaugeChartProps {
    installId: number;
    startDate?: string;
    endDate?: string;
}

const COLORS = {
    intensity: '#0EA5E9',     // cyan
    cumulative: '#3B82F6',    // blue
};

const RainGaugeChart: React.FC<RainGaugeChartProps> = ({ installId, startDate, endDate }) => {
    const [showCumulative, setShowCumulative] = useState(true);

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
        let cumulativeRain = 0;

        // Find rain variable (could be Rain, Intensity, IntensityData)
        const rainKey = Object.keys(data.variables).find(k =>
            k.toLowerCase().includes('rain') || k.toLowerCase().includes('intensity')
        );

        if (!rainKey) return { chartData: [], stats: {} };

        const varData = data.variables[rainKey] as any;
        varData.data?.forEach((point: { time: string; value: number }) => {
            const ts = new Date(point.time).getTime();
            cumulativeRain += point.value * (15 / 60); // Assuming 15-min intervals, convert to depth

            timeMap.set(ts, {
                time: ts,
                intensity: point.value,
                cumulative: cumulativeRain,
            });
        });

        const sortedData = Array.from(timeMap.values()).sort((a, b) => a.time - b.time);

        // Calculate stats
        const intensityVals = sortedData.map(d => d.intensity);
        const maxIntensity = intensityVals.length > 0 ? Math.max(...intensityVals) : 0;
        const totalRainfall = sortedData.length > 0 ? sortedData[sortedData.length - 1].cumulative : 0;
        const rainyHours = intensityVals.filter(v => v > 0).length * 0.25; // Assuming 15-min intervals

        return {
            chartData: sortedData,
            stats: {
                dataPoints: sortedData.length,
                maxIntensity,
                totalRainfall,
                rainyHours,
            }
        };
    }, [data]);

    const formatDate = (timestamp: number) => {
        return new Date(timestamp).toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
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
            {/* Intensity Chart with optional Cumulative */}
            <div className="bg-gray-50 rounded-lg p-4">
                <div className="flex justify-between items-center mb-3">
                    <h4 className="font-semibold text-gray-700">Rainfall Intensity</h4>
                    <label className="flex items-center gap-2 text-sm text-gray-600">
                        <input
                            type="checkbox"
                            checked={showCumulative}
                            onChange={(e) => setShowCumulative(e.target.checked)}
                            className="rounded border-gray-300"
                        />
                        Show Cumulative
                    </label>
                </div>

                <ResponsiveContainer width="100%" height={showCumulative ? 300 : 200}>
                    <ComposedChart data={chartData} margin={{ top: 10, right: 40, left: 0, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#E5E7EB" />
                        <XAxis
                            dataKey="time"
                            type="number"
                            domain={['dataMin', 'dataMax']}
                            tickFormatter={formatDate}
                            tick={{ fontSize: 9 }}
                        />
                        <YAxis
                            yAxisId="left"
                            tick={{ fontSize: 9 }}
                            width={50}
                            label={{ value: 'mm/hr', angle: -90, position: 'insideLeft', fontSize: 10 }}
                        />
                        {showCumulative && (
                            <YAxis
                                yAxisId="right"
                                orientation="right"
                                tick={{ fontSize: 9 }}
                                width={50}
                                label={{ value: 'mm', angle: 90, position: 'insideRight', fontSize: 10 }}
                            />
                        )}
                        <Tooltip
                            labelFormatter={(val) => new Date(val).toLocaleString()}
                            contentStyle={{ fontSize: 11 }}
                            formatter={(value: number, name: string) => [
                                name === 'intensity' ? `${value.toFixed(2)} mm/hr` : `${value.toFixed(1)} mm`,
                                name === 'intensity' ? 'Intensity' : 'Cumulative'
                            ]}
                        />
                        <Legend wrapperStyle={{ fontSize: 10 }} />

                        <Bar
                            yAxisId="left"
                            dataKey="intensity"
                            fill={COLORS.intensity}
                            opacity={0.8}
                            name="Intensity (mm/hr)"
                        />

                        {showCumulative && (
                            <Line
                                yAxisId="right"
                                type="monotone"
                                dataKey="cumulative"
                                stroke={COLORS.cumulative}
                                dot={false}
                                strokeWidth={2}
                                name="Cumulative (mm)"
                            />
                        )}
                    </ComposedChart>
                </ResponsiveContainer>
            </div>

            {/* Daily Totals */}
            <div className="bg-gray-50 rounded-lg overflow-hidden">
                <button
                    className="w-full p-3 flex items-center justify-between text-left hover:bg-gray-100"
                >
                    <span className="font-semibold text-gray-700">Daily Rainfall Summary</span>
                </button>
                <div className="p-4 pt-0">
                    <DailyRainfallTable data={chartData} />
                </div>
            </div>

            {/* Statistics */}
            <div className="bg-gray-50 rounded-lg p-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Rainfall Summary</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                        <p className="text-gray-500 text-xs">Data Points</p>
                        <p className="font-semibold">{(stats as any).dataPoints?.toLocaleString()}</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Max Intensity</p>
                        <p className="font-semibold text-cyan-600">{(stats as any).maxIntensity?.toFixed(1)} mm/hr</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Total Rainfall</p>
                        <p className="font-semibold text-blue-600">{(stats as any).totalRainfall?.toFixed(1)} mm</p>
                    </div>
                    <div>
                        <p className="text-gray-500 text-xs">Rainy Hours</p>
                        <p className="font-semibold">{(stats as any).rainyHours?.toFixed(1)} hrs</p>
                    </div>
                </div>
            </div>
        </div>
    );
};

// Helper component for daily totals table
const DailyRainfallTable: React.FC<{ data: any[] }> = ({ data }) => {
    const dailyTotals = useMemo(() => {
        const dayMap = new Map<string, { total: number; max: number; count: number }>();

        data.forEach(point => {
            const date = new Date(point.time).toLocaleDateString('en-GB');
            if (!dayMap.has(date)) {
                dayMap.set(date, { total: 0, max: 0, count: 0 });
            }
            const day = dayMap.get(date)!;
            day.total += point.intensity * 0.25; // 15-min to depth
            day.max = Math.max(day.max, point.intensity);
            day.count++;
        });

        return Array.from(dayMap.entries()).map(([date, vals]) => ({
            date,
            ...vals,
        }));
    }, [data]);

    if (dailyTotals.length === 0) return null;

    return (
        <div className="max-h-48 overflow-y-auto">
            <table className="w-full text-sm">
                <thead className="bg-gray-100 sticky top-0">
                    <tr>
                        <th className="text-left p-2 font-medium text-gray-600">Date</th>
                        <th className="text-right p-2 font-medium text-gray-600">Total (mm)</th>
                        <th className="text-right p-2 font-medium text-gray-600">Max (mm/hr)</th>
                    </tr>
                </thead>
                <tbody>
                    {dailyTotals.map((day) => (
                        <tr key={day.date} className="border-t border-gray-100">
                            <td className="p-2">{day.date}</td>
                            <td className="p-2 text-right font-medium text-blue-600">{day.total.toFixed(1)}</td>
                            <td className="p-2 text-right">{day.max.toFixed(1)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
};

export default RainGaugeChart;
