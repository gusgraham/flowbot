import React, { useMemo, useState, useEffect } from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    ResponsiveContainer,
    Cell
} from 'recharts';
import { format } from 'date-fns';
import { ZoomIn, ZoomOut, RotateCcw, ChevronLeft, ChevronRight } from 'lucide-react';

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

interface RainfallEventsGanttProps {
    events: EventResult[];
}

const RainfallEventsGantt: React.FC<RainfallEventsGanttProps> = ({ events }) => {
    const processedData = useMemo(() => {
        if (!events || events.length === 0) return { chartData: [], maxSegments: 0, minTime: 0, maxTime: 0 };

        // 1. Find global time range
        const timestamps = events.flatMap(e => [new Date(e.start_time).getTime(), new Date(e.end_time).getTime()]);
        const minTime = Math.min(...timestamps);
        const maxTime = Math.max(...timestamps);

        // 2. Group by dataset
        const grouped: Record<string, EventResult[]> = {};
        events.forEach(e => {
            if (!grouped[e.dataset_name]) grouped[e.dataset_name] = [];
            grouped[e.dataset_name].push(e);
        });

        // 3. Transform to stacked bar format
        let maxSegments = 0;
        const chartData = Object.keys(grouped).map(datasetName => {
            const datasetEvents = grouped[datasetName].sort((a, b) =>
                new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
            );

            const row: any = { name: datasetName };
            let lastEndTime = minTime;

            datasetEvents.forEach((event, idx) => {
                const start = new Date(event.start_time).getTime();
                const end = new Date(event.end_time).getTime();

                // Gap from last event (or start) to this event
                const gapDuration = start - lastEndTime;
                // Duration of this event
                // Ensure at least some width for very short events
                const eventDuration = Math.max(end - start, 60000);

                row[`gap_${idx}`] = gapDuration;
                row[`dur_${idx}`] = eventDuration;

                // Store metadata for tooltip/coloring
                row[`meta_${idx}`] = event;

                lastEndTime = start + eventDuration; // Use calculated end for next gap
            });

            maxSegments = Math.max(maxSegments, datasetEvents.length);
            return row;
        });

        return { chartData, maxSegments, minTime, maxTime };
    }, [events]);

    const { chartData, maxSegments, minTime, maxTime } = processedData;

    // Zoom state - only affects X-axis (time dimension), Y-axis (datasets) is locked
    const totalDuration = maxTime - minTime;
    const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null);

    // Initialize zoom domain when data is available
    useEffect(() => {
        if (totalDuration > 0) {
            setZoomDomain([0, totalDuration]);
        }
    }, [totalDuration]);

    const handleZoomIn = () => {
        if (!zoomDomain) return;
        const [start, end] = zoomDomain;
        const duration = end - start;
        const newDuration = duration * 0.6; // Zoom in by 40%
        const center = start + duration / 2;
        setZoomDomain([
            Math.max(0, center - newDuration / 2),
            Math.min(totalDuration, center + newDuration / 2)
        ]);
    };

    const handleZoomOut = () => {
        if (!zoomDomain) return;
        const [start, end] = zoomDomain;
        const duration = end - start;
        const newDuration = duration * 1.4; // Zoom out by 40%
        const center = start + duration / 2;
        setZoomDomain([
            Math.max(0, center - newDuration / 2),
            Math.min(totalDuration, center + newDuration / 2)
        ]);
    };

    const handleReset = () => {
        setZoomDomain([0, totalDuration]);
    };

    const handlePanLeft = () => {
        if (!zoomDomain) return;
        const [start, end] = zoomDomain;
        const duration = end - start;
        const panAmount = duration * 0.25; // Pan by 25% of visible range
        const newStart = Math.max(0, start - panAmount);
        const newEnd = newStart + duration;
        setZoomDomain([newStart, Math.min(totalDuration, newEnd)]);
    };

    const handlePanRight = () => {
        if (!zoomDomain) return;
        const [start, end] = zoomDomain;
        const duration = end - start;
        const panAmount = duration * 0.25; // Pan by 25% of visible range
        const newEnd = Math.min(totalDuration, end + panAmount);
        const newStart = Math.max(0, newEnd - duration);
        setZoomDomain([newStart, newEnd]);
    };

    // Generate bars - memoized to prevent re-rendering on zoom/pan
    const bars = useMemo(() => {
        const barElements = [];
        for (let i = 0; i < maxSegments; i++) {
            // Transparent Gap Bar
            barElements.push(
                <Bar key={`gap-${i}`} dataKey={`gap_${i}`} stackId="a" fill="transparent" isAnimationActive={false} />
            );

            // Colored Event Bar
            barElements.push(
                <Bar key={`dur-${i}`} dataKey={`dur_${i}`} stackId="a" isAnimationActive={false}>
                    {chartData.map((entry: any, index: number) => {
                        const event = entry[`meta_${i}`] as EventResult;
                        if (!event) return <Cell key={`cell-${index}`} fill="transparent" />;

                        let color = '#ef4444'; // Red (No Event)
                        if (event.status === 'Event') color = '#22c55e'; // Green
                        else if (event.status === 'Partial Event') color = '#f59e0b'; // Orange

                        return <Cell key={`cell-${index}`} fill={color} />;
                    })}
                </Bar>
            );
        }
        return barElements;
    }, [chartData, maxSegments]);

    const formatXAxis = (tickItem: number) => {
        return format(new Date(minTime + tickItem), 'dd MMM HH:mm');
    };

    if (events.length === 0) return <div className="text-center p-4 text-gray-500">No events to display</div>;

    return (
        <div className="space-y-2">
            {/* Zoom and Pan Controls - Only affect X-axis (time), Y-axis (datasets) is locked */}
            <div className="flex justify-end gap-2">
                <button
                    onClick={handlePanLeft}
                    className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors disabled:opacity-50"
                    title="Pan Left"
                    disabled={!zoomDomain || zoomDomain[0] === 0}
                >
                    <ChevronLeft size={18} />
                </button>
                <button
                    onClick={handlePanRight}
                    className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors disabled:opacity-50"
                    title="Pan Right"
                    disabled={!zoomDomain || zoomDomain[1] >= totalDuration}
                >
                    <ChevronRight size={18} />
                </button>
                <div className="w-px bg-gray-300 mx-1" />
                <button
                    onClick={handleZoomIn}
                    className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors"
                    title="Zoom In"
                >
                    <ZoomIn size={18} />
                </button>
                <button
                    onClick={handleZoomOut}
                    className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors"
                    title="Zoom Out"
                >
                    <ZoomOut size={18} />
                </button>
                <button
                    onClick={handleReset}
                    className="p-1.5 bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors"
                    title="Reset Zoom"
                >
                    <RotateCcw size={18} />
                </button>
            </div>

            <div style={{ width: '100%', height: Math.max(400, chartData.length * 60) }}>
                <ResponsiveContainer>
                    <BarChart
                        layout="vertical"
                        data={chartData}
                        margin={{ top: 20, right: 30, left: 100, bottom: 20 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            type="number"
                            domain={zoomDomain || [0, totalDuration]}
                            allowDataOverflow={true}
                            tickFormatter={formatXAxis}
                            stroke="#888888"
                            fontSize={12}
                        />
                        <YAxis
                            type="category"
                            dataKey="name"
                            stroke="#888888"
                            fontSize={12}
                            fontWeight={500}
                        />
                        {bars}
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default RainfallEventsGantt;
