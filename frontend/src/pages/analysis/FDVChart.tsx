import React, { useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Brush, Legend } from 'recharts';
import { Loader2 } from 'lucide-react';
import { useQueries } from '@tanstack/react-query';
import api from '../../api/client';

interface FDVChartProps {
    datasets: { id: number; name: string; variable: string }[];
}

const COLORS = ['#8884d8', '#82ca9d', '#ffc658', '#ff7300', '#0088fe', '#00C49F', '#FFBB28', '#FF8042'];

const FDVChart: React.FC<FDVChartProps> = ({ datasets }) => {
    // Fetch data for all datasets
    const queries = useQueries({
        queries: datasets.map(dataset => ({
            queryKey: ['fdv_timeseries', dataset.id],
            queryFn: async () => {
                const { data } = await api.get<any>(`/fsa/fdv/${dataset.id}/timeseries`);
                return { ...data, datasetId: dataset.id, variable: dataset.variable, name: dataset.name };
            },
            enabled: !!dataset.id,
        }))
    });

    const isLoading = queries.some(q => q.isLoading);
    const error = queries.find(q => q.error);

    // State for zoom range
    const [zoomRange, setZoomRange] = React.useState<{ startIndex: number; endIndex: number } | null>(null);

    // Merge and process data with smart downsampling
    const { mergedData, seriesInfo } = useMemo(() => {
        if (isLoading) return { mergedData: [], seriesInfo: [] };

        const successfulQueries = queries.filter(q => q.isSuccess && q.data);
        if (successfulQueries.length === 0) return { mergedData: [], seriesInfo: [] };

        const timeMap = new Map<string, any>();
        const info: any[] = [];

        // First pass: merge all data onto common timeline (no downsampling yet)
        successfulQueries.forEach((query, index) => {
            if (!query.data?.data) return;

            const { data, datasetId, variable, name } = query.data;
            const color = COLORS[index % COLORS.length];

            info.push({ id: datasetId, name, variable, color });

            // Helper to add value to time map
            const addValue = (time: string, key: string, val: number) => {
                if (!timeMap.has(time)) {
                    timeMap.set(time, { time: new Date(time).getTime(), rawTime: time });
                }
                const entry = timeMap.get(time);
                entry[key] = val;
            };

            const records = data || [];
            records.forEach((record: any) => {
                if (variable === 'Rainfall') {
                    addValue(record.time, `rain_${datasetId}`, record.rainfall);
                } else {
                    addValue(record.time, `flow_${datasetId}`, record.flow);
                    addValue(record.time, `depth_${datasetId}`, record.depth);
                    addValue(record.time, `velocity_${datasetId}`, record.velocity);
                }
            });
        });

        // Sort the merged data
        const sortedData = Array.from(timeMap.values()).sort((a, b) => a.time - b.time);

        // Second pass: downsample the merged timeline
        let downsampledData = sortedData;
        if (sortedData.length > 2000) {
            const chunkSize = Math.ceil(sortedData.length / 500);
            const sampled: any[] = [];

            for (let i = 0; i < sortedData.length; i += chunkSize) {
                const chunk = sortedData.slice(i, Math.min(i + chunkSize, sortedData.length));
                if (chunk.length === 0) continue;

                // Always include first and last points of chunk
                const indices = new Set<number>([0, chunk.length - 1]);

                // Find min/max for each series in this chunk
                info.forEach(series => {
                    if (series.variable === 'Rainfall') {
                        const key = `rain_${series.id}`;
                        let minVal = chunk[0][key] ?? 0;
                        let maxVal = chunk[0][key] ?? 0;
                        let minIdx = 0;
                        let maxIdx = 0;

                        chunk.forEach((record: any, idx: number) => {
                            const val = record[key] ?? 0;
                            if (val < minVal) { minVal = val; minIdx = idx; }
                            if (val > maxVal) { maxVal = val; maxIdx = idx; }
                        });

                        indices.add(minIdx);
                        indices.add(maxIdx);
                    } else {
                        // For flow monitors, check flow, depth, and velocity
                        ['flow', 'depth', 'velocity'].forEach(metric => {
                            const key = `${metric}_${series.id}`;
                            let minVal = chunk[0][key] ?? 0;
                            let maxVal = chunk[0][key] ?? 0;
                            let minIdx = 0;
                            let maxIdx = 0;

                            chunk.forEach((record: any, idx: number) => {
                                const val = record[key] ?? 0;
                                if (val < minVal) { minVal = val; minIdx = idx; }
                                if (val > maxVal) { maxVal = val; maxIdx = idx; }
                            });

                            indices.add(minIdx);
                            indices.add(maxIdx);
                        });
                    }
                });

                // Add selected points to sampled data
                Array.from(indices).sort((a, b) => a - b).forEach(idx => {
                    sampled.push(chunk[idx]);
                });
            }

            downsampledData = sampled;
        }

        // Format time for display
        const formatted = downsampledData.map(d => ({
            ...d,
            displayTime: new Date(d.rawTime).toLocaleString('en-GB', {
                day: '2-digit', month: '2-digit', year: 'numeric',
                hour: '2-digit', minute: '2-digit'
            })
        }));

        return { mergedData: formatted, seriesInfo: info };
    }, [datasets.map(d => d.id).join('-'), isLoading, queries.filter(q => q.isSuccess).length]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="animate-spin text-purple-500" size={32} />
            </div>
        );
    }

    if (error) {
        return (
            <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-lg">
                Error loading time-series data.
            </div>
        );
    }

    if (mergedData.length === 0) {
        return <div className="text-center text-gray-500 p-8">No data available for selected datasets.</div>;
    }

    const hasRainfall = seriesInfo.some(s => s.variable === 'Rainfall');
    const flowSeries = seriesInfo.filter(s => s.variable !== 'Rainfall');
    const hasFlowData = flowSeries.length > 0;

    return (
        <div className="space-y-2">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Time Series Analysis</h3>

            {/* Rainfall Chart - show at top if mixed, or as only chart if rainfall-only */}
            {hasRainfall && (
                <div className={`relative bg-white border border-gray-200 ${hasFlowData ? 'rounded-t-lg' : 'rounded-lg'} p-4 ${hasFlowData ? 'pb-0' : ''}`}>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Rainfall Intensity</h4>
                    <ResponsiveContainer width="100%" height={hasFlowData ? 150 : 400}>
                        <LineChart data={mergedData} syncId="fdv" margin={{ top: 10, right: 30, left: 0, bottom: hasFlowData ? 0 : 60 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                            <XAxis
                                dataKey="displayTime"
                                tick={hasFlowData ? false : { fontSize: 10 }}
                                height={hasFlowData ? 0 : 60}
                                axisLine={!hasFlowData}
                                angle={hasFlowData ? 0 : -45}
                                textAnchor={hasFlowData ? "middle" : "end"}
                            />
                            <YAxis label={{ value: 'mm/hr', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }} tick={{ fontSize: 10 }} reversed />
                            <Tooltip contentStyle={{ fontSize: 12 }} labelStyle={{ fontWeight: 'bold' }} />
                            <Legend />
                            {seriesInfo.filter(s => s.variable === 'Rainfall').map(s => (
                                <Line
                                    key={s.id}
                                    type="step"
                                    dataKey={`rain_${s.id}`}
                                    stroke={s.color}
                                    strokeWidth={1.5}
                                    dot={false}
                                    name={s.name}
                                    isAnimationActive={false}
                                />
                            ))}
                            {!hasFlowData && (
                                <Brush
                                    dataKey="displayTime"
                                    height={30}
                                    stroke="#8884d8"
                                    tickFormatter={() => ""}
                                />
                            )}
                        </LineChart>
                    </ResponsiveContainer>
                </div>
            )}

            {/* Only show flow/depth/velocity charts if we have flow data */}
            {hasFlowData && (
                <>
                    {/* Depth Chart */}
                    <div className={`relative bg-white border border-gray-200 ${hasRainfall ? 'border-t-0' : 'rounded-t-lg'} p-4 pb-0`}>
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Depth</h4>
                        <ResponsiveContainer width="100%" height={200}>
                            <LineChart data={mergedData} syncId="fdv" margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                <XAxis dataKey="displayTime" tick={false} height={0} axisLine={false} />
                                <YAxis label={{ value: 'mm', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }} tick={{ fontSize: 10 }} />
                                <Tooltip contentStyle={{ fontSize: 12 }} labelStyle={{ fontWeight: 'bold' }} />
                                <Legend />
                                {flowSeries.map(s => (
                                    <Line
                                        key={s.id}
                                        type="monotone"
                                        dataKey={`depth_${s.id}`}
                                        stroke={s.color}
                                        strokeWidth={1.5}
                                        dot={false}
                                        name={s.name}
                                        isAnimationActive={false}
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Flow Chart */}
                    <div className="relative bg-white border-x border-gray-200 p-4 pb-0 -mt-px">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Flow</h4>
                        <ResponsiveContainer width="100%" height={200}>
                            <LineChart data={mergedData} syncId="fdv" margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                <XAxis dataKey="displayTime" tick={false} height={0} axisLine={false} />
                                <YAxis label={{ value: 'L/s', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }} tick={{ fontSize: 10 }} />
                                <Tooltip contentStyle={{ fontSize: 12 }} labelStyle={{ fontWeight: 'bold' }} />
                                <Legend />
                                {flowSeries.map(s => (
                                    <Line
                                        key={s.id}
                                        type="monotone"
                                        dataKey={`flow_${s.id}`}
                                        stroke={s.color}
                                        strokeWidth={1.5}
                                        dot={false}
                                        name={s.name}
                                        isAnimationActive={false}
                                    />
                                ))}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Velocity Chart */}
                    <div className="relative bg-white border border-gray-200 rounded-b-lg p-4 -mt-px">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Velocity</h4>
                        <ResponsiveContainer width="100%" height={260}>
                            <LineChart data={mergedData} syncId="fdv" margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                                <XAxis dataKey="displayTime" tick={{ fontSize: 10 }} angle={-45} textAnchor="end" height={60} />
                                <YAxis label={{ value: 'm/s', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }} tick={{ fontSize: 10 }} />
                                <Tooltip contentStyle={{ fontSize: 12 }} labelStyle={{ fontWeight: 'bold' }} />
                                <Legend />
                                {flowSeries.map(s => (
                                    <Line
                                        key={s.id}
                                        type="monotone"
                                        dataKey={`velocity_${s.id}`}
                                        stroke={s.color}
                                        strokeWidth={1.5}
                                        dot={false}
                                        name={s.name}
                                        isAnimationActive={false}
                                    />
                                ))}
                                <Brush
                                    dataKey="displayTime"
                                    height={30}
                                    stroke="#8884d8"
                                    tickFormatter={() => ""}
                                    onChange={(e: any) => {
                                        if (e && e.startIndex !== undefined && e.endIndex !== undefined) {
                                            setZoomRange({ startIndex: e.startIndex, endIndex: e.endIndex });
                                        }
                                    }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </>
            )}
        </div>
    );
};

export default FDVChart;
