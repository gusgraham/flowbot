import React, { useState } from 'react';
import { useInstallTimeseries, useProcessInstall } from '../../api/hooks';
import { Loader2, Calendar, Play, X, ZoomOut } from 'lucide-react';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
    ReferenceArea,
} from 'recharts';

interface DataViewerTabProps {
    installId: number;
    installType: string;
}

const DataViewerTab: React.FC<DataViewerTabProps> = ({ installId, installType }) => {
    const [dataType, setDataType] = useState<'Raw' | 'Processed'>('Raw');
    const [startDate, setStartDate] = useState<string>('');
    const [endDate, setEndDate] = useState<string>('');

    const { data, isLoading, error } = useInstallTimeseries(
        installId,
        dataType,
        startDate || undefined,
        endDate || undefined
    );

    const { mutate: processInstall, isLoading: isProcessing } = useProcessInstall();

    const handleProcess = () => {
        processInstall(installId, {
            onSuccess: () => {
                setDataType('Processed');
            }
        });
    };

    // Prepare chart data by combining all variables with timestamps
    const prepareChartData = () => {
        if (!data) return [];
        const timeMap = new Map<string, any>();

        Object.entries(data.variables).forEach(([varName, varData]) => {
            varData.data.forEach((point) => {
                if (!timeMap.has(point.time)) {
                    timeMap.set(point.time, { time: new Date(point.time).getTime() });
                }
                timeMap.get(point.time)![varName] = point.value;
            });
        });

        return Array.from(timeMap.values()).sort((a, b) => a.time - b.time);
    };

    const chartData = prepareChartData();

    const [refAreaLeft, setRefAreaLeft] = useState<string | number | null>(null);
    const [refAreaRight, setRefAreaRight] = useState<string | number | null>(null);
    const [left, setLeft] = useState<string | number | null>('dataMin');
    const [right, setRight] = useState<string | number | null>('dataMax');

    // Reset zoom when data changes
    React.useEffect(() => {
        setLeft('dataMin');
        setRight('dataMax');
        setRefAreaLeft(null);
        setRefAreaRight(null);
    }, [data, dataType]);

    // Zoom handlers
    const zoom = () => {
        if (refAreaLeft === refAreaRight || refAreaRight === null) {
            setRefAreaLeft(null);
            setRefAreaRight(null);
            return;
        }

        // Determine min and max
        let min = refAreaLeft;
        let max = refAreaRight;

        if (typeof min === 'number' && typeof max === 'number') {
            if (min > max) [min, max] = [max, min];
        }

        setRefAreaLeft(null);
        setRefAreaRight(null);
        setLeft(min);
        setRight(max);
    };

    const zoomOut = () => {
        setLeft('dataMin');
        setRight('dataMax');
        setRefAreaLeft(null);
        setRefAreaRight(null);
    };

    // Determine appropriate date format based on data range
    const getXAxisFormatter = () => {
        if (chartData.length === 0) return (time: number) => new Date(time).toLocaleDateString();

        let minTime = chartData[0].time;
        let maxTime = chartData[chartData.length - 1].time;

        // If zoomed in, use the zoom range
        if (typeof left === 'number' && typeof right === 'number') {
            minTime = left;
            maxTime = right;
        }

        const duration = maxTime - minTime;
        const DAY = 86400000;

        if (duration > 365 * DAY) {
            // > 1 year: mm/yy
            return (time: number) => {
                const d = new Date(time);
                return `${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getFullYear().toString().slice(2)}`;
            };
        } else if (duration > 30 * DAY) {
            // > 1 month: dd/mm/yyyy
            return (time: number) => {
                const d = new Date(time);
                return `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}/${d.getFullYear()}`;
            };
        } else {
            // <= 1 month: dd/mm HH:MM
            return (time: number) => {
                const d = new Date(time);
                return `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')} ${d.getHours().toString().padStart(2, '0')}:${d.getMinutes().toString().padStart(2, '0')}`;
            };
        }
    };

    const dateFormatter = getXAxisFormatter();

    const renderFlowMonitorCharts = () => {
        if (!data) return null;
        const variables = Object.keys(data.variables);
        const hasDepth = variables.includes('Depth');
        const hasVelocity = variables.includes('Velocity');
        const hasVoltage = variables.includes('Voltage');
        const hasFlow = variables.includes('Flow');

        return (
            <div className="space-y-6">
                {hasDepth && (
                    <div>
                        <h3 className="text-lg font-semibold mb-2">Depth</h3>
                        <div className="flex gap-4">
                            <div className="flex-1 select-none">
                                <ResponsiveContainer width="100%" height={250}>
                                    <LineChart
                                        data={chartData}
                                        onMouseDown={(e: any) => e && setRefAreaLeft(e.activeLabel)}
                                        onMouseMove={(e: any) => refAreaLeft && e && setRefAreaRight(e.activeLabel)}
                                        onMouseUp={zoom}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="time"
                                            type="number"
                                            domain={[left, right]}
                                            allowDataOverflow
                                            tickFormatter={dateFormatter}
                                        />
                                        <YAxis label={{ value: data.variables.Depth.unit, angle: -90, position: 'insideLeft' }} />
                                        <Tooltip labelFormatter={(time) => new Date(time).toLocaleString()} />
                                        <Legend />
                                        <Line type="monotone" dataKey="Depth" stroke="#ef4444" dot={false} strokeWidth={1.5} />
                                        {refAreaLeft && refAreaRight ? (
                                            <ReferenceArea x1={refAreaLeft} x2={refAreaRight} strokeOpacity={0.3} />
                                        ) : null}
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="w-48 bg-gray-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-sm mb-2">Statistics</h4>
                                <div className="space-y-1 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Min:</span>
                                        <span className="font-medium">{data.variables.Depth.stats.min?.toFixed(2)} {data.variables.Depth.unit}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Max:</span>
                                        <span className="font-medium">{data.variables.Depth.stats.max?.toFixed(2)} {data.variables.Depth.unit}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Mean:</span>
                                        <span className="font-medium">{data.variables.Depth.stats.mean?.toFixed(2)} {data.variables.Depth.unit}</span>
                                    </div>
                                    {/* <div className="flex justify-between">
                                        <span className="text-gray-600">Points:</span>
                                        <span className="font-medium">{data.variables.Depth.stats.count}</span>
                                    </div> */}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {hasVelocity && (
                    <div>
                        <h3 className="text-lg font-semibold mb-2">Velocity</h3>
                        <div className="flex gap-4">
                            <div className="flex-1 select-none">
                                <ResponsiveContainer width="100%" height={250}>
                                    <LineChart
                                        data={chartData}
                                        onMouseDown={(e: any) => e && setRefAreaLeft(e.activeLabel)}
                                        onMouseMove={(e: any) => refAreaLeft && e && setRefAreaRight(e.activeLabel)}
                                        onMouseUp={zoom}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="time"
                                            type="number"
                                            domain={[left, right]}
                                            allowDataOverflow
                                            tickFormatter={dateFormatter}
                                        />
                                        <YAxis label={{ value: data.variables.Velocity.unit, angle: -90, position: 'insideLeft' }} />
                                        <Tooltip labelFormatter={(time) => new Date(time).toLocaleString()} />
                                        <Legend />
                                        <Line type="monotone" dataKey="Velocity" stroke="#10b981" dot={false} strokeWidth={1.5} />
                                        {refAreaLeft && refAreaRight ? (
                                            <ReferenceArea x1={refAreaLeft} x2={refAreaRight} strokeOpacity={0.3} />
                                        ) : null}
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="w-48 bg-gray-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-sm mb-2">Statistics</h4>
                                <div className="space-y-1 text-sm">
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Min:</span>
                                        <span className="font-medium">{data.variables.Velocity.stats.min?.toFixed(2)} {data.variables.Velocity.unit}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Max:</span>
                                        <span className="font-medium">{data.variables.Velocity.stats.max?.toFixed(2)} {data.variables.Velocity.unit}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-gray-600">Mean:</span>
                                        <span className="font-medium">{data.variables.Velocity.stats.mean?.toFixed(2)} {data.variables.Velocity.unit}</span>
                                    </div>
                                    {/* <div className="flex justify-between">
                                        <span className="text-gray-600">Points:</span>
                                        <span className="font-medium">{data.variables.Velocity.stats.count}</span>
                                    </div> */}
                                </div>
                            </div>
                        </div>
                    </div>
                )}

                {(hasVoltage || hasFlow) && (
                    <div>
                        <h3 className="text-lg font-semibold mb-2">{hasFlow ? 'Flow' : 'Voltage'}</h3>
                        <div className="flex gap-4">
                            <div className="flex-1 select-none">
                                <ResponsiveContainer width="100%" height={250}>
                                    <LineChart
                                        data={chartData}
                                        onMouseDown={(e: any) => e && setRefAreaLeft(e.activeLabel)}
                                        onMouseMove={(e: any) => refAreaLeft && e && setRefAreaRight(e.activeLabel)}
                                        onMouseUp={zoom}
                                    >
                                        <CartesianGrid strokeDasharray="3 3" />
                                        <XAxis
                                            dataKey="time"
                                            type="number"
                                            domain={[left, right]}
                                            allowDataOverflow
                                            tickFormatter={dateFormatter}
                                        />
                                        <YAxis label={{ value: hasFlow ? data.variables.Flow.unit : data.variables.Voltage.unit, angle: -90, position: 'insideLeft' }} />
                                        <Tooltip labelFormatter={(time) => new Date(time).toLocaleString()} />
                                        <Legend />
                                        <Line type="monotone" dataKey={hasFlow ? 'Flow' : 'Voltage'} stroke="#3b82f6" dot={false} strokeWidth={1.5} />
                                        {refAreaLeft && refAreaRight ? (
                                            <ReferenceArea x1={refAreaLeft} x2={refAreaRight} strokeOpacity={0.3} />
                                        ) : null}
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                            <div className="w-48 bg-gray-50 p-4 rounded-lg">
                                <h4 className="font-semibold text-sm mb-2">Statistics</h4>
                                {hasFlow && (
                                    <div className="space-y-1 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Min:</span>
                                            <span className="font-medium">{data.variables.Flow.stats.min?.toFixed(2)} {data.variables.Flow.unit}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Max:</span>
                                            <span className="font-medium">{data.variables.Flow.stats.max?.toFixed(2)} {data.variables.Flow.unit}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Mean:</span>
                                            <span className="font-medium">{data.variables.Flow.stats.mean?.toFixed(2)} {data.variables.Flow.unit}</span>
                                        </div>
                                        {/* <div className="flex justify-between">
                                            <span className="text-gray-600">Points:</span>
                                            <span className="font-medium">{data.variables.Flow.stats.count}</span>
                                        </div> */}
                                    </div>
                                )}
                                {hasVoltage && (
                                    <div className="space-y-1 text-sm">
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Min:</span>
                                            <span className="font-medium">{data.variables.Voltage.stats.min?.toFixed(2)} {data.variables.Voltage.unit}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Max:</span>
                                            <span className="font-medium">{data.variables.Voltage.stats.max?.toFixed(2)} {data.variables.Voltage.unit}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span className="text-gray-600">Mean:</span>
                                            <span className="font-medium">{data.variables.Voltage.stats.mean?.toFixed(2)} {data.variables.Voltage.unit}</span>
                                        </div>
                                        {/* <div className="flex justify-between">
                                            <span className="text-gray-600">Points:</span>
                                            <span className="font-medium">{data.variables.Voltage.stats.count}</span>
                                        </div> */}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        );
    };

    const renderRainGaugeChart = () => {
        if (!data) return null;
        const varName = 'Rain';
        const varData = data.variables[varName];

        return (
            <div>
                <h3 className="text-lg font-semibold mb-2">{dataType === 'Raw' ? 'Tips' : 'Intensity'}</h3>
                <div className="flex gap-4">
                    <div className="flex-1 select-none">
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart
                                data={chartData}
                                onMouseDown={(e: any) => e && setRefAreaLeft(e.activeLabel)}
                                onMouseMove={(e: any) => refAreaLeft && e && setRefAreaRight(e.activeLabel)}
                                onMouseUp={zoom}
                            >
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    dataKey="time"
                                    type="number"
                                    domain={[left, right]}
                                    allowDataOverflow
                                    tickFormatter={dateFormatter}
                                />
                                <YAxis label={{ value: varData.unit, angle: -90, position: 'insideLeft' }} />
                                <Tooltip labelFormatter={(time) => new Date(time).toLocaleString()} />
                                <Legend />
                                <Line type="monotone" dataKey="Rain" stroke="#0ea5e9" dot={false} strokeWidth={1.5} />
                                {refAreaLeft && refAreaRight ? (
                                    <ReferenceArea x1={refAreaLeft} x2={refAreaRight} strokeOpacity={0.3} />
                                ) : null}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="w-48 bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-semibold text-sm mb-2">Statistics</h4>
                        <div className="space-y-1 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Min:</span>
                                <span className="font-medium">{varData.stats.min?.toFixed(2)} {varData.unit}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Max:</span>
                                <span className="font-medium">{varData.stats.max?.toFixed(2)} {varData.unit}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Mean:</span>
                                <span className="font-medium">{varData.stats.mean?.toFixed(2)} {varData.unit}</span>
                            </div>
                            {/* <div className="flex justify-between">
                                <span className="text-gray-600">Points:</span>
                                <span className="font-medium">{varData.stats.count}</span>
                            </div> */}
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    const renderPumpLoggerChart = () => {
        if (!data) return null;
        const varName = 'Pump_State';
        const varData = data.variables[varName];

        if (!varData) return null;

        // Helper function to format duration in human-readable format
        const formatDuration = (seconds: number): string => {
            if (seconds < 60) return `${Math.round(seconds)}s`;
            if (seconds < 3600) return `${Math.floor(seconds / 60)}m ${Math.round(seconds % 60)}s`;
            const hours = Math.floor(seconds / 3600);
            const mins = Math.floor((seconds % 3600) / 60);
            return `${hours}h ${mins}m`;
        };

        // Calculate pump logger statistics
        const calculatePumpStats = () => {
            const points = varData.data;
            if (!points || points.length === 0) {
                return { nOn: 0, nOff: 0, runtimeSeconds: 0, measurementDurationSeconds: 0 };
            }

            // Sort by time
            const sortedPoints = [...points].sort((a, b) =>
                new Date(a.time).getTime() - new Date(b.time).getTime()
            );

            // Filter points based on zoom range if active
            const zoomedPoints = (typeof left === 'number' && typeof right === 'number')
                ? sortedPoints.filter(p => {
                    const t = new Date(p.time).getTime();
                    return t >= left && t <= right;
                })
                : sortedPoints;

            // If zoomedPoints is empty (e.g. zoomed area has no data points), metrics might be misleading.
            // But usually zoom area has points.
            if (zoomedPoints.length === 0) return { nOn: 0, nOff: 0, runtimeSeconds: 0, measurementDurationSeconds: 0 };

            const times = zoomedPoints.map(p => new Date(p.time).getTime());
            const values = zoomedPoints.map(p => p.value);

            // Calculate transitions
            let nOn = 0;
            let nOff = 0;
            for (let i = 1; i < values.length; i++) {
                const diff = values[i] - values[i - 1];
                if (diff === 1) nOn++;
                if (diff === -1) nOff++;
            }

            // Count starting state
            if (values.length > 0) {
                if (values[0] === 1) {
                    nOn++;
                }
            }

            // Calculate runtime
            let runtimeMs = 0;
            for (let i = 0; i < times.length - 1; i++) {
                const dt = times[i + 1] - times[i];
                if (values[i] === 1) {
                    runtimeMs += dt;
                }
            }

            // Measurement duration (from first to last data point within zoom)
            const measurementDurationMs = times.length > 1
                ? times[times.length - 1] - times[0]
                : 0;

            return {
                nOn,
                nOff,
                runtimeSeconds: runtimeMs / 1000,
                measurementDurationSeconds: measurementDurationMs / 1000
            };
        };

        const stats = calculatePumpStats();
        const activationsPerHour = stats.measurementDurationSeconds > 0
            ? (stats.nOn / (stats.measurementDurationSeconds / 3600)).toFixed(2)
            : '0.00';
        const avgRuntimePerActivation = stats.nOn > 0
            ? formatDuration(stats.runtimeSeconds / stats.nOn)
            : 'N/A';

        return (
            <div>
                <h3 className="text-lg font-semibold mb-2">Pump State</h3>
                <div className="flex gap-4">
                    <div className="flex-1 select-none">
                        <ResponsiveContainer width="100%" height={400}>
                            <LineChart
                                data={chartData}
                                onMouseDown={(e: any) => e && setRefAreaLeft(e.activeLabel)}
                                onMouseMove={(e: any) => refAreaLeft && e && setRefAreaRight(e.activeLabel)}
                                onMouseUp={zoom}
                            >
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    dataKey="time"
                                    type="number"
                                    domain={[left, right]}
                                    allowDataOverflow
                                    tickFormatter={dateFormatter}
                                />
                                <YAxis domain={[0, 1]} ticks={[0, 1]} tickFormatter={(val) => val === 1 ? 'On' : 'Off'} />
                                <Tooltip
                                    labelFormatter={(time) => new Date(time).toLocaleString()}
                                    formatter={(value: any) => [value === 1 ? 'On' : 'Off', 'State']}
                                />
                                <Legend />
                                <Line type="stepAfter" dataKey="Pump_State" stroke="#8b5cf6" dot={false} strokeWidth={2} />
                                {refAreaLeft && refAreaRight ? (
                                    <ReferenceArea x1={refAreaLeft} x2={refAreaRight} strokeOpacity={0.3} />
                                ) : null}
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                    <div className="w-56 bg-gray-50 p-4 rounded-lg">
                        <h4 className="font-semibold text-sm mb-3">Pump Statistics {typeof left === 'number' ? '(Zoomed)' : ''}</h4>
                        <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                                <span className="text-gray-600">Ons:</span>
                                <span className="font-medium text-green-600">{stats.nOn}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Offs:</span>
                                <span className="font-medium text-red-600">{stats.nOff}</span>
                            </div>
                            <div className="border-t border-gray-200 my-2"></div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Runtime:</span>
                                <span className="font-medium">{formatDuration(stats.runtimeSeconds)}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Measured:</span>
                                <span className="font-medium">{formatDuration(stats.measurementDurationSeconds)}</span>
                            </div>
                            <div className="border-t border-gray-200 my-2"></div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Act./hour:</span>
                                <span className="font-medium">{activationsPerHour}</span>
                            </div>
                            <div className="flex justify-between">
                                <span className="text-gray-600">Avg runtime:</span>
                                <span className="font-medium">{avgRuntimePerActivation}</span>
                            </div>
                            <div className="border-t border-gray-200 my-2"></div>
                            {/* <div className="flex justify-between">
                                <span className="text-gray-600">Points:</span>
                                <span className="font-medium">{varData.stats?.count || varData.data?.length || 0}</span>
                            </div> */}
                        </div>
                    </div>
                </div>
            </div>
        );
    };

    const renderContent = () => {
        if (isLoading) {
            return (
                <div className="flex justify-center items-center py-12">
                    <Loader2 className="animate-spin text-blue-500" size={32} />
                </div>
            );
        }

        if (error) {
            return (
                <div className="text-center py-12">
                    <p className="text-red-500">Error loading data: {(error as Error).message}</p>
                </div>
            );
        }

        if (!data || Object.keys(data.variables).length === 0) {
            return (
                <div className="text-center py-12">
                    <p className="text-gray-500">No data available for this install</p>
                </div>
            );
        }

        return (
            <div className="border-t pt-6">
                {installType === 'Flow Monitor' && renderFlowMonitorCharts()}
                {installType === 'Rain Gauge' && renderRainGaugeChart()}
                {installType === 'Pump Logger' && renderPumpLoggerChart()}
            </div>
        );
    };

    return (
        <div className="space-y-6">
            {/* Controls */}
            <div className="flex gap-4 items-end">
                <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Calendar size={16} className="inline mr-1" />
                        Start Date
                    </label>
                    <div className="relative">
                        <input
                            type="datetime-local"
                            value={startDate}
                            onChange={(e) => setStartDate(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-8"
                        />
                        {startDate && (
                            <button
                                onClick={() => setStartDate('')}
                                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            >
                                <X size={16} />
                            </button>
                        )}
                    </div>
                </div>
                <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                        <Calendar size={16} className="inline mr-1" />
                        End Date
                    </label>
                    <div className="relative">
                        <input
                            type="datetime-local"
                            value={endDate}
                            onChange={(e) => setEndDate(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 pr-8"
                        />
                        {endDate && (
                            <button
                                onClick={() => setEndDate('')}
                                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                            >
                                <X size={16} />
                            </button>
                        )}
                    </div>
                </div>
                <div className="flex-1">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Data Type</label>
                    <div className="flex gap-2">
                        <button
                            onClick={() => setDataType('Raw')}
                            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${dataType === 'Raw'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            Raw
                        </button>
                        <button
                            onClick={() => setDataType('Processed')}
                            className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${dataType === 'Processed'
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                }`}
                        >
                            Processed
                        </button>
                    </div>
                </div>
                <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">&nbsp;</label>
                    <div className="flex gap-2">
                        {left !== 'dataMin' && (
                            <button
                                onClick={zoomOut}
                                className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
                            >
                                <ZoomOut size={16} />
                                Zoom Out
                            </button>
                        )}
                        <button
                            onClick={handleProcess}
                            disabled={isProcessing}
                            className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                        >
                            {isProcessing ? <Loader2 className="animate-spin" size={16} /> : <Play size={16} />}
                            {isProcessing ? 'Processing...' : 'Run Processing'}
                        </button>
                    </div>
                </div>
            </div>

            {/* Charts or Status Message */}
            {renderContent()}
        </div>
    );
};

export default DataViewerTab;
