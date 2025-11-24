import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Brush } from 'recharts';
import { Loader2 } from 'lucide-react';
import { useFDVTimeseries } from '../../api/hooks';


interface FDVChartProps {
    datasetId: number;
}

const FDVChart: React.FC<FDVChartProps> = ({ datasetId }) => {
    const { data: response, isLoading, error } = useFDVTimeseries(datasetId);

    // State for zoom range
    const [zoomRange, setZoomRange] = React.useState<{ startIndex: number; endIndex: number } | null>(null);

    // Smart Downsampling: Preserves peaks and troughs for all series
    const downsampledData = React.useMemo(() => {
        if (!response?.data || response.data.length <= 2000) return response?.data || [];

        const data = response.data;
        // Target roughly 1000 "chunks", but we might pick multiple points per chunk
        const chunkSize = Math.ceil(data.length / 500);
        const sampled: any[] = [];

        for (let i = 0; i < data.length; i += chunkSize) {
            const chunk = data.slice(i, Math.min(i + chunkSize, data.length));
            if (chunk.length === 0) continue;

            // Always include the first point of the chunk
            const indices = new Set<number>([0, chunk.length - 1]);

            // Find indices of min/max for each variable
            let minFlow = chunk[0].flow, maxFlow = chunk[0].flow;
            let minDepth = chunk[0].depth, maxDepth = chunk[0].depth;
            let minVel = chunk[0].velocity, maxVel = chunk[0].velocity;

            let minFlowIdx = 0, maxFlowIdx = 0;
            let minDepthIdx = 0, maxDepthIdx = 0;
            let minVelIdx = 0, maxVelIdx = 0;

            chunk.forEach((d: any, idx: number) => {
                if (d.flow < minFlow) { minFlow = d.flow; minFlowIdx = idx; }
                if (d.flow > maxFlow) { maxFlow = d.flow; maxFlowIdx = idx; }

                if (d.depth < minDepth) { minDepth = d.depth; minDepthIdx = idx; }
                if (d.depth > maxDepth) { maxDepth = d.depth; maxDepthIdx = idx; }

                if (d.velocity < minVel) { minVel = d.velocity; minVelIdx = idx; }
                if (d.velocity > maxVel) { maxVel = d.velocity; maxVelIdx = idx; }
            });

            // Add key points
            indices.add(minFlowIdx); indices.add(maxFlowIdx);
            indices.add(minDepthIdx); indices.add(maxDepthIdx);
            indices.add(minVelIdx); indices.add(maxVelIdx);

            // Sort indices and add to sampled data
            Array.from(indices).sort((a, b) => a - b).forEach(idx => {
                sampled.push(chunk[idx]);
            });
        }
        return sampled;
    }, [response]);

    // Calculate statistics based on current zoom range
    const stats = React.useMemo(() => {
        if (!response?.data) return null;

        // Use downsampled data for stats if zoomed, otherwise full data
        // Note: Ideally we'd filter the full data by time range, but for responsiveness 
        // using the downsampled data visible in the view is a good approximation for the user
        let dataToAnalyze = downsampledData;

        if (zoomRange) {
            dataToAnalyze = downsampledData.slice(zoomRange.startIndex, zoomRange.endIndex + 1);
        }

        if (dataToAnalyze.length === 0) return null;

        return {
            flow: {
                max: Math.max(...dataToAnalyze.map((d: any) => d.flow)),
                min: Math.min(...dataToAnalyze.map((d: any) => d.flow)),
                mean: dataToAnalyze.reduce((sum: number, d: any) => sum + d.flow, 0) / dataToAnalyze.length
            },
            depth: {
                max: Math.max(...dataToAnalyze.map((d: any) => d.depth)),
                min: Math.min(...dataToAnalyze.map((d: any) => d.depth)),
                mean: dataToAnalyze.reduce((sum: number, d: any) => sum + d.depth, 0) / dataToAnalyze.length
            },
            velocity: {
                max: Math.max(...dataToAnalyze.map((d: any) => d.velocity)),
                min: Math.min(...dataToAnalyze.map((d: any) => d.velocity)),
                mean: dataToAnalyze.reduce((sum: number, d: any) => sum + d.velocity, 0) / dataToAnalyze.length
            }
        };
    }, [response, downsampledData, zoomRange]);

    // Format time for display
    const formattedData = React.useMemo(() => {
        return downsampledData.map((d: any) => ({
            ...d,
            time: new Date(d.time).toLocaleString('en-GB', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            })
        }));
    }, [downsampledData]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="animate-spin text-purple-500" size={32} />
            </div>
        );
    }

    if (error || !response?.data) {
        return (
            <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-lg">
                Error loading time-series data.
            </div>
        );
    }

    const StatBox: React.FC<{ title: string; stats: { max: number; min: number; mean: number }; unit: string }> = ({ title, stats, unit }) => (
        <div className="absolute top-2 right-2 bg-white bg-opacity-90 border border-gray-200 text-gray-700 text-xs p-2 rounded shadow-sm z-10">
            <div className="font-semibold mb-1 text-gray-900">{title}</div>
            <div>Max: {stats.max.toFixed(3)} {unit}</div>
            <div>Min: {stats.min.toFixed(3)} {unit}</div>
            <div>Mean: {stats.mean.toFixed(4)} {unit}</div>
        </div>
    );

    return (
        <div className="space-y-2">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Flow, Depth, Velocity Time Series</h3>

            {/* Depth Chart (Top) */}
            <div className="relative bg-white border border-gray-200 rounded-t-lg p-4 pb-0">
                {stats && <StatBox title="Depth" stats={stats.depth} unit="mm" />}
                <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={formattedData} syncId="fdv" margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                            dataKey="time"
                            tick={false}
                            height={0}
                            axisLine={false}
                        />
                        <YAxis
                            label={{ value: 'Depth (mm)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                            tick={{ fontSize: 10 }}
                        />
                        <Tooltip
                            contentStyle={{ fontSize: 12 }}
                            labelStyle={{ fontWeight: 'bold' }}
                        />
                        <Line
                            type="monotone"
                            dataKey="depth"
                            stroke="#cd5c5c"
                            strokeWidth={1.5}
                            dot={false}
                            name="Depth"
                            isAnimationActive={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Flow Chart (Middle) */}
            <div className="relative bg-white border-x border-gray-200 p-4 pb-0 -mt-px">
                {stats && <StatBox title="Flow" stats={stats.flow} unit="L/s" />}
                <ResponsiveContainer width="100%" height={200}>
                    <LineChart data={formattedData} syncId="fdv" margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                            dataKey="time"
                            tick={false}
                            height={0}
                            axisLine={false}
                        />
                        <YAxis
                            label={{ value: 'Flow (L/s)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                            tick={{ fontSize: 10 }}
                        />
                        <Tooltip
                            contentStyle={{ fontSize: 12 }}
                            labelStyle={{ fontWeight: 'bold' }}
                        />
                        <Line
                            type="monotone"
                            dataKey="flow"
                            stroke="#4682b4"
                            strokeWidth={1.5}
                            dot={false}
                            name="Flow"
                            isAnimationActive={false}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Velocity Chart (Bottom) */}
            <div className="relative bg-white border border-gray-200 rounded-b-lg p-4 -mt-px">
                {stats && <StatBox title="Velocity" stats={stats.velocity} unit="m/s" />}
                <ResponsiveContainer width="100%" height={260}>
                    <LineChart data={formattedData} syncId="fdv" margin={{ top: 10, right: 30, left: 0, bottom: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                            dataKey="time"
                            tick={{ fontSize: 10 }}
                            angle={-45}
                            textAnchor="end"
                            height={60}
                        />
                        <YAxis
                            label={{ value: 'Velocity (m/s)', angle: -90, position: 'insideLeft', style: { fontSize: 12 } }}
                            tick={{ fontSize: 10 }}
                        />
                        <Tooltip
                            contentStyle={{ fontSize: 12 }}
                            labelStyle={{ fontWeight: 'bold' }}
                        />
                        <Line
                            type="monotone"
                            dataKey="velocity"
                            stroke="#3cb371"
                            strokeWidth={1.5}
                            dot={false}
                            name="Velocity"
                            isAnimationActive={false}
                        />
                        <Brush
                            dataKey="time"
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
        </div>
    );
};

export default FDVChart;
