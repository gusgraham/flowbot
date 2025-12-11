import React, { useState, useEffect } from 'react';
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceArea
} from 'recharts';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Loader2, ZoomIn } from 'lucide-react';
import { format, parseISO } from 'date-fns';

const API_URL = 'http://localhost:8001/api';

interface WQGraphProps {
    monitorId: number;
}

const COLORS = ['#0891b2', '#16a34a', '#dc2626', '#ea580c', '#8b5cf6'];

const WQGraph: React.FC<WQGraphProps> = ({ monitorId }) => {
    // Zoom state
    const [left, setLeft] = useState<string | 'dataMin'>('dataMin');
    const [right, setRight] = useState<string | 'dataMax'>('dataMax');
    const [refAreaLeft, setRefAreaLeft] = useState('');
    const [refAreaRight, setRefAreaRight] = useState('');

    // Resolution state
    const [resolution, setResolution] = useState(5000);

    // Mean Value Aggregation State
    const [showMean, setShowMean] = useState(false);
    const [meanFreq, setMeanFreq] = useState('D'); // D, W, M, A

    // Fetch Data
    const { data: rawData, isLoading } = useQuery({
        queryKey: ['wq-data', monitorId, resolution, showMean, meanFreq], // Add mean options to key
        queryFn: async () => {
            let url = `${API_URL}/wq/monitors/${monitorId}/data?points=${resolution}`;
            if (showMean) {
                url += `&resample=${meanFreq}`;
            }
            const res = await axios.get(url);
            return res.data as Record<string, { time: string, value: number }[]>;
        },
        enabled: !!monitorId
    });

    // Transform data for Recharts (merge series by time)
    // Recharts needs: [{time: '...', pH: 7.1, DO: 8.2}, ...]
    const [chartData, setChartData] = useState<any[]>([]);
    const [variables, setVariables] = useState<string[]>([]);

    useEffect(() => {
        if (!rawData) return;

        const timestampMap = new Map<string, any>();
        // Base variables are those WITHOUT _mean suffix
        const allKeys = Object.keys(rawData);
        const baseVars = allKeys.filter(k => !k.endsWith('_mean'));

        // Sort according to user preference
        const PREFERRED_ORDER = ['Conductivity', 'DO', 'DOSat', 'Ammonia', 'pH', 'Temperature'];
        baseVars.sort((a, b) => {
            const idxA = PREFERRED_ORDER.indexOf(a);
            const idxB = PREFERRED_ORDER.indexOf(b);
            // If both found, sort by index
            if (idxA !== -1 && idxB !== -1) return idxA - idxB;
            // If only A found, A comes first
            if (idxA !== -1) return -1;
            // If only B found, B comes first
            if (idxB !== -1) return 1;
            // Otherwise alphabetical
            return a.localeCompare(b);
        });

        setVariables(baseVars);

        allKeys.forEach(v => {
            rawData[v].forEach(pt => {
                if (!timestampMap.has(pt.time)) {
                    timestampMap.set(pt.time, { time: pt.time, timeVal: new Date(pt.time).getTime() });
                }
                const entry = timestampMap.get(pt.time);
                entry[v] = pt.value;
            });
        });

        const sortedData = Array.from(timestampMap.values()).sort((a, b) => a.timeVal - b.timeVal);
        setChartData(sortedData);
    }, [rawData]);

    const zoom = () => {
        if (refAreaLeft === refAreaRight || refAreaRight === '') {
            setRefAreaLeft('');
            setRefAreaRight('');
            return;
        }

        let l = refAreaLeft;
        let r = refAreaRight;

        // Ensure left is smaller
        if (l > r) [l, r] = [r, l];

        setLeft(l);
        setRight(r);
        setRefAreaLeft('');
        setRefAreaRight('');
    };

    const zoomOut = () => {
        setLeft('dataMin');
        setRight('dataMax');
    };

    if (isLoading) return <div className="h-64 flex justify-center items-center"><Loader2 className="animate-spin" /></div>;
    if (!chartData.length) return <div className="h-64 flex justify-center items-center text-gray-400">No data to display</div>;

    return (
        <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm select-none">
            <div className="flex justify-between items-center mb-4 sticky top-0 bg-white z-10 pb-2 border-b">
                <div className="flex items-center gap-4 flex-wrap">
                    <h3 className="font-bold text-gray-700">Time Series Analysis</h3>

                    {/* Resolution Control - Always visible */}
                    <div className="flex items-center gap-2">
                        <label className="text-xs text-gray-500">Res:</label>
                        <select
                            value={resolution}
                            onChange={e => setResolution(Number(e.target.value))}
                            className="text-xs border border-gray-300 rounded px-1.5 py-0.5"
                        >
                            <option value={500}>Low (500 pts)</option>
                            <option value={2000}>Med (2k pts)</option>
                            <option value={5000}>High (5k pts)</option>
                            <option value={100000}>Full (All)</option>
                        </select>
                    </div>

                    {/* Mean Value Toggle */}
                    <div className="flex items-center gap-2 border-l pl-4 ml-2">
                        <label className="flex items-center gap-2 cursor-pointer">
                            <input
                                type="checkbox"
                                checked={showMean}
                                onChange={e => setShowMean(e.target.checked)}
                                className="rounded text-cyan-600 focus:ring-cyan-500"
                            />
                            <span className="text-sm font-medium text-gray-700">Plot Mean Values</span>
                        </label>

                        {showMean && (
                            <select
                                value={meanFreq}
                                onChange={e => setMeanFreq(e.target.value)}
                                className="text-xs border border-gray-300 rounded px-1.5 py-0.5 bg-cyan-50 border-cyan-200"
                            >
                                <option value="D">Daily</option>
                                <option value="W">Weekly</option>
                                <option value="M">Monthly</option>
                                <option value="A">Yearly</option>
                            </select>
                        )}
                    </div>
                </div>

                <button onClick={zoomOut} className="text-xs flex items-center gap-1 text-cyan-600 hover:text-cyan-800">
                    <ZoomIn size={14} /> Reset Zoom
                </button>
            </div>

            <div className="space-y-4">
                {variables.map((v, i) => (
                    <div key={v} className="h-[200px] w-full relative">
                        {/* Title overlay? or Axis Label? */}

                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart
                                data={chartData}
                                syncId="wqGraphSync"
                                onMouseDown={e => e && e.activeLabel && setRefAreaLeft(e.activeLabel)}
                                onMouseMove={e => e && e.activeLabel && refAreaLeft && setRefAreaRight(e.activeLabel)}
                                onMouseUp={zoom}
                                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
                            >
                                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                                <XAxis
                                    dataKey="time"
                                    domain={[left, right]}
                                    type="category"
                                    allowDataOverflow
                                    tickFormatter={t => format(parseISO(t), 'MM/dd HH:mm')}
                                    minTickGap={50}
                                    hide={i < variables.length - 1} // Only show X axis on bottom chart
                                />
                                <YAxis
                                    label={{ value: v, angle: -90, position: 'insideLeft', offset: 10, style: { textAnchor: 'middle' } }}
                                />
                                <Tooltip
                                    labelFormatter={t => format(parseISO(t as string), 'PPpp')}
                                    contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }}
                                />

                                {/* RAW Data Line */}
                                <Line
                                    type="monotone"
                                    dataKey={v}
                                    stroke={COLORS[i % COLORS.length]}
                                    dot={false}
                                    strokeWidth={1}
                                    strokeOpacity={showMean ? 0.3 : 1}
                                    connectNulls
                                    animationDuration={300}
                                    name={v}
                                />

                                {/* Mean Data Line (Overlay) */}
                                {showMean && (
                                    <Line
                                        type="monotone"
                                        dataKey={`${v}_mean`}
                                        stroke={COLORS[i % COLORS.length]}
                                        strokeWidth={2}
                                        dot={false}
                                        connectNulls
                                        animationDuration={300}
                                        name={`${v} (Mean)`}
                                    />
                                )}

                                {refAreaLeft && refAreaRight ? (
                                    <ReferenceArea x1={refAreaLeft} x2={refAreaRight} strokeOpacity={0.3} />
                                ) : null}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default WQGraph;
