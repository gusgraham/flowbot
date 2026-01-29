import React, { useMemo, useState, useRef, useCallback } from 'react';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    ResponsiveContainer,
    ReferenceLine,
    Legend,
    ReferenceArea,
    Tooltip,
} from 'recharts';
import { format } from 'date-fns';

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

interface CaptureData {
    type: 'storm' | 'dryDay';
    startTime: Date;
    endTime: Date;
}

interface RainfallEventsHistogramProps {
    events: EventResult[];
    dryDays: DryDayResult[];
    totalDatasets: number;
    zoomDomain: [number, number] | null;
    minTime: number;
    onCaptureEvent?: (data: CaptureData) => void;
}

const chartMargin = { top: 10, right: 30, left: 100, bottom: 0 };

const RainfallEventsHistogram: React.FC<RainfallEventsHistogramProps> = ({
    events,
    dryDays,
    totalDatasets,
    zoomDomain,
    minTime: propsMinTime,
    onCaptureEvent,
}) => {
    const containerRef = useRef<HTMLDivElement>(null);
    const [hoverInfo, setHoverInfo] = useState<{
        type: 'storm' | 'dryDay' | null;
        startOffset: number;
        endOffset: number;
    } | null>(null);

    // Track the current hovered time offset from tooltip
    const [hoveredTimeOffset, setHoveredTimeOffset] = useState<number | null>(null);

    // Compute minTime internally from events to ensure consistency
    const localMinTime = useMemo(() => {
        if (!events || events.length === 0) return 0;
        const allTimes = events.flatMap(e => [
            new Date(e.start_time).getTime(),
            new Date(e.end_time).getTime(),
        ]);
        return Math.min(...allTimes);
    }, [events]);

    // Use props minTime if set (non-zero), otherwise use local calculation
    const effectiveMinTime = propsMinTime > 0 ? propsMinTime : localMinTime;

    // Compute storm event spans (contiguous periods where storms are active)
    const stormSpans = useMemo(() => {
        const spans: Array<{ start: number; end: number }> = [];
        const passingEvents = events.filter(e => e.status === 'Event' || e.status === 'Partial Event');

        for (const event of passingEvents) {
            const eventStart = new Date(event.start_time).getTime() - effectiveMinTime;
            const eventEnd = new Date(event.end_time).getTime() - effectiveMinTime;

            // Check if this event extends an existing span
            let merged = false;
            for (const span of spans) {
                if (eventStart <= span.end && eventEnd >= span.start) {
                    span.start = Math.min(span.start, eventStart);
                    span.end = Math.max(span.end, eventEnd);
                    merged = true;
                    break;
                }
            }
            if (!merged) {
                spans.push({ start: eventStart, end: eventEnd });
            }
        }

        return spans.sort((a, b) => a.start - b.start);
    }, [events, effectiveMinTime]);

    // Compute dry day spans (individual days)
    const dryDaySpans = useMemo(() => {
        const msPerDay = 24 * 60 * 60 * 1000;
        const spans: Array<{ start: number; end: number; date: string }> = [];

        for (const dd of dryDays) {
            // Parse date as local midnight (not UTC)
            const dateStr = dd.date.split('T')[0]; // Get just the date part
            const dayStart = new Date(dateStr + 'T00:00:00').getTime() - effectiveMinTime;
            const dayEnd = dayStart + msPerDay;

            const exists = spans.some(s => s.start === dayStart);
            if (!exists) {
                spans.push({ start: dayStart, end: dayEnd, date: dd.date });
            }
        }

        return spans.sort((a, b) => a.start - b.start);
    }, [dryDays, effectiveMinTime]);

    // Build step-chart data
    const histogramData = useMemo(() => {
        if (!events || events.length === 0) return [];

        const timePoints = new Set<number>();
        const msPerDay = 24 * 60 * 60 * 1000;

        for (const event of events) {
            if (event.status === 'Event' || event.status === 'Partial Event') {
                timePoints.add(new Date(event.start_time).getTime());
                timePoints.add(new Date(event.end_time).getTime());
            }
        }

        for (const dd of dryDays) {
            const dateStr = dd.date.split('T')[0];
            const dayStart = new Date(dateStr + 'T00:00:00').getTime();
            timePoints.add(dayStart);
            timePoints.add(dayStart + msPerDay);
        }

        const allTimes = events.flatMap(e => [
            new Date(e.start_time).getTime(),
            new Date(e.end_time).getTime(),
        ]);
        const dataMinTime = Math.min(...allTimes);
        const dataMaxTime = Math.max(...allTimes);
        timePoints.add(dataMinTime);
        timePoints.add(dataMaxTime);

        const sortedTimes = Array.from(timePoints).sort((a, b) => a - b);

        const data: Array<{
            time: number;
            stormEvents: number;
            dryDays: number;
        }> = [];

        for (const t of sortedTimes) {
            const datasetsWithEvents = new Set<number>();
            for (const event of events) {
                if (event.status === 'Event' || event.status === 'Partial Event') {
                    const eventStart = new Date(event.start_time).getTime();
                    const eventEnd = new Date(event.end_time).getTime();
                    if (t >= eventStart && t < eventEnd) {
                        datasetsWithEvents.add(event.dataset_id);
                    }
                }
            }

            const datasetsWithDryDays = new Set<number>();
            for (const dd of dryDays) {
                const dateStr = dd.date.split('T')[0];
                const dayStart = new Date(dateStr + 'T00:00:00').getTime();
                const dayEnd = dayStart + msPerDay;
                if (t >= dayStart && t < dayEnd) {
                    datasetsWithDryDays.add(dd.dataset_id);
                }
            }

            data.push({
                time: t - effectiveMinTime,
                stormEvents: datasetsWithEvents.size,
                dryDays: datasetsWithDryDays.size,
            });
        }

        return data;
    }, [events, dryDays, effectiveMinTime]);

    // Update hover info when time offset changes
    const updateHoverInfo = useCallback((timeOffset: number | null) => {
        if (timeOffset === null) {
            setHoverInfo(null);
            return;
        }

        // Check storm spans first
        for (const span of stormSpans) {
            if (timeOffset >= span.start && timeOffset < span.end) {
                setHoverInfo({
                    type: 'storm',
                    startOffset: span.start,
                    endOffset: span.end,
                });
                return;
            }
        }

        // Check dry day spans
        for (const span of dryDaySpans) {
            if (timeOffset >= span.start && timeOffset < span.end) {
                setHoverInfo({
                    type: 'dryDay',
                    startOffset: span.start,
                    endOffset: span.end,
                });
                return;
            }
        }

        setHoverInfo(null);
    }, [stormSpans, dryDaySpans]);

    // Custom tooltip content that captures the time value
    const CustomTooltipContent = useCallback(({ active, payload, label }: any) => {
        if (active && payload && payload.length > 0) {
            const timeOffset = label as number;
            // Update hover state when tooltip is active
            if (timeOffset !== hoveredTimeOffset) {
                setHoveredTimeOffset(timeOffset);
                updateHoverInfo(timeOffset);
            }
        }
        // Return null to hide the actual tooltip - we only use it for coordinate detection
        return null;
    }, [hoveredTimeOffset, updateHoverInfo]);

    // Handle click to capture
    const handleClick = useCallback(() => {
        if (!hoverInfo || !onCaptureEvent) return;

        onCaptureEvent({
            type: hoverInfo.type!,
            startTime: new Date(effectiveMinTime + hoverInfo.startOffset),
            endTime: new Date(effectiveMinTime + hoverInfo.endOffset),
        });
    }, [hoverInfo, onCaptureEvent, effectiveMinTime]);

    const formatXAxis = (x: number) => format(new Date(effectiveMinTime + x), "dd MMM");

    if (events.length === 0) {
        return null;
    }

    return (
        <div
            ref={containerRef}
            className="w-full relative"
            style={{ height: 150, cursor: hoverInfo ? 'pointer' : 'default' }}
            onMouseLeave={() => {
                setHoverInfo(null);
                setHoveredTimeOffset(null);
            }}
            onClick={handleClick}
        >
            <ResponsiveContainer>
                <AreaChart
                    data={histogramData}
                    margin={chartMargin}
                >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis
                        dataKey="time"
                        type="number"
                        domain={zoomDomain || ['dataMin', 'dataMax']}
                        allowDataOverflow
                        tickFormatter={formatXAxis}
                        fontSize={12}
                    />
                    <YAxis
                        domain={[0, totalDatasets]}
                        allowDataOverflow
                        fontSize={12}
                        label={{
                            value: 'RGs Passing',
                            angle: -90,
                            position: 'insideLeft',
                            style: { textAnchor: 'middle', fontSize: 11 }
                        }}
                    />

                    {/* Hidden tooltip for coordinate detection */}
                    <Tooltip
                        content={CustomTooltipContent}
                        cursor={false}
                    />

                    {/* Threshold line for total datasets */}
                    <ReferenceLine
                        y={totalDatasets}
                        stroke="#10b981"
                        strokeDasharray="5 5"
                        strokeWidth={2}
                    />
                    {/* Half threshold line */}
                    {totalDatasets > 1 && (
                        <ReferenceLine
                            y={Math.ceil(totalDatasets / 2)}
                            stroke="#6b7280"
                            strokeDasharray="3 3"
                            strokeWidth={1}
                        />
                    )}

                    {/* Highlight hovered span */}
                    {hoverInfo && (
                        <ReferenceArea
                            x1={hoverInfo.startOffset}
                            x2={hoverInfo.endOffset}
                            fill={hoverInfo.type === 'storm' ? '#3b82f6' : '#f97316'}
                            fillOpacity={0.3}
                            stroke={hoverInfo.type === 'storm' ? '#3b82f6' : '#f97316'}
                            strokeWidth={2}
                            strokeDasharray="3 3"
                        />
                    )}

                    <Area
                        type="stepAfter"
                        dataKey="stormEvents"
                        name="Storm Events"
                        stroke="#3b82f6"
                        fill="#3b82f6"
                        fillOpacity={0.3}
                        strokeWidth={2}
                        isAnimationActive={false}
                    />
                    <Area
                        type="stepAfter"
                        dataKey="dryDays"
                        name="Dry Days"
                        stroke="#f97316"
                        fill="#f97316"
                        fillOpacity={0.3}
                        strokeWidth={2}
                        isAnimationActive={false}
                    />
                    <Legend
                        verticalAlign="top"
                        height={25}
                        iconType="line"
                    />
                </AreaChart>
            </ResponsiveContainer>

            {/* Tooltip showing what will be captured */}
            {hoverInfo && (
                <div
                    className="absolute top-2 right-2 bg-white border border-gray-300 shadow-md px-3 py-2 rounded text-xs pointer-events-none"
                    style={{ zIndex: 10 }}
                >
                    <div className="font-semibold">
                        {hoverInfo.type === 'storm' ? '🌧️ Capture Storm Event' : '☀️ Capture Dry Day'}
                    </div>
                    <div className="text-gray-600">
                        {format(new Date(effectiveMinTime + hoverInfo.startOffset), "dd MMM HH:mm")} -
                        {format(new Date(effectiveMinTime + hoverInfo.endOffset), "dd MMM HH:mm")}
                    </div>
                    <div className="text-gray-400 mt-1">Click to capture</div>
                </div>
            )}
        </div>
    );
};

export default RainfallEventsHistogram;
