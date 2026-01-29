import React, { useMemo, useState, useEffect, useRef } from 'react';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    ResponsiveContainer,
    Cell,
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
    onZoomChange?: (domain: [number, number] | null, minTime: number, totalDuration: number) => void;
    externalZoomDomain?: [number, number] | null;
}

// Keep margins here so chart + mouse math stay in sync
const chartMargin = { top: 20, right: 30, left: 100, bottom: 20 };

const RainfallEventsGantt: React.FC<RainfallEventsGanttProps> = ({ events, onZoomChange, externalZoomDomain }) => {
    // Tooltip state
    const [cursorTime, setCursorTime] = useState<Date | null>(null);
    const [cursorX, setCursorX] = useState(0);
    const [cursorY, setCursorY] = useState(0);

    // Ref for measuring container
    const containerRef = useRef<HTMLDivElement>(null);

    // Preprocess events
    const processedData = useMemo(() => {
        if (!events || events.length === 0) {
            return { chartData: [], maxSegments: 0, minTime: 0, maxTime: 0 };
        }

        const timestamps = events.flatMap(e => [
            new Date(e.start_time).getTime(),
            new Date(e.end_time).getTime(),
        ]);
        const minTime = Math.min(...timestamps);
        const maxTime = Math.max(...timestamps);

        // Group by dataset
        const grouped: Record<string, EventResult[]> = {};
        for (const e of events) {
            if (!grouped[e.dataset_name]) grouped[e.dataset_name] = [];
            grouped[e.dataset_name].push(e);
        }

        // Build stacked rows
        let maxSegments = 0;
        const chartData = Object.keys(grouped).map(dataset => {
            const datasetEvents = grouped[dataset].sort(
                (a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime()
            );

            const row: any = { name: dataset };
            let lastEndTime = minTime;

            datasetEvents.forEach((event, idx) => {
                const start = new Date(event.start_time).getTime();
                const end = new Date(event.end_time).getTime();

                const gapDuration = start - lastEndTime;
                const eventDuration = Math.max(end - start, 60000); // enforce min width

                row[`gap_${idx}`] = gapDuration;
                row[`dur_${idx}`] = eventDuration;
                row[`meta_${idx}`] = event;

                lastEndTime = start + eventDuration;
            });

            maxSegments = Math.max(maxSegments, datasetEvents.length);
            return row;
        });

        return { chartData, maxSegments, minTime, maxTime };
    }, [events]);

    const { chartData, maxSegments, minTime, maxTime } = processedData;
    const totalDuration = maxTime - minTime;

    // Zoom domain - use external if provided
    const [internalZoomDomain, setInternalZoomDomain] = useState<[number, number] | null>(null);
    const zoomDomain = externalZoomDomain ?? internalZoomDomain;

    const setZoomDomain = (domain: [number, number] | null) => {
        setInternalZoomDomain(domain);
        if (onZoomChange && domain) {
            onZoomChange(domain, minTime, totalDuration);
        }
    };

    useEffect(() => {
        if (totalDuration > 0 && !externalZoomDomain) {
            const initial: [number, number] = [0, totalDuration];
            setInternalZoomDomain(initial);
            if (onZoomChange) {
                onZoomChange(initial, minTime, totalDuration);
            }
        }
    }, [totalDuration, externalZoomDomain, minTime, onZoomChange]);

    // Zoom/pan handlers
    const handleZoomIn = () => {
        if (!zoomDomain) return;
        const [s, e] = zoomDomain;
        const d = e - s;
        const nd = d * 0.6;
        const c = s + d / 2;
        setZoomDomain([Math.max(0, c - nd / 2), Math.min(totalDuration, c + nd / 2)]);
    };

    const handleZoomOut = () => {
        if (!zoomDomain) return;
        const [s, e] = zoomDomain;
        const d = e - s;
        const nd = d * 1.4;
        const c = s + d / 2;
        setZoomDomain([Math.max(0, c - nd / 2), Math.min(totalDuration, c + nd / 2)]);
    };

    const handleReset = () => setZoomDomain([0, totalDuration]);

    const handlePanLeft = () => {
        if (!zoomDomain) return;
        const [s, e] = zoomDomain;
        const d = e - s;
        const amt = d * 0.25;
        const ns = Math.max(0, s - amt);
        setZoomDomain([ns, Math.min(totalDuration, ns + d)]);
    };

    const handlePanRight = () => {
        if (!zoomDomain) return;
        const [s, e] = zoomDomain;
        const d = e - s;
        const amt = d * 0.25;
        const ne = Math.min(totalDuration, e + amt);
        setZoomDomain([Math.max(0, ne - d), ne]);
    };

    // Build bars
    const bars = useMemo(() => {
        const arr = [];
        for (let i = 0; i < maxSegments; i++) {
            arr.push(
                <Bar
                    key={`gap-${i}`}
                    dataKey={`gap_${i}`}
                    stackId="a"
                    fill="transparent"
                    isAnimationActive={false}
                />
            );
            arr.push(
                <Bar
                    key={`dur-${i}`}
                    dataKey={`dur_${i}`}
                    stackId="a"
                    isAnimationActive={false}
                >
                    {chartData.map((entry: any, idx) => {
                        const ev = entry[`meta_${i}`] as EventResult;
                        if (!ev) return <Cell key={idx} fill="transparent" />;
                        let fill = "#ef4444";
                        if (ev.status === "Event") fill = "#22c55e";
                        else if (ev.status === "Partial Event") fill = "#f59e0b";
                        return <Cell key={idx} fill={fill} />;
                    })}
                </Bar>
            );
        }
        return arr;
    }, [chartData, maxSegments]);

    const formatXAxis = (x: number) =>
        format(new Date(minTime + x), "dd MMM HH:mm");

    if (events.length === 0) {
        return <div className="text-center p-4 text-gray-500">No events to display</div>;
    }

    return (
        <div className="relative space-y-2">
            {/* Controls */}
            <div className="flex justify-end gap-2">
                <button onClick={handlePanLeft}><ChevronLeft size={18} /></button>
                <button onClick={handlePanRight}><ChevronRight size={18} /></button>
                <button onClick={handleZoomIn}><ZoomIn size={18} /></button>
                <button onClick={handleZoomOut}><ZoomOut size={18} /></button>
                <button onClick={handleReset}><RotateCcw size={18} /></button>
            </div>

            {/* Floating tooltip – just date */}
            {cursorTime && Number.isFinite(cursorX) && Number.isFinite(cursorY) && (
                <div
                    className="absolute pointer-events-none bg-white border border-gray-300 shadow-md p-2 text-xs rounded"
                    style={{
                        left: cursorX + 12,
                        top: cursorY + 12,
                        zIndex: 9999,
                    }}
                >
                    {format(cursorTime, "dd MMM yyyy")}
                </div>
            )}

            {/* Mouse tracking wrapper */}
            <div
                ref={containerRef}
                style={{
                    width: "100%",
                    height: Math.max(400, chartData.length * 60),
                    position: "relative",
                }}
                onMouseMove={(e) => {
                    if (!containerRef.current || !zoomDomain) {
                        setCursorTime(null);
                        return;
                    }

                    const rect = containerRef.current.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;

                    const fullWidth = rect.width;

                    // X-axis actual drawing area (exclude left/right margins)
                    const axisStart = chartMargin.left;
                    const axisEnd = fullWidth - chartMargin.right;
                    const axisWidth = axisEnd - axisStart;

                    if (axisWidth <= 0) {
                        setCursorTime(null);
                        return;
                    }

                    // If mouse is outside plot area horizontally, hide tooltip
                    if (x < axisStart || x > axisEnd) {
                        setCursorTime(null);
                        return;
                    }

                    const ratio = (x - axisStart) / axisWidth;
                    const [ds, de] = zoomDomain;
                    const offset = ds + ratio * (de - ds);

                    setCursorX(x);
                    setCursorY(y);
                    setCursorTime(new Date(minTime + offset));
                }}
                onMouseLeave={() => setCursorTime(null)}
            >
                <ResponsiveContainer>
                    <BarChart
                        layout="vertical"
                        data={chartData}
                        margin={chartMargin}
                    >
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis
                            type="number"
                            domain={zoomDomain || [0, totalDuration]}
                            allowDataOverflow
                            tickFormatter={formatXAxis}
                            fontSize={12}
                        />
                        <YAxis
                            type="category"
                            dataKey="name"
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