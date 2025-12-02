// ScatterChart.tsx – Reimplemented from scratch
import React, { useEffect, useState } from "react";
import {
    ScatterChart as RechartsScatter,
    Scatter,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceLine,
} from "recharts";
import { Loader2, ChevronDown } from "lucide-react";
import { useFDVScatter } from "../../api/hooks";

// ---------------------------------------------------------------------------
// Helper types
// ---------------------------------------------------------------------------
type PipeParams = {
    diameter?: number; // mm
    roughness?: number; // mm
    gradient?: number; // ratio (e.g. 0.054)
    shape?: string; // "CIRC" | "RECT"
    length?: number; // m (optional)
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------
const ScatterChart: React.FC<{ datasetId: string }> = ({ datasetId }) => {
    // -----------------------------------------------------------------------
    // UI state
    // -----------------------------------------------------------------------
    const [plotMode, setPlotMode] = useState<"velocity" | "flow">("velocity");
    const [showScatter, setShowScatter] = useState(true);
    const [showCBW, setShowCBW] = useState(true);
    const [showIso, setShowIso] = useState(true);
    const [controlsExpanded, setControlsExpanded] = useState(false);

    // Iso‑line configuration
    const [localIsoMin, setLocalIsoMin] = useState<string>("");
    const [localIsoMax, setLocalIsoMax] = useState<string>("");
    const [localIsoCount, setLocalIsoCount] = useState<string>("2");
    const [isoMin, setIsoMin] = useState<number | undefined>(undefined);
    const [isoMax, setIsoMax] = useState<number | undefined>(undefined);
    const [isoCount, setIsoCount] = useState<number>(2);

    // -----------------------------------------------------------------------
    // Data fetching
    // -----------------------------------------------------------------------
    const { data: response, isLoading, error } = useFDVScatter(
        datasetId,
        plotMode,
        isoMin,
        isoMax,
        isoCount
    );

    // -----------------------------------------------------------------------
    // Prepare data points (Moved before early returns to satisfy Rules of Hooks)
    // -----------------------------------------------------------------------
    const {
        scatter_data = [],
        cbw_curve = [],
        iso_curves = [],
        iso_type = "flow",
        pipe_params = {},
        pipe_profile = [],
    } = response || {};

    const xVar = plotMode === "velocity" ? "velocity" : "flow";

    const scatterPoints = React.useMemo(() => scatter_data.map((d: any) => ({
        x: d[xVar],
        y: d.depth,
        flow: d.flow,
        velocity: d.velocity,
    })), [scatter_data, xVar]);

    const cbwPoints = React.useMemo(() => cbw_curve.map((d: any) => ({ x: d[xVar], y: d.depth })), [cbw_curve, xVar]);



    // -----------------------------------------------------------------------
    // Initialise iso‑line defaults
    // -----------------------------------------------------------------------
    useEffect(() => {
        if (response?.scatter_data && !localIsoMin && !localIsoMax) {
            const data = response.scatter_data;
            if (plotMode === "velocity") {
                const flowVals = data.map((d: any) => d.flow).filter((f: number) => f > 0);
                if (flowVals.length) {
                    setLocalIsoMin(Math.min(...flowVals).toFixed(2));
                    setLocalIsoMax(Math.max(...flowVals).toFixed(2));
                }
            } else {
                const velVals = data.map((d: any) => d.velocity).filter((v: number) => v > 0);
                if (velVals.length) {
                    setLocalIsoMin(Math.min(...velVals).toFixed(3));
                    setLocalIsoMax(Math.max(...velVals).toFixed(3));
                }
            }
        }
    }, [response, plotMode, localIsoMin, localIsoMax]);

    // Reset iso‑line UI when switching plot mode
    useEffect(() => {
        setLocalIsoMin("");
        setLocalIsoMax("");
        setLocalIsoCount("2");
        setIsoMin(undefined);
        setIsoMax(undefined);
        setIsoCount(2);
    }, [plotMode]);

    const applyIsoSettings = () => {
        setIsoMin(localIsoMin ? parseFloat(localIsoMin) : undefined);
        setIsoMax(localIsoMax ? parseFloat(localIsoMax) : undefined);
        setIsoCount(parseInt(localIsoCount) || 2);
    };

    // -----------------------------------------------------------------------
    // Loading / error handling
    // -----------------------------------------------------------------------
    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-64">
                <Loader2 className="animate-spin text-purple-500" size={32} />
            </div>
        );
    }

    if (error || !response) {
        return (
            <div className="bg-red-50 border border-red-200 text-red-600 p-4 rounded-lg">
                Error loading scatter graph data.
            </div>
        );
    }

    // -----------------------------------------------------------------------
    // Axis domain calculation
    // -----------------------------------------------------------------------
    const allX = [...scatterPoints.map((p: any) => p.x), ...cbwPoints.map((p: any) => p.x)];
    const allY = [...scatterPoints.map((p: any) => p.y), ...cbwPoints.map((p: any) => p.y)];

    const minX = Math.min(...allX);
    const maxX = Math.max(...allX);
    const minY = Math.min(...allY);
    const maxY = Math.max(...allY);

    const xRange = maxX - minX;
    const yRange = maxY - minY;

    // Calculate initial domain from data
    let xDomain = [minX < 0 ? minX - 0.1 * xRange : 0, maxX + 0.1 * xRange];
    const yDomain = [0, maxY + 0.1 * yRange];

    // Expand X domain to include pipe profile if present
    if (pipe_profile && pipe_profile.length > 0) {
        const allPipeX: number[] = [];
        pipe_profile.forEach((line: any) => {
            line.forEach((point: any) => {
                if (point.x !== undefined) {
                    allPipeX.push(point.x);
                }
            });
        });

        if (allPipeX.length > 0) {
            const pipeMinX = Math.min(...allPipeX);
            const pipeMaxX = Math.max(...allPipeX);
            xDomain = [Math.min(xDomain[0], pipeMinX), Math.max(xDomain[1], pipeMaxX)];
        }
    }


    // -----------------------------------------------------------------------
    // Tooltip
    // -----------------------------------------------------------------------
    const CustomTooltip = ({ active, payload }: any) => {
        if (active && payload && payload.length) {
            const data = payload[0].payload;
            return (
                <div className="bg-white p-2 border border-gray-200 shadow-md rounded text-xs">
                    <p className="font-semibold">Data Point</p>
                    <p>Depth: {data.y.toFixed(2)} mm</p>
                    <p>Velocity: {data.velocity?.toFixed(3)} m/s</p>
                    <p>Flow: {data.flow?.toFixed(3)} L/s</p>
                </div>
            );
        }
        return null;
    };

    // -----------------------------------------------------------------------
    // Render
    // -----------------------------------------------------------------------
    return (
        <div className="space-y-4">
            {/* Header & mode toggle */}
            <div className="flex justify-between items-center">
                <h3 className="text-lg font-semibold text-gray-900">Scatter Graph</h3>
                <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg">
                    <button
                        onClick={() => setPlotMode("velocity")}
                        className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${plotMode === "velocity"
                            ? "bg-white text-purple-600 shadow"
                            : "text-gray-600 hover:text-gray-900"
                            }`}
                    >
                        Depth vs Velocity
                    </button>
                    <button
                        onClick={() => setPlotMode("flow")}
                        className={`px-3 py-1.5 text-sm font-medium rounded transition-colors ${plotMode === "flow"
                            ? "bg-white text-purple-600 shadow"
                            : "text-gray-600 hover:text-gray-900"
                            }`}
                    >
                        Depth vs Flow
                    </button>
                </div>
            </div>

            {/* Collapsible controls */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
                <button
                    onClick={() => setControlsExpanded(!controlsExpanded)}
                    className="w-full flex items-center justify-between p-3 hover:bg-gray-100 transition-colors"
                >
                    <span className="text-sm font-semibold text-gray-700">
                        Display Options & Configuration
                    </span>
                    <ChevronDown
                        size={18}
                        className={`transition-transform text-gray-600 ${controlsExpanded ? "rotate-180" : ""
                            }`}
                    />
                </button>
                {controlsExpanded && (
                    <div className="p-4 border-t border-gray-200 grid grid-cols-1 md:grid-cols-2 gap-4">
                        {/* Display toggles */}
                        <div>
                            <h4 className="text-sm font-semibold text-gray-700 mb-3">
                                Display Options
                            </h4>
                            <div className="space-y-2">

                                <label className="flex items-center space-x-2 cursor-pointer text-sm">
                                    <input
                                        type="checkbox"
                                        checked={showScatter}
                                        onChange={e => setShowScatter(e.target.checked)}
                                        className="rounded text-purple-600 focus:ring-purple-500"
                                    />
                                    <span>Show Individual Points</span>
                                </label>
                                <label className="flex items-center space-x-2 cursor-pointer text-sm">
                                    <input
                                        type="checkbox"
                                        checked={showCBW}
                                        onChange={e => setShowCBW(e.target.checked)}
                                        className="rounded text-purple-600 focus:ring-purple-500"
                                    />
                                    <span>Show Colebrook‑White</span>
                                </label>
                                <label className="flex items-center space-x-2 cursor-pointer text-sm">
                                    <input
                                        type="checkbox"
                                        checked={showIso}
                                        onChange={e => setShowIso(e.target.checked)}
                                        className="rounded text-purple-600 focus:ring-purple-500"
                                    />
                                    <span>Show Iso‑{iso_type === "flow" ? "Flow" : "Velocity"} Lines</span>
                                </label>
                            </div>
                        </div>
                        {/* Iso‑line configuration */}
                        <div>
                            <h4 className="text-sm font-semibold text-gray-700 mb-3">
                                Iso‑{iso_type === "flow" ? "Flow" : "Velocity"} Configuration
                            </h4>
                            <div className="grid grid-cols-3 gap-2 mb-2">
                                <div>
                                    <label className="block text-xs text-gray-600 mb-1">
                                        Min ({iso_type === "flow" ? "L/s" : "m/s"})
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={localIsoMin}
                                        onChange={e => setLocalIsoMin(e.target.value)}
                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-600 mb-1">
                                        Max ({iso_type === "flow" ? "L/s" : "m/s"})
                                    </label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={localIsoMax}
                                        onChange={e => setLocalIsoMax(e.target.value)}
                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs text-gray-600 mb-1">Count</label>
                                    <input
                                        type="number"
                                        min="1"
                                        max="10"
                                        value={localIsoCount}
                                        onChange={e => setLocalIsoCount(e.target.value)}
                                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                                    />
                                </div>
                            </div>
                            <button
                                onClick={applyIsoSettings}
                                className="w-full px-3 py-1.5 bg-purple-600 text-white text-sm rounded hover:bg-purple-700 transition-colors"
                            >
                                Apply Settings
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {/* Chart */}
            <div className="bg-white border border-gray-200 rounded-lg p-4 relative">
                <ResponsiveContainer width="100%" height={500}>
                    <RechartsScatter margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                        <XAxis
                            type="number"
                            dataKey="x"
                            name={plotMode === "velocity" ? "Velocity (m/s)" : "Flow (L/s)"}
                            label={{ value: plotMode === "velocity" ? "Velocity (m/s)" : "Flow (L/s)", position: "insideBottom", offset: -5 }}
                            domain={xDomain}
                            allowDataOverflow={true}
                            tickFormatter={(value) => value.toFixed(2)}
                        />
                        <YAxis
                            type="number"
                            dataKey="y"
                            name="Depth"
                            unit=" mm"
                            label={{ value: "Depth (mm)", angle: -90, position: "insideLeft" }}
                            domain={yDomain}
                            allowDataOverflow={true}
                        />
                        <Tooltip content={<CustomTooltip />} cursor={{ strokeDasharray: "3 3" }} />
                        <Legend verticalAlign="top" height={36} />

                        {/* Reference line for pipe soffit – depth equals pipe diameter */}
                        {pipe_params?.diameter && (
                            <ReferenceLine
                                y={pipe_params.diameter}
                                stroke="red"
                                strokeDasharray="3 3"
                                label={{ value: "Pipe Soffit", position: "insideTopRight", fill: "red", fontSize: 12 }}
                            />
                        )}



                        {showScatter && (
                            <Scatter
                                name="Individual Points"
                                data={scatterPoints}
                                fill="#8884d8"
                                fillOpacity={0.3}
                                shape="circle"
                            />
                        )}

                        {showCBW && cbwPoints.length > 0 && (
                            <Line
                                name="Colebrook‑White"
                                data={cbwPoints}
                                type="monotone"
                                dataKey="y"
                                stroke="#000000"
                                strokeWidth={2}
                                strokeDasharray="5 5"
                                dot={false}
                                activeDot={false}
                                isAnimationActive={false}
                            />
                        )}

                        {showIso && iso_curves && iso_curves.length > 0 &&
                            iso_curves.map((curve: any, idx: number) => (
                                <Line
                                    key={`iso-${idx}`}
                                    name={`${iso_type === "flow" ? "Flow" : "Velocity"} = ${curve.value.toFixed(2)} ${iso_type === "flow" ? "L/s" : "m/s"}`}
                                    data={curve.points.map((d: any) => ({ x: d[xVar], y: d.depth }))}
                                    type="monotone"
                                    dataKey="y"
                                    stroke="#82ca9d"
                                    strokeDasharray="5 5"
                                    strokeWidth={1}
                                    dot={false}
                                    activeDot={false}
                                    isAnimationActive={false}
                                />
                            ))}

                        {/* Pipe profile lines (from backend) */}
                        {pipe_profile && pipe_profile.map((lineData: any, idx: number) => (
                            <Line
                                key={`pipe-profile-${idx}`}
                                name={idx === 0 ? "Pipe Profile" : undefined}
                                data={lineData}
                                type="monotone"
                                dataKey="y"
                                stroke="#000000"
                                strokeWidth={1.5}
                                dot={false}
                                activeDot={false}
                                isAnimationActive={false}
                                legendType={idx === 0 ? "line" : "none"}
                            />
                        ))}
                    </RechartsScatter>
                </ResponsiveContainer>
            </div>

            {/* Pipe parameter summary */}
            <div className="bg-gray-50 p-4 rounded-lg text-sm text-gray-700 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                    <span className="font-semibold block">Pipe Diameter</span>
                    {pipe_params?.diameter ? `${pipe_params.diameter} mm` : "N/A"}
                </div>
                <div>
                    <span className="font-semibold block">Roughness (ks)</span>
                    {pipe_params?.roughness ? `${pipe_params.roughness} mm` : "N/A"}
                </div>
                <div>
                    <span className="font-semibold block">Gradient</span>
                    {pipe_params?.gradient ? `${(pipe_params.gradient * 100).toFixed(3)} %` : "N/A"}
                </div>
                <div>
                    <span className="font-semibold block">Shape</span>
                    {pipe_params?.shape ?? "N/A"}
                </div>
            </div>
        </div>
    );
};

export default ScatterChart;
